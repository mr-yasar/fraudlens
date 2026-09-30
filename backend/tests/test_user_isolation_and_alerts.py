import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.core.security import create_access_token

def test_user_data_isolation_monisha_ajay_mogana_sowmiya():
    client = TestClient(app)

    users = [
        {"name": "Monisha", "email": "monisha@fraudlens.ai", "expected_cust": "CUST_MONISHA_001", "sub": "11"},
        {"name": "Mogana", "email": "mohana@fraudlens.ai", "expected_cust": "CUST_MOHANA_002", "sub": "12"},
        {"name": "Sowmiya", "email": "sowmiya@fraudlens.ai", "expected_cust": "CUST_SOWMIYA_003", "sub": "13"},
        {"name": "Ajay", "email": "ajay@fraudlens.ai", "expected_cust": "CUST_AJAY_004", "sub": "15"},
    ]

    for u in users:
        token = create_access_token(subject=u["sub"], role="CUSTOMER", extra_claims={"email": u["email"], "name": u["name"]})
        headers = {"Authorization": f"Bearer {token}"}

        # 1. Transactions List isolation check
        tx_res = client.get("/api/v1/transactions?limit=20", headers=headers)
        assert tx_res.status_code == 200
        items = tx_res.json().get("items", []) or tx_res.json().get("transactions", [])
        assert len(items) > 0, f"{u['name']} should have transactions"

        # Verify EVERY returned transaction belongs ONLY to this user's customer_id
        for tx in items:
            assert tx["customer_id"] == u["expected_cust"], f"Data leak detected! User {u['name']} received transaction for customer_id {tx['customer_id']}"

        # 2. Dashboard Stats isolation check
        stats_res = client.get("/api/v1/dashboard/stats", headers=headers)
        assert stats_res.status_code == 200
        stats = stats_res.json()
        assert stats["total_customers"] == 1

        # 3. Raise Complaint and Admin Alert check
        target_tx = items[0]["transaction_id"]
        complaint_res = client.post(
            "/api/v1/investigations",
            json={
                "transaction_id": target_tx,
                "notes": f"[CUSTOMER REPORTED FRAUD]\nReason: Unauthorized Transaction\nDetails: Dispute by {u['name']}"
            },
            headers=headers
        )
        assert complaint_res.status_code in (201, 409)

        # 4. Verify User CANNOT modify or resolve case (403 Forbidden)
        if complaint_res.status_code == 201:
            case_id = complaint_res.json()["case_id"]
        else:
            list_res = client.get("/api/v1/investigations", headers=headers)
            case_id = [c for c in list_res.json()["items"] if c["transaction_id"] == target_tx][0]["case_id"]

        hack_res = client.patch(f"/api/v1/investigations/{case_id}", json={"status": "RESOLVED", "decision": "CONFIRMED_FRAUD", "notes": "hack"}, headers=headers)
        assert hack_res.status_code == 403, f"User {u['name']} should not be allowed to modify investigation cases"

    # 5. Admin can see alerts with user names
    admin_token = create_access_token(subject="1", role="ADMIN", extra_claims={"email": "admin@fraudlens.ai"})
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    alerts_res = client.get("/api/v1/alerts?limit=20", headers=admin_headers)
    assert alerts_res.status_code == 200
    alerts = alerts_res.json()
    assert len(alerts) > 0
