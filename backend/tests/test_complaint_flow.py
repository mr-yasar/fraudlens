import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.core.security import create_access_token

def test_full_complaint_and_admin_investigation_lifecycle():
    client = TestClient(app)

    # 1. Customer token for Monisha (user_id 11, role CUSTOMER)
    cust_token = create_access_token(subject="11", role="CUSTOMER", extra_claims={"email": "monisha@fraudlens.ai"})
    cust_headers = {"Authorization": f"Bearer {cust_token}"}

    # Get a transaction belonging to Monisha
    tx_res = client.get("/api/v1/transactions?limit=1", headers=cust_headers)
    assert tx_res.status_code == 200
    tx_data = tx_res.json()
    tx_items = tx_data.get("transactions", []) or tx_data.get("items", [])
    assert len(tx_items) > 0, "Customer has transactions"
    target_tx_id = tx_items[0]["transaction_id"]

    # 2. Customer creates complaint
    complaint_payload = {
        "transaction_id": target_tx_id,
        "notes": "[CUSTOMER REPORTED FRAUD]\nReason: Unauthorized Transaction\nDetails: Test customer dispute"
    }
    create_res = client.post("/api/v1/investigations", json=complaint_payload, headers=cust_headers)
    assert create_res.status_code in (201, 409), f"Create complaint status: {create_res.status_code}"
    if create_res.status_code == 201:
        case_id = create_res.json()["case_id"]
    else:
        admin_token_tmp = create_access_token(subject="1", role="ADMIN", extra_claims={"email": "admin@fraudlens.ai"})
        list_res = client.get("/api/v1/investigations", headers={"Authorization": f"Bearer {admin_token_tmp}"})
        cases_list = list_res.json().get("cases", []) or list_res.json().get("items", [])
        matched = [c for c in cases_list if c.get("transaction_id") == target_tx_id]
        case_id = matched[0]["case_id"] if matched else f"CASE-{target_tx_id[:8]}"

    assert case_id.startswith("CASE-")

    # 3. Customer attempts to modify/resolve case -> MUST BE 403 FORBIDDEN
    hack_res = client.patch(f"/api/v1/investigations/{case_id}", json={"status": "RESOLVED", "decision": "CONFIRMED_FRAUD", "notes": "hack"}, headers=cust_headers)
    assert hack_res.status_code == 403, f"Expected 403 for customer patch, got {hack_res.status_code}"

    # 4. Admin token for Admin
    admin_token = create_access_token(subject="1", role="ADMIN", extra_claims={"email": "admin@fraudlens.ai"})
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # Admin adjudicates the case
    admin_res = client.patch(f"/api/v1/investigations/{case_id}", json={"status": "RESOLVED", "decision": "CONFIRMED_FRAUD", "notes": "Investigator confirmed unauthorized charge."}, headers=admin_headers)
    assert admin_res.status_code == 200, f"Admin patch failed: {admin_res.status_code} {admin_res.text}"

    # 5. Customer views updated complaint status (Read-only)
    cust_view_res = client.get(f"/api/v1/investigations/{case_id}", headers=cust_headers)
    assert cust_view_res.status_code == 200
    view_data = cust_view_res.json()
    assert view_data["status"] == "RESOLVED"
    assert view_data["decision"] == "CONFIRMED_FRAUD"
