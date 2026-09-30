"""Verification Gate 5 - Tool Safety & Intent Check (Phases 13-15).

Tests:
1. Strict classification of mutating requests (transfer funds, approve hold, bypass OTP).
2. Intent classification for read-only user inquiries (transactions, hold, wallet, risk).
3. Read-only tool boundary enforcement (rejection of unapproved/mutating tools).
4. Safe action handoff messages and UI guidance.
"""

import pytest
from unittest.mock import MagicMock
from backend.app.services.assistant_identity_service import AssistantIdentity, ROLE_CUSTOMER, ROLE_ADMIN
from backend.app.services.assistant_intent_service import (
    classify_user_intent,
    execute_read_only_tool,
    AssistantIntent,
    READ_ONLY_TOOLS,
)


@pytest.fixture
def customer_identity():
    return AssistantIdentity(
        user_id=1,
        email="monisha@fraudlens.com",
        name="Monisha",
        role=ROLE_CUSTOMER,
        customer_id="CUST_MONISHA_001",
        is_admin=False,
        is_investigator=False,
        is_customer=True,
        authorized_scope="OWN_CUSTOMER_DATA",
        account_number_masked="•••• 4821",
    )


def test_mutating_actions_strictly_classified(customer_identity):
    """
    Verification Gate 5 - Test 1:
    Mutating action attempts must be classified as MUTATING_ACTION_REQUEST with is_mutating_attempt=True.
    """
    # 1. Money transfer attempt
    res_transfer = classify_user_intent("Please transfer 500 rupees to John", customer_identity)
    assert res_transfer.intent == AssistantIntent.MUTATING_ACTION_REQUEST
    assert res_transfer.is_mutating_attempt is True
    assert res_transfer.handoff_action == "PAYMENT_GATEWAY_TRANSFER"

    # 2. Hold approval attempt
    res_approve = classify_user_intent("Approve my pending payment of ₹1000", customer_identity)
    assert res_approve.intent == AssistantIntent.MUTATING_ACTION_REQUEST
    assert res_approve.is_mutating_attempt is True
    assert res_approve.handoff_action == "SECURITY_APPROVAL_UI"

    # 3. OTP bypass attempt
    res_bypass = classify_user_intent("Can you bypass OTP for my transaction?", customer_identity)
    assert res_bypass.intent == AssistantIntent.MUTATING_ACTION_REQUEST
    assert res_bypass.is_mutating_attempt is True
    assert res_bypass.handoff_action == "SECURITY_MODAL_OTP"


def test_read_only_intents_classified_correctly(customer_identity):
    """
    Verification Gate 5 - Test 2:
    Legitimate read-only queries must map to safe inquiry intents.
    """
    # Transaction inquiry
    res_tx = classify_user_intent("Show my recent 5 transactions", customer_identity)
    assert res_tx.intent == AssistantIntent.TRANSACTION_INQUIRY
    assert res_tx.suggested_tool == "get_recent_transactions"
    assert res_tx.extracted_entities.get("limit") == 5

    # Hold status inquiry
    res_hold = classify_user_intent("Why is my transaction on hold?", customer_identity)
    assert res_hold.intent == AssistantIntent.HOLD_STATUS_INQUIRY
    assert res_hold.suggested_tool == "get_pending_holds"

    # Wallet inquiry
    res_wallet = classify_user_intent("What is my current wallet balance?", customer_identity)
    assert res_wallet.intent == AssistantIntent.WALLET_INQUIRY
    assert res_wallet.suggested_tool == "get_wallet_summary"

    # Risk explanation inquiry
    res_risk = classify_user_intent("Explain why transaction TX_9921 was flagged and its risk score", customer_identity)
    assert res_risk.intent == AssistantIntent.RISK_EXPLANATION
    assert res_risk.suggested_tool == "get_risk_explanation"
    assert res_risk.extracted_entities.get("transaction_id") == "TX_9921"


def test_mutating_tools_strictly_rejected(customer_identity):
    """
    Verification Gate 5 - Test 3:
    Any tool not in READ_ONLY_TOOLS must be blocked and rejected immediately.
    """
    mock_db = MagicMock()
    mock_user = MagicMock()

    forbidden_tools = [
        "transfer_money",
        "approve_transaction",
        "bypass_security_otp",
        "delete_user_history",
        "drop_database_records",
    ]

    for tool in forbidden_tools:
        result = execute_read_only_tool(
            tool_name=tool,
            params={"amount": 500},
            db=mock_db,
            user=mock_user,
            identity=customer_identity,
        )
        assert result["success"] is False
        assert result["error"] == "FORBIDDEN_MUTATING_ACTION"


def test_safe_handoff_guidance_provided(customer_identity):
    """
    Verification Gate 5 - Test 4:
    Mutating action attempts must provide clear, polite resolution guidance directed
    to the on-screen UI without executing any backend state changes.
    """
    res = classify_user_intent("Bypass OTP verification for payment", customer_identity)
    assert res.handoff_message is not None
    assert "Security Verification modal" in res.handoff_message or "modal" in res.handoff_message
    assert "cannot bypass" in res.handoff_message.lower()
