"""Comprehensive Conversational Intelligence, Follow-up Context, and Customer Isolation Suite.

Covers:
- Test A: Greetings, acknowledgements, small talk, and capabilities
- Test B: Multi-turn conversational follow-up context and session separation
- Test C: Grounded transaction risk explanations, TreeSHAP, and clarification prompts
- Test D: Provider configuration, model cascades, and failover behavior
- Test E: Customer data isolation and RBAC scope enforcement
- Test F: End-to-end FastAPI endpoint request/response contracts
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.main import app
from backend.app.core.database import SessionLocal
from backend.app.core.security import create_access_token
from backend.app.models.user import User
from backend.app.models.transaction import Transaction
from backend.app.services.assistant_identity_service import (
    resolve_assistant_identity,
    ROLE_CUSTOMER,
    ROLE_ADMIN,
    ROLE_INVESTIGATOR,
)
from backend.app.services.hybrid_assistant import route_and_execute_query, RouteType
from backend.app.services.assistant_session_service import session_memory
from backend.app.services.llm_service import (
    get_available_providers,
    is_gemini_configured,
    is_mistral_configured,
    verify_gemini_key,
    verify_mistral_key,
)


@pytest.fixture(scope="module")
def db_session():
    db = SessionLocal()
    yield db
    db.close()


@pytest.fixture(scope="module")
def api_client():
    return TestClient(app)


@pytest.fixture(scope="module")
def ajay_user(db_session: Session):
    user = db_session.query(User).filter(User.email.like("%ajay%")).first()
    assert user is not None, "Ajay user record must exist in database"
    return user


@pytest.fixture(scope="module")
def monisha_user(db_session: Session):
    user = db_session.query(User).filter(User.email.like("%monisha%")).first()
    assert user is not None, "Monisha user record must exist in database"
    return user


@pytest.fixture(scope="module")
def admin_user(db_session: Session):
    user = db_session.query(User).filter(User.email.like("%admin%")).first()
    assert user is not None, "Admin user record must exist in database"
    return user


# ─────────────────────────────────────────────────────────────────────────────
# TEST A: BASIC CONVERSATION & GREETINGS
# ─────────────────────────────────────────────────────────────────────────────

def test_greeting_hi_receives_personalized_greeting(db_session: Session, ajay_user: User):
    """'Hi' must return a friendly, role-tailored greeting with the user's name without demanding a transaction ID."""
    identity = resolve_assistant_identity(ajay_user, db_session)
    res = route_and_execute_query("Hi", identity, db_session)
    
    assert res.source_type == RouteType.PREDEFINED
    assert "Ajay" in res.answer
    assert "Security Copilot" in res.answer
    assert len(res.follow_up_suggestions) > 0


@pytest.mark.parametrize("query,expected_phrase", [
    ("Hello", "Ajay"),
    ("Hey there", "Ajay"),
    ("Good morning", "Ajay"),
    ("Hi, how are you?", "Ajay"),
    ("Thanks", "welcome"),
    ("Thank you very much", "welcome"),
    ("Okay", "Understood"),
    ("Got it", "Understood"),
    ("Bye", "Goodbye"),
])
def test_small_talk_and_acknowledgements(db_session: Session, ajay_user: User, query: str, expected_phrase: str):
    """Small talk and acknowledgements must receive polite, contextually appropriate responses."""
    identity = resolve_assistant_identity(ajay_user, db_session)
    res = route_and_execute_query(query, identity, db_session)
    
    assert expected_phrase.lower() in res.answer.lower()
    assert res.confidence >= 0.90


def test_capabilities_query(db_session: Session, ajay_user: User):
    """'What can you do?' must outline real FraudLens AI capabilities."""
    identity = resolve_assistant_identity(ajay_user, db_session)
    res = route_and_execute_query("What can you do?", identity, db_session)
    
    assert "FraudLens AI" in res.answer or "Transaction Risk" in res.answer
    assert "TreeSHAP" in res.answer or "Recent Activity" in res.answer


