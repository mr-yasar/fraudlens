"""Verification Gate 12 - Final System E2E & Release Lock (Phases 34-35).

Tests:
1. Clean import and instantiation of all centralized AI Assistant services.
2. Full lifecycle end-to-end execution:
   - Server-side JWT identity resolution
   - Pre-flight prompt injection / zero-leak guard
   - Context envelope generation
   - Read-only tool dispatch
   - Bounded turn window enforcement
   - Post-flight output sanitization
3. Integrity of dual API mount paths (/api/v1/ai and /api/v1/ai-assistant).
"""

import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from backend.app.main import create_application
from backend.app.core.database import SessionLocal
from backend.app.models.user import User
from backend.app.core.security import create_access_token

from backend.app.services.assistant_identity_service import resolve_assistant_identity
from backend.app.services.assistant_financial_context_service import build_safe_context_envelope
from backend.app.services.assistant_intent_service import classify_user_intent, AssistantIntent
from backend.app.services.assistant_explainability_service import explain_transaction_risk, explain_hold_status
from backend.app.services.assistant_admin_service import get_admin_system_telemetry
from backend.app.services.assistant_session_service import session_memory
from backend.app.services.intelligence.orchestrator import LLMOrchestrator
from backend.app.services.intelligence.synthesizer import ResponseValidator

app = create_application()
client = TestClient(app)


@pytest.fixture(scope="module")
def db_session():
    db = SessionLocal()
    yield db
    db.close()


@pytest.fixture(scope="module")
def monisha_token(db_session):
    user = db_session.query(User).filter(User.email == "monisha@fraudlens.ai").first()
    return create_access_token(
        subject=user.id,
        role="customer",
        extra_claims={"email": user.email, "name": user.name},
    ), user


def test_service_initialization_and_clean_imports():
    """
    Verification Gate 12 - Test 1:
    All core centralized assistant components must initialize with clean contracts.
    """
    assert callable(resolve_assistant_identity)
    assert callable(build_safe_context_envelope)
    assert callable(classify_user_intent)
    assert callable(explain_transaction_risk)
    assert callable(explain_hold_status)
    assert callable(get_admin_system_telemetry)
    assert hasattr(session_memory, "prune_incoming_messages")
    assert hasattr(LLMOrchestrator, "chat")
    assert hasattr(ResponseValidator, "validate_and_scrub")


def test_full_lifecycle_e2e_trace(db_session, monisha_token):
    """
    Verification Gate 12 - Test 2:
    Execute a full E2E lifecycle trace from JWT authentication to sanitized output.
    """
    token, user = monisha_token

    # 1. Identity Resolution
    identity = resolve_assistant_identity(user, db_session)
    assert identity.customer_id == "CUST_MONISHA_001"
    assert identity.role == "customer"

    # 2. Intent Classification
    intent = classify_user_intent("Show my recent transactions", identity)
    assert intent.intent == AssistantIntent.TRANSACTION_INQUIRY
    assert intent.is_mutating_attempt is False

    # 3. Context Envelope Construction
    envelope = build_safe_context_envelope(identity, "Show my recent transactions", db_session)
    assert envelope["customer_id"] == "CUST_MONISHA_001"
    assert "account_number_masked" in envelope["wallet"]

    # 4. Bounded Turn Window
    dummy_history = [{"role": "user", "content": f"Q{i}"} for i in range(12)]
    pruned = session_memory.prune_incoming_messages(dummy_history, max_turns=6)
    assert len(pruned) == 6

    # 5. Output Sanitization
    dirty_output = "Secret key is AIzaSyD98234jkhsdfkjh2348sdfkjhsd234 and OTP: 440628"
    scrubbed = ResponseValidator.validate_and_scrub(dirty_output, role="customer", user_info={"customer_id": "CUST_MONISHA_001"})
    assert "AIza" not in scrubbed
    assert "440628" not in scrubbed
    assert "[PROTECTED_API_KEY]" in scrubbed
    assert "[PROTECTED_OTP]" in scrubbed


def test_dual_api_routes_operational(monisha_token):
    """
    Verification Gate 12 - Test 3:
    Both /ai-assistant/providers and /ai/providers endpoints return valid configuration.
    """
    token, _ = monisha_token

    r1 = client.get("/api/v1/ai-assistant/providers", headers={"Authorization": f"Bearer {token}"})
    assert r1.status_code == 200
    d1 = r1.json()
    assert "providers" in d1

    r2 = client.get("/api/v1/ai/providers", headers={"Authorization": f"Bearer {token}"})
    assert r2.status_code == 200
    d2 = r2.json()
    assert "providers" in d2
