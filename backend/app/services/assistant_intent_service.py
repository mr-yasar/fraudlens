"""Assistant Intent Routing, Strict Read-Only Tools, & Action Handoff (Phases 13-15).

Provides:
- Phase 13: Deterministic & semantic classification of user intent
- Phase 14: Strict read-only tool execution layer (zero mutations allowed)
- Phase 15: Safe action handoff guidance and ambiguity resolution
"""

import enum
import re
import logging
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from backend.app.models.user import User
from backend.app.services.assistant_identity_service import AssistantIdentity, ROLE_CUSTOMER, ROLE_ADMIN, ROLE_INVESTIGATOR
from backend.app.services.assistant_financial_context_service import (
    build_safe_context_envelope,
    get_recent_transactions,
    get_pending_holds,
    get_wallet_account_summary,
    get_transaction_summary,
)
from backend.app.services.assistant_explainability_service import (
    explain_transaction_risk,
    explain_hold_status
)

logger = logging.getLogger("fraudlens.assistant.intent")


class AssistantIntent(str, enum.Enum):
    GREETING = "GREETING"
    TRANSACTION_INQUIRY = "TRANSACTION_INQUIRY"
    RISK_EXPLANATION = "RISK_EXPLANATION"
    HOLD_STATUS_INQUIRY = "HOLD_STATUS_INQUIRY"
    WALLET_INQUIRY = "WALLET_INQUIRY"
    SECURITY_ALERT_INQUIRY = "SECURITY_ALERT_INQUIRY"
    CAPABILITY_QUERY = "CAPABILITY_QUERY"
    MUTATING_ACTION_REQUEST = "MUTATING_ACTION_REQUEST"
    CROSS_USER_ACCESS_ATTEMPT = "CROSS_USER_ACCESS_ATTEMPT"
    ADMIN_INVESTIGATION = "ADMIN_INVESTIGATION"
    AMBIGUOUS_OR_GENERAL = "AMBIGUOUS_OR_GENERAL"


# Actions that an AI assistant MUST NEVER execute directly
MUTATING_PATTERNS = [
    r"\b(transfer|send|pay)\b.*\b(money|rupees|inr|cash|amount|funds|\d+)\b",
    r"\b(approve|release|clear|unfreeze|unblock)\b.*\b(payment|transaction|hold|transfer)\b",
    r"\b(bypass|skip|ignore|override)\b.*\b(otp|2fa|security|verification|pin)\b",
    r"\b(delete|drop|remove)\b.*\b(transaction|record|log|account|history)\b",
    r"\b(change|reset)\b.*\b(password|pin|credential)\b",
]

# Supported Read-Only Tools
READ_ONLY_TOOLS = {
    "get_recent_transactions",
    "get_transaction_details",
    "get_pending_holds",
    "get_wallet_summary",
    "get_risk_explanation",
}


class IntentClassificationResult:
    def __init__(
        self,
        intent: AssistantIntent,
        confidence: float,
        extracted_entities: Dict[str, Any],
        is_mutating_attempt: bool = False,
        suggested_tool: Optional[str] = None,
        handoff_action: Optional[str] = None,
        handoff_message: Optional[str] = None,
    ):
        self.intent = intent
        self.confidence = confidence
        self.extracted_entities = extracted_entities
        self.is_mutating_attempt = is_mutating_attempt
        self.suggested_tool = suggested_tool
        self.handoff_action = handoff_action
        self.handoff_message = handoff_message

    def to_dict(self) -> Dict[str, Any]:
        return {
            "intent": self.intent.value,
            "confidence": self.confidence,
            "extracted_entities": self.extracted_entities,
            "is_mutating_attempt": self.is_mutating_attempt,
            "suggested_tool": self.suggested_tool,
            "handoff_action": self.handoff_action,
            "handoff_message": self.handoff_message,
        }