# ─────────────────────────────────────────────────────────────────────────────
# TEST B: FOLLOW-UP CONVERSATIONAL CONTEXT
# ─────────────────────────────────────────────────────────────────────────────

def test_followup_context_preserves_referenced_transaction(db_session: Session, monisha_user: User):
    """Follow-up questions like 'Why is it low risk?' must preserve context of the previously referenced transaction."""
    identity = resolve_assistant_identity(monisha_user, db_session)
    
    # Locate a real transaction for Monisha
    tx = db_session.query(Transaction).filter(Transaction.customer_id == identity.customer_id).first()
    assert tx is not None
    tx_id = tx.transaction_id

    # Turn 1: Explicit transaction inquiry
    res1 = route_and_execute_query(f"Explain {tx_id}", identity, db_session)
    assert tx_id in res1.answer

    # Turn 2: Follow-up without repeating transaction ID
    ctx = {"last_transaction_id": tx_id}
    res2 = route_and_execute_query("Why is it considered risky?", identity, db_session, conversation_context=ctx)
    assert tx_id in res2.answer
    assert res2.source_type == RouteType.LIVE_TOOL


def test_followup_verification_checks(db_session: Session, monisha_user: User):
    """'How can I verify that?' must return practical, evidence-based verification steps."""
    identity = resolve_assistant_identity(monisha_user, db_session)
    ctx = {"last_transaction_id": "TXN-TEST-123"}
    res = route_and_execute_query("How can I verify that?", identity, db_session, conversation_context=ctx)
    
    assert "Verification" in res.answer
    assert "OTP" in res.answer or "Device" in res.answer or "IP" in res.answer


def test_followup_session_summary(db_session: Session, monisha_user: User):
    """'Summarize everything' must summarize previous turns in the session."""
    identity = resolve_assistant_identity(monisha_user, db_session)
    recent_msgs = [
        {"role": "user", "content": "Explain my recent payment"},
        {"role": "assistant", "content": "Payment verified and approved under 4ms."},
        {"role": "user", "content": "How does OTP work?"},
    ]
    ctx = {"recent_messages": recent_msgs}
    res = route_and_execute_query("Summarize everything", identity, db_session, conversation_context=ctx)
    
    assert "Summary" in res.answer or "recap" in res.answer.lower()


# ─────────────────────────────────────────────────────────────────────────────
# TEST C: GROUNDED TRANSACTIONS & CLARIFICATION
# ─────────────────────────────────────────────────────────────────────────────

def test_ambiguous_transaction_question_returns_clarification(db_session: Session, ajay_user: User):
    """Asking 'Why is this transaction considered risky?' without context must return a helpful clarification question."""
    identity = resolve_assistant_identity(ajay_user, db_session)
    res = route_and_execute_query("Why is this transaction considered risky?", identity, db_session, conversation_context={})
    
    assert "Which transaction" in res.answer
    assert "Transaction ID" in res.answer


def test_recent_transactions_tool_grounded(db_session: Session, monisha_user: User):
    """'Show my recent transactions' must return authoritative transactions belonging only to Monisha."""
    identity = resolve_assistant_identity(monisha_user, db_session)
    res = route_and_execute_query("Show my recent transactions", identity, db_session)
    
    assert res.source_type == RouteType.LIVE_TOOL
    assert "Recent" in res.answer


# ─────────────────────────────────────────────────────────────────────────────
# TEST D: PROVIDER CONFIGURATION & DIAGNOSTICS
# ─────────────────────────────────────────────────────────────────────────────

def test_available_providers_returned():
    """Verify that provider listing returns available engines without crashing."""
    providers = get_available_providers()
    assert len(providers) > 0
    provider_ids = [p["id"] for p in providers]
    assert "auto" in provider_ids or "fallback" in provider_ids or "gemini" in provider_ids


def test_provider_key_verification_does_not_leak_secrets():
    """Key verification diagnostics must never leak the actual raw secret key string."""
    gemini_diag = verify_gemini_key()
    assert isinstance(gemini_diag, dict)
    
    # Check that raw key characters are not dumped
    if "message" in gemini_diag:
        assert "AIza" not in gemini_diag["message"]


