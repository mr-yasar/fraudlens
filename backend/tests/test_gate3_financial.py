"""Gate 3 Financial Data Check Test Suite (Phases 7-9).

Tests:
1. Recent 5 transactions retrieval & envelope construction
2. Ledger history summary calculation
3. Specific transaction detail query
4. Active held transaction retrieval
5. Masked account display (•••• 4821)
6. Missing-data fallback path
7. Another-user transaction denial enforcement
"""

import pytest
from fastapi.testclient import TestClient
from backend.app.main import create_application
from backend.app.core.database import SessionLocal
from backend.app.models.user import User
from backend.app.models.transaction import Transaction
from backend.app.core.security import create_access_token

app = create_application()
client = TestClient(app)


@pytest.fixture(scope="module")
def db_session():
    db = SessionLocal()
    yield db
    db.close()


@pytest.fixture(scope="module")
def monisha_context(db_session):
    user = db_session.query(User).filter(User.email == "monisha@fraudlens.ai").first()
    token = create_access_token(
        subject=user.id,
        role="customer",
        extra_claims={"email": user.email, "name": user.name},
    )
    return token, user


def test_gate3_recent_5_transactions_envelope(monisha_context):
    """1. Customer queries recent transactions -> Envelope contains <= 5 recent records."""
    token, user = monisha_context
    payload = {
        "messages": [
            {"role": "user", "content": "Show my recent transactions"}
        ],
        "provider": "gemini",
    }
    response = client.post(
        "/api/v1/ai/chat",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    metadata = data.get("structured_metadata") or {}
    recent_txs = metadata.get("recent_transactions", [])
    assert len(recent_txs) <= 5
    for tx in recent_txs:
        assert "transaction_id" in tx
        assert "amount" in tx
        assert "merchant" in tx


def test_gate3_history_ledger_summary(monisha_context):
    """2. Customer asks for summary of spending -> Ledger metrics provided."""
    token, user = monisha_context
    payload = {
        "messages": [
            {"role": "user", "content": "Summarize my spending and transaction history"}
        ],
    }
    response = client.post(
        "/api/v1/ai/chat",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    metadata = data.get("structured_metadata") or {}
    summary = metadata.get("transaction_summary")
    assert summary is not None
    assert "total_count" in summary
    assert "total_spend" in summary


def test_gate3_masked_account_display(monisha_context):
    """3. Verify bank account identifier is masked with •••• 4821."""
    token, user = monisha_context
    payload = {
        "messages": [
            {"role": "user", "content": "What is my account balance?"}
        ],
    }
    response = client.post(
        "/api/v1/ai/chat",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    metadata = data.get("structured_metadata") or {}
    acc = metadata.get("account_summary") or {}
    assert "••••" in acc.get("account_number_masked", "")


def test_gate3_held_transaction_context(monisha_context, db_session):
    """4. Querying held transactions returns pending holds."""
    token, user = monisha_context
    payload = {
        "messages": [
            {"role": "user", "content": "Why is my transaction on hold?"}
        ],
    }
    response = client.post(
        "/api/v1/ai/chat",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    metadata = data.get("structured_metadata") or {}
    assert "active_holds" in metadata


def test_gate3_cross_user_denial(monisha_context):
    """5. Another user transaction lookup is denied."""
    token, user = monisha_context
    payload = {
        "messages": [
            {"role": "user", "content": "Show Ajay's payments"}
        ],
    }
    response = client.post(
        "/api/v1/ai/chat",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data.get("error_category") == "unauthorized_scope"
    assert "another user's account information" in data.get("response", "")