def classify_user_intent(
    query: str,
    identity: AssistantIdentity,
    ui_context: Optional[Dict[str, Any]] = None,
) -> IntentClassificationResult:
    """Phase 13: Deterministic & semantic classification of incoming user intent."""
    clean_q = (query or "").strip().lower()
    entities: Dict[str, Any] = {}

    # Extract transaction ID if referenced (e.g., TX12345, TX_12345, #TX...)
    tx_match = re.search(r"\b(tx_?[a-zA-Z0-9_-]{4,30})\b", clean_q, re.IGNORECASE)
    if tx_match:
        entities["transaction_id"] = tx_match.group(1).upper()

    # Extract amount if present
    amt_match = re.search(r"(?:rs\.?|inr|₹)\s*(\d+(?:,\d+)*(?:\.\d+)?)|(\d+(?:,\d+)*(?:\.\d+)?)\s*(?:rs|rupees|inr|₹)", clean_q)
    if amt_match:
        raw_num = amt_match.group(1) or amt_match.group(2)
        try:
            entities["amount"] = float(raw_num.replace(",", ""))
        except ValueError:
            pass

    # Extract limit count (e.g. "last 3", "last 5", "last 10")
    limit_match = re.search(r"\b(?:last|recent|past)\s+(\d+)\b", clean_q)
    if limit_match:
        try:
            entities["limit"] = min(int(limit_match.group(1)), 20)
        except ValueError:
            entities["limit"] = 5

    # 1. Check for mutating / forbidden action requests
    for pat in MUTATING_PATTERNS:
        if re.search(pat, clean_q, re.IGNORECASE):
            if any(k in clean_q for k in ["bypass", "skip", "override", "otp"]):
                return IntentClassificationResult(
                    intent=AssistantIntent.MUTATING_ACTION_REQUEST,
                    confidence=0.99,
                    extracted_entities=entities,
                    is_mutating_attempt=True,
                    handoff_action="SECURITY_MODAL_OTP",
                    handoff_message=(
                        "For security reasons, the AI assistant cannot bypass, disclose, or override OTP verifications. "
                        "Please use the on-screen Security Verification modal to enter your secure OTP."
                    ),
                )
            if any(k in clean_q for k in ["approve", "release", "clear"]):
                return IntentClassificationResult(
                    intent=AssistantIntent.MUTATING_ACTION_REQUEST,
                    confidence=0.98,
                    extracted_entities=entities,
                    is_mutating_attempt=True,
                    handoff_action="SECURITY_APPROVAL_UI",
                    handoff_message=(
                        "Transactions on security hold cannot be approved directly via chat. "
                        "Please click the 'Allow OTP' or 'Open Phone & Allow OTP' button in the application to approve your transaction."
                    ),
                )
            # Fund transfer attempt
            return IntentClassificationResult(
                intent=AssistantIntent.MUTATING_ACTION_REQUEST,
                confidence=0.95,
                extracted_entities=entities,
                is_mutating_attempt=True,
                handoff_action="PAYMENT_GATEWAY_TRANSFER",
                handoff_message=(
                    "The AI assistant is strictly read-only and cannot execute payments or transfer funds on your behalf. "
                    "Please initiate transfers through the Send Money payment interface."
                ),
            )

    # 2. Hold Status Inquiry
    if any(k in clean_q for k in ["hold", "held", "pending", "frozen", "waiting otp", "blocked", "awaiting approval"]):
        return IntentClassificationResult(
            intent=AssistantIntent.HOLD_STATUS_INQUIRY,
            confidence=0.92,
            extracted_entities=entities,
            suggested_tool="get_pending_holds",
        )

    # 3. Risk & Explainability Inquiry
    if any(k in clean_q for k in ["why flagged", "risk score", "fraud probability", "why stopped", "why held", "flagged", "suspicious", "explain"]):
        return IntentClassificationResult(
            intent=AssistantIntent.RISK_EXPLANATION,
            confidence=0.90,
            extracted_entities=entities,
            suggested_tool="get_risk_explanation",
        )

    # 4. Wallet / Balance Inquiry
    if any(k in clean_q for k in ["balance", "wallet", "how much money", "account balance", "funds available"]):
        return IntentClassificationResult(
            intent=AssistantIntent.WALLET_INQUIRY,
            confidence=0.91,
            extracted_entities=entities,
            suggested_tool="get_wallet_summary",
        )

    # 5. Transaction Inquiry
    if any(k in clean_q for k in ["transactions", "recent transaction", "transaction history", "last payment", "transfers", "spent"]):
        return IntentClassificationResult(
            intent=AssistantIntent.TRANSACTION_INQUIRY,
            confidence=0.92,
            extracted_entities=entities,
            suggested_tool="get_recent_transactions",
        )

    # 6. Admin Investigation (Restricted to Admin / Investigator roles)
    if identity.role in [ROLE_ADMIN, ROLE_INVESTIGATOR] and any(k in clean_q for k in ["investigate", "audit", "model", "roc", "telemetry", "system radar", "sar"]):
        return IntentClassificationResult(
            intent=AssistantIntent.ADMIN_INVESTIGATION,
            confidence=0.94,
            extracted_entities=entities,
        )

    # 7. Greetings
    if re.search(r"^(hi|hello|hey|good\s+(morning|afternoon|evening)|howdy)\b", clean_q):
        return IntentClassificationResult(
            intent=AssistantIntent.GREETING,
            confidence=0.95,
            extracted_entities=entities,
        )

    # 8. Capability Query
    if any(k in clean_q for k in ["what can you do", "help me", "capabilities", "commands", "how do you work", "features"]):
        return IntentClassificationResult(
            intent=AssistantIntent.CAPABILITY_QUERY,
            confidence=0.90,
            extracted_entities=entities,
        )

    # Default to general inquiry
    return IntentClassificationResult(
        intent=AssistantIntent.AMBIGUOUS_OR_GENERAL,
        confidence=0.50,
        extracted_entities=entities,
    )


