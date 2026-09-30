"""Test End-to-End Decision Persistence (Confirm Fraud & Not Fraud) in SQLite."""
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.core.database import get_db, SessionLocal
from backend.app.models.investigation import Investigation
from backend.app.models.transaction import Transaction
from backend.app.models.user import User

from backend.app.core.security import create_access_token

client = TestClient(app)

def test_confirm_fraud_and_not_fraud_persistence():
    # 1. Obtain admin token
    admin_token = create_access_token(subject="1", role="ADMIN", extra_claims={"email": "admin@fraudlens.ai"})
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # 2. Get or create an open investigation case
    cases_res = client.get("/api/v1/investigations?limit=10", headers=admin_headers)
    assert cases_res.status_code == 200
    cases_data = cases_res.json()
    assert len(cases_data["items"]) > 0

    target_case_id = cases_data["items"][0]["case_id"]

    # 3. Apply CONFIRM FRAUD determination
    update_res = client.patch(
        f"/api/v1/investigations/{target_case_id}",
        headers=admin_headers,
        json={
            "status": "RESOLVED",
            "decision": "CONFIRMED_FRAUD",
            "notes": "Automated test: Confirmed fraud determination with card freeze.",
        },
    )
    assert update_res.status_code == 200, f"Update failed: {update_res.text}"
    updated_data = update_res.json()
    assert updated_data["status"] == "RESOLVED"
    assert updated_data["decision"] == "CONFIRMED_FRAUD"

    # 4. Verify DB persistence via fresh GET request (simulating page reload)
    reload_res = client.get(f"/api/v1/investigations/{target_case_id}", headers=admin_headers)
    assert reload_res.status_code == 200
    reloaded_case = reload_res.json()
    assert reloaded_case["status"] == "RESOLVED", "Case status reverted after reload!"
    assert reloaded_case["decision"] == "CONFIRMED_FRAUD", "Decision was not persisted!"

    # 5. Apply NOT FRAUD (GENUINE) determination
    genuine_res = client.patch(
        f"/api/v1/investigations/{target_case_id}",
        headers=admin_headers,
        json={
            "status": "RESOLVED",
            "decision": "GENUINE",
            "notes": "Automated test: Investigator determined transaction is verified genuine.",
        },
    )
    assert genuine_res.status_code == 200, f"Not Fraud update failed: {genuine_res.text}"
    genuine_data = genuine_res.json()
    assert genuine_data["status"] == "RESOLVED"
    assert genuine_data["decision"] == "GENUINE"

    # 6. Verify second DB persistence via fresh GET request
    reload_genuine = client.get(f"/api/v1/investigations/{target_case_id}", headers=admin_headers)
    assert reload_genuine.status_code == 200
    reloaded_genuine = reload_genuine.json()
    assert reloaded_genuine["status"] == "RESOLVED"
    assert reloaded_genuine["decision"] == "GENUINE"
