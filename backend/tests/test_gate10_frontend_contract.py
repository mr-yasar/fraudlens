"""Verification Gate 10 - Frontend Contract & Regression Check (Phases 28-30).

Tests:
1. Contract compatibility: /ai-assistant/chat accepts session_id, ui_context, context, and messages.
2. Response schema matches frontend expectation (response, provider, model, used_real_api, structured_metadata).
3. Session memory purge endpoint /session/clear returns success.
4. Graceful handling of empty or fallback cases without crashing frontend.
"""

import pytest
from fastapi.testclient import TestClient
from backend.app.main import create_application
from backend.app.core.database import SessionLocal
from backend.app.models.user import User
from backend.app.core.security import create_access_token

app = create_application()
client = TestClient(app)


@pytest.fixture(scope="module")
def db_session():
    db = SessionLocal()
    yield db
    db.close()


@pytest.fixture(scope="module")
def customer_token(db_session):
    user = db_session.query(User).filter(User.email == "monisha@fraudlens.ai").first()
    return create_access_token(
        subject=user.id,
        role="customer",
        extra_claims={"email": user.email, "name": user.name},
    )


def test_ai_assistant_chat_contract(customer_token):
    """
    Verification Gate 10 - Test 1:
    POST /api/v1/ai-assistant/chat handles frontend payload with session_id and ui_context.
    """
    payload = {
        "messages": [
            {"role": "user", "content": "Hello! What can you help me with?"}
        ],
        "provider": "auto",
        "temperature": 0.7,
        "session_id": "sess_test_fe_1001",
        "ui_context": {"current_view": "Dashboard", "transaction_id": None},
        "context": "View: Dashboard",
    }

    response = client.post(
        "/api/v1/ai-assistant/chat",
        headers={"Authorization": f"Bearer {customer_token}"},
        json=payload,
    )

    assert response.status_code == 200
    data = response.json()
    assert "response" in data
    assert "provider" in data
    assert "model" in data
    assert "used_real_api" in data
    assert data["session_id"] == "sess_test_fe_1001"
    assert "structured_metadata" in data


def test_session_clear_endpoint(customer_token):
    """
    Verification Gate 10 - Test 2:
    POST /api/v1/ai-assistant/session/clear purges user memory.
    """
    response = client.post(
        "/api/v1/ai-assistant/session/clear?session_id=sess_test_fe_1001",
        headers={"Authorization": f"Bearer {customer_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data.get("success") is True


def test_dual_route_ai_chat_mounted(customer_token):
    """
    Verification Gate 10 - Test 3:
    Both /api/v1/ai/chat and /api/v1/ai-assistant/chat are mounted and functional.
    """
    payload = {
        "messages": [{"role": "user", "content": "Help me check my account."}],
    }

    res_ai = client.post(
        "/api/v1/ai/chat",
        headers={"Authorization": f"Bearer {customer_token}"},
        json=payload,
    )
    assert res_ai.status_code == 200

    res_assistant = client.post(
        "/api/v1/ai-assistant/chat",
        headers={"Authorization": f"Bearer {customer_token}"},
        json=payload,
    )
    assert res_assistant.status_code == 200