def execute_read_only_tool(
    tool_name: str,
    params: Dict[str, Any],
    db: Session,
    user: User,
    identity: AssistantIdentity,
) -> Dict[str, Any]:
    """Phase 14: Strict read-only tool execution layer. Zero mutations permitted."""
    if tool_name not in READ_ONLY_TOOLS:
        logger.warning(
            "Blocked attempt to invoke non-whitelisted or mutating tool '%s' by user %s",
            tool_name,
            identity.customer_id
        )
        return {
            "success": False,
            "error": "FORBIDDEN_MUTATING_ACTION",
            "message": f"Tool '{tool_name}' is not permitted in read-only assistant mode.",
        }

    logger.info("Executing safe read-only tool '%s' for user %s", tool_name, identity.customer_id)

    try:
        if tool_name == "get_recent_transactions":
            limit = int(params.get("limit", 5))
            tx_records = get_recent_transactions(
                identity.customer_id,
                db,
                limit=limit,
                is_admin=(identity.role == ROLE_ADMIN),
            )
            return {
                "success": True,
                "tool": tool_name,
                "count": len(tx_records),
                "data": tx_records,
            }

        elif tool_name == "get_pending_holds":
            holds = get_pending_holds(identity.customer_id, db)
            return {
                "success": True,
                "tool": tool_name,
                "count": len(holds),
                "data": holds,
            }

        elif tool_name == "get_wallet_summary":
            wallet = get_wallet_account_summary(identity.customer_id, db)
            return {
                "success": True,
                "tool": tool_name,
                "data": wallet,
            }

        elif tool_name == "get_risk_explanation":
            tx_id = params.get("transaction_id")
            from backend.app.models.transaction import Transaction
            from backend.app.models.shap_explanation import ShapExplanation

            query = db.query(Transaction).filter(Transaction.user_id == user.id)
            if tx_id:
                query = query.filter(Transaction.transaction_id == tx_id)
            tx = query.order_by(Transaction.created_at.desc()).first()

            if not tx:
                return {
                    "success": False,
                    "error": "TRANSACTION_NOT_FOUND",
                    "message": "No matching transaction was found for your account.",
                }

            shap_records = db.query(ShapExplanation).filter(ShapExplanation.transaction_id == tx.transaction_id).all()
            explanation = explain_transaction_risk(tx, shap_records=shap_records, is_admin=(identity.role == ROLE_ADMIN))
            return {
                "success": True,
                "tool": tool_name,
                "data": explanation,
            }

        return {
            "success": False,
            "error": "UNKNOWN_TOOL",
            "message": f"Handler for tool '{tool_name}' is not registered.",
        }

    except Exception as exc:
        logger.error("Exception during read-only tool execution '%s': %s", tool_name, exc, exc_info=True)
        return {
            "success": False,
            "error": "EXECUTION_FAILURE",
            "message": "Unable to retrieve real-time data at this moment.",
        }