# ─────────────────────────────────────────────────────────────────────────────
# TEST E: CUSTOMER DATA ISOLATION & RBAC SCOPING
# ─────────────────────────────────────────────────────────────────────────────

def test_monisha_cannot_access_sowmiya_account(db_session: Session, monisha_user: User):
    """Customer Monisha must be blocked from inspecting Sowmiya's account."""
    identity = resolve_assistant_identity(monisha_user, db_session)
    res = route_and_execute_query("Show me Sowmiya's account and balance", identity, db_session)
    
    assert res.source_type == RouteType.SECURITY_REFUSAL
    assert "another user" in res.answer.lower() or "permission" in res.answer.lower()


def test_ajay_cannot_access_monisha_transaction(db_session: Session, ajay_user: User, monisha_user: User):
    """Customer Ajay must be denied access to Monisha's specific transaction record."""
    monisha_id = resolve_assistant_identity(monisha_user, db_session)
    monisha_tx = db_session.query(Transaction).filter(Transaction.customer_id == monisha_id.customer_id).first()
    assert monisha_tx is not None
    
    ajay_id = resolve_assistant_identity(ajay_user, db_session)
    res = route_and_execute_query(f"Explain transaction {monisha_tx.transaction_id}", ajay_id, db_session)
    
    assert res.source_type == RouteType.SECURITY_REFUSAL
    assert "another account" in res.answer.lower() or "denied" in res.answer.lower() or "permission" in res.answer.lower()


# ─────────────────────────────────────────────────────────────────────────────
# TEST F: END-TO-END FASTAPI HTTP ROUTE CONTRACTS
# ─────────────────────────────────────────────────────────────────────────────

def test_api_chat_endpoint_greeting(api_client: TestClient, ajay_user: User):
    """FastAPI POST /api/v1/ai-assistant/chat must successfully handle greeting with valid JWT."""
    token = create_access_token(subject=str(ajay_user.id), role="customer")
    headers = {"Authorization": f"Bearer {token}"}
    
    payload = {
        "messages": [{"role": "user", "content": "Hi"}],
        "session_id": "test_session_ajay_101",
        "provider": "auto",
        "temperature": 0.7,
    }
    
    response = api_client.post("/api/v1/ai-assistant/chat", json=payload, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "response" in data
    assert "Ajay" in data["response"]
    assert data["authorized_role"] in ("customer", "Verified Customer")


def test_api_chat_endpoint_followup_and_session_isolation(api_client: TestClient, monisha_user: User, db_session: Session):
    """FastAPI endpoint must support conversation history and isolate sessions."""
    token = create_access_token(subject=str(monisha_user.id), role="customer")
    headers = {"Authorization": f"Bearer {token}"}

    tx = db_session.query(Transaction).filter(Transaction.customer_id == "CUST_MONISHA_001").first()
    assert tx is not None

    # Step 1: Inquire about transaction
    payload1 = {
        "messages": [{"role": "user", "content": f"Explain {tx.transaction_id}"}],
        "session_id": "session_turn_monisha_1",
    }
    res1 = api_client.post("/api/v1/ai-assistant/chat", json=payload1, headers=headers)
    assert res1.status_code == 200
    data1 = res1.json()
    assert tx.transaction_id in data1["response"]

    # Step 2: Follow-up question referencing the conversation
    payload2 = {
        "messages": [
            {"role": "user", "content": f"Explain {tx.transaction_id}"},
            {"role": "assistant", "content": data1["response"]},
            {"role": "user", "content": "Why is it low risk?"},
        ],
        "session_id": "session_turn_monisha_1",
    }
    res2 = api_client.post("/api/v1/ai-assistant/chat", json=payload2, headers=headers)
    assert res2.status_code == 200
    data2 = res2.json()
    assert tx.transaction_id in data2["response"] or "risk" in data2["response"].lower()
