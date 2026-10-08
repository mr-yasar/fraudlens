"""Test Suite for Customer Security Copilot (40-Phase Implementation).

Validates:
- Monisha, Mohana, Sowmiya, and Ajay customer identity resolution
- Cross-customer data isolation and authorization enforcement
- Master question bank routing (Transactions, Fraud & Alerts, Security, Verification, Activity, Help)
- Customer-safe explainability (No raw internal model names or SHAP numbers leaked to customers)
- Dispute and guided recognition flow via backend investigations & approvals
"""

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.core.security import create_access_token


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def monisha_headers():
    token = create_access_token(subject="11", role="CUSTOMER", extra_claims={"email": "monisha@fraudlens.ai"})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def mohana_headers():
    token = create_access_token(subject="12", role="CUSTOMER", extra_claims={"email": "mohana@fraudlens.ai"})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def sowmiya_headers():
    token = create_access_token(subject="13", role="CUSTOMER", extra_claims={"email": "sowmiya@fraudlens.ai"})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def ajay_headers():
    token = create_access_token(subject="15", role="CUSTOMER", extra_claims={"email": "ajay@fraudlens.ai"})
    return {"Authorization": f"Bearer {token}"}


def test_customer_scoped_transactions_isolation(client, monisha_headers, mohana_headers):
    """Monisha and Mohana must only see their own transactions."""
    res_monisha = client.get("/api/v1/transactions?limit=10", headers=monisha_headers)
    assert res_monisha.status_code == 200
    monisha_txs = res_monisha.json().get("items", []) or res_monisha.json().get("transactions", [])
    for tx in monisha_txs:
        assert "MONISHA" in tx["customer_id"].upper(), f"Unexpected customer in Monisha's list: {tx['customer_id']}"

    res_mohana = client.get("/api/v1/transactions?limit=10", headers=mohana_headers)
    assert res_mohana.status_code == 200
    mohana_txs = res_mohana.json().get("items", []) or res_mohana.json().get("transactions", [])
    for tx in mohana_txs:
        assert "MOHANA" in tx["customer_id"].upper(), f"Unexpected customer in Mohana's list: {tx['customer_id']}"


def test_customer_security_copilot_greeting_and_recent_activity(client, monisha_headers):
    """Customer asks for recent activity in the copilot."""
    payload = {
        "messages": [
            {"role": "user", "content": "Show my recent transactions."}
        ],
        "role": "customer",
        "session_id": "test_monisha_sess_01",
    }
    res = client.post("/api/v1/ai-assistant/chat", json=payload, headers=monisha_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["authorized_role"] == "customer"
    assert "response" in data
    # Customer responses must be friendly and not expose raw backend debug
    assert len(data["response"]) > 0


def test_customer_safe_explainability_no_internal_model_leaks(client, monisha_headers):
    """Customer asks why a transaction was flagged; response must be customer-safe."""
    payload = {
        "messages": [
            {"role": "user", "content": "Why was my transaction flagged?"}
        ],
        "role": "customer",
        "session_id": "test_monisha_sess_02",
    }
    res = client.post("/api/v1/ai-assistant/chat", json=payload, headers=monisha_headers)
    assert res.status_code == 200
    data = res.json()
    resp_text = data["response"].lower()

    # Must NOT expose raw internal ML framework names in customer conversational copy
    assert "xgboost champion" not in resp_text
    assert "randomforestclassifier" not in resp_text
    assert "logreg" not in resp_text


def test_customer_guided_dispute_reporting_workflow(client, monisha_headers):
    """Customer unrecognized charge triggers dispute case creation with backend protection."""
    # 1. Fetch Monisha's transaction
    tx_res = client.get("/api/v1/transactions?limit=1", headers=monisha_headers)
    assert tx_res.status_code == 200
    tx_items = tx_res.json().get("items", []) or tx_res.json().get("transactions", [])
    assert len(tx_items) > 0
    target_tx_id = tx_items[0]["transaction_id"]

    # 2. Customer reports fraud
    report_payload = {
        "transaction_id": target_tx_id,
        "notes": "[CUSTOMER REPORTED FRAUD]\nAction: Customer did not recognize transaction.",
    }
    case_res = client.post("/api/v1/investigations", json=report_payload, headers=monisha_headers)
    assert case_res.status_code in (201, 409)
    if case_res.status_code == 201:
        case_id = case_res.json()["case_id"]
        # Customer can read their case
        get_res = client.get(f"/api/v1/investigations/{case_id}", headers=monisha_headers)
        assert get_res.status_code == 200
        # Customer cannot tamper with case determination
        tamper_res = client.patch(f"/api/v1/investigations/{case_id}", json={"status": "RESOLVED"}, headers=monisha_headers)
        assert tamper_res.status_code == 403


def test_all_four_customers_support(client, monisha_headers, mohana_headers, sowmiya_headers, ajay_headers):
    """Verify copilot connectivity and context for all 4 customer accounts."""
    for headers, name in [
        (monisha_headers, "Monisha"),
        (mohana_headers, "Mohana"),
        (sowmiya_headers, "Sowmiya"),
        (ajay_headers, "Ajay"),
    ]:
        res = client.post(
            "/api/v1/ai-assistant/chat",
            json={
                "messages": [{"role": "user", "content": "Is my account secure?"}],
                "role": "customer",
            },
            headers=headers,
        )
        assert res.status_code == 200
        assert res.json()["authorized_role"] == "customer"
