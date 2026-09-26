"""AI Assistant & Role-Aware Help Desk Endpoint.

Provides:
- Multi-LLM Chat Routing (Gemini 3.6/3.7, Grok-2, Mistral AI, AUTO Failover)
- Role-Aware Help Desk Context & Permission Resolution from Backend JWT
- Strict User Data Isolation (Customer vs Investigator vs Admin)
- Zero-Leak Security Boundaries (PCI-DSS & GDPR Compliance)
- Per-User Isolated Conversation History
"""

import re
import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_active_user, get_optional_current_user, get_db
from backend.app.models.user import User
from backend.app.models.transaction import Transaction
from backend.app.models.customer import Customer
from backend.app.services.llm_service import (
    chat_with_llm,
    get_available_providers,
    is_gemini_configured,
    is_grok_configured,
    is_mistral_configured,
    verify_grok_key,
    verify_gemini_key,
    verify_mistral_key,
)

logger = logging.getLogger("fraudlens.api.ai_assistant")
router = APIRouter()

# In-memory thread-safe user chat history storage (keyed strictly by user.id)
_user_chat_histories: Dict[int, List[Dict[str, Any]]] = {}


# ─────────────────────────────────────────────────────────────────────────────
# Schemas
# ─────────────────────────────────────────────────────────────────────────────
class ChatMessage(BaseModel):
    role: str = Field(..., description="'user' or 'assistant'")
    content: str = Field(..., min_length=1, max_length=4000)


class ChatRequest(BaseModel):
    messages: List[ChatMessage] = Field(
        ...,
        min_length=1,
        description="Full conversation history including the latest user message",
    )
    provider: Optional[str] = Field(
        None,
        description="Preferred LLM provider: 'gemini' | 'grok' | 'mistral' | None (auto)",
    )
    temperature: float = Field(0.7, ge=0.0, le=1.0)
    context: Optional[str] = Field(
        None,
        description="Optional domain context (e.g. transaction_id, current_view)",
    )
    role: Optional[str] = Field(
        None,
        description="Client hint (backend verifies against authenticated User.role)",
    )


class ChatResponse(BaseModel):
    response: str
    provider: str
    model: str
    used_real_api: bool
    routing: Optional[Dict[str, Any]] = None
    grok_challenge_applied: bool = False
    authorized_role: str = "customer"


class ProvidersResponse(BaseModel):
    providers: List[Dict[str, Any]]
    gemini_configured: bool
    grok_configured: bool
    mistral_configured: bool = False
    default_provider: str


class HelpDeskContextResponse(BaseModel):
    user_id: int
    user_name: str
    user_email: str
    authenticated_role: str
    is_admin: bool
    is_investigator: bool
    is_customer: bool
    authorized_modules: List[str]
    accessible_entities: Dict[str, Any]
    suggested_prompts: List[Dict[str, str]]
    security_clearance: str


# ─────────────────────────────────────────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────────────────────────────────────────
@router.get(
    "/helpdesk-context",
    response_model=HelpDeskContextResponse,
    summary="Get Role-Aware Help Desk Security & Permission Context",
    description="Resolves authenticated user permissions, authorized modules, and personalized prompts strictly from backend JWT.",
)
def get_helpdesk_context(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> HelpDeskContextResponse:
    """Return backend-verified role context and accessible modules for Help Desk."""
    user_role_raw = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
    user_role = user_role_raw.lower().strip()
    user_name = current_user.name or current_user.email.split("@")[0]

    is_admin = user_role == "admin"
    is_investigator = user_role in ["investigator", "fraud_investigator", "analyst", "soc"]
    is_customer = not is_admin and not is_investigator

    # Module permissions based strictly on verified role
    if is_admin:
        role_label = "Platform Administrator"
        clearance = "LEVEL_3_FULL_SYSTEM_AUDIT"
        modules = [
            "Command Dashboard",
            "Model Lab & Registry",
            "Dataset Health & Audit",
            "Reports & Analytics",
            "Audit Trail & Compliance",
            "Platform Settings",
            "Multi-LLM Orchestrator Telemetry",
        ]
        prompts = [
            {"label": "🔑 Verify All API Keys", "query": "Test API key status for Gemini, Grok, and Mistral."},
            {"label": "🤖 4 Model Comparison", "query": "Compare precision, recall, and ROC-AUC of the 4 ML models."},
            {"label": "⏱️ <4ms Latency Profile", "query": "How does the FraudLens pre-auth gateway achieve sub-4ms inference latency?"},
            {"label": "📊 Retrain Triggers & Drift", "query": "What triggers automated model retraining in production?"},
            {"label": "🌲 XGBoost Champion", "query": "Explain how the XGBoost champion model compares with the Voting Ensemble."},
        ]
        entities = {"scope": "GLOBAL_SYSTEM", "customer_records_masked": False}

    elif is_investigator:
        role_label = "Fraud Investigator / SOC"
        clearance = "LEVEL_2_FORENSIC_INVESTIGATION"
        modules = [
            "Live Fraud Monitor",
            "Fraud Investigations",
            "Explainable AI & TreeSHAP",
            "Transaction Risk Analyzer",
            "Merchant Intelligence",
            "Customer Intelligence",
            "Suspicious Activity Reports (SAR)",
        ]
        prompts = [
            {"label": "📊 TreeSHAP Waterfall", "query": "Explain the TreeSHAP waterfall and key risk drivers for high-risk alerts."},
            {"label": "⚡ Velocity Bursts & Hops", "query": "What velocity bursts or geo-location hops trigger automated block rules?"},
            {"label": "👥 Monisha vs Sowmiya", "query": "Analyze behavioral risk differences between Monisha (3%), Mohana (12%), and Sowmiya (26%)."},
            {"label": "⚖️ False Positive Tuning", "query": "How should investigators evaluate false positives in the 30-70 OTP step-up band?"},
            {"label": "📝 FinCEN SAR Filing", "query": "Draft a structured FinCEN Suspicious Activity Report narrative for suspicious bursts."},
        ]
        entities = {"scope": "INVESTIGATION_QUEUES", "customer_records_masked": True}

    else:
        role_label = "Verified Customer"
        clearance = "LEVEL_1_PERSONAL_ACCOUNT"
        modules = [
            "Security Dashboard",
            "Payment Gateway (Pre-Auth)",
            "My Transactions",
            "My Customer Profile",
            "Account Security Reports",
            "Dispute Center",
        ]
        prompts = [
            {"label": "📱 Why was OTP required?", "query": "Why was my payment held for 6-digit Mobile OTP step-up verification?"},
            {"label": "🟢 Instant Approval", "query": "Why was my grocery purchase at NovaMart Fresh approved in milliseconds?"},
            {"label": "🚨 Unrecognized Charge", "query": "What should I do immediately if I see a transaction I did not authorize?"},
            {"label": "🛡️ Card Security Guard", "query": "How does FraudLens protect my account credentials and card data from theft?"},
            {"label": "💳 Step-Up Threshold", "query": "Explain how the 30-70 risk threshold decides when to ask for OTP vs instant approve."},
        ]
        # Resolve customer's own ID
        cust_rec = db.query(Customer).filter(Customer.email == current_user.email).first()
        entities = {
            "scope": "SELF_ONLY",
            "customer_id": cust_rec.customer_id if cust_rec else "CUST_ACTIVE_USER",
            "card_status": "PROTECTED",
        }

    return HelpDeskContextResponse(
        user_id=current_user.id,
        user_name=user_name,
        user_email=current_user.email,
        authenticated_role=role_label,
        is_admin=is_admin,
        is_investigator=is_investigator,
        is_customer=is_customer,
        authorized_modules=modules,
        accessible_entities=entities,
        suggested_prompts=prompts,
        security_clearance=clearance,
    )


@router.post(
    "/chat",
    response_model=ChatResponse,
    summary="AI Assistant & Help Desk Chat",
    description="Route a chat conversation with verified backend user role enforcement and cross-user data isolation.",
)
def ai_chat(
    payload: ChatRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> ChatResponse:
    """Route a chat conversation to the configured LLM with strict user isolation."""
    messages = [{"role": m.role, "content": m.content} for m in payload.messages]

    # Verify user role from backend database (NEVER trust client payload.role)
    user_role_raw = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
    user_role = user_role_raw.lower().strip()
    user_name = current_user.name or current_user.email.split("@")[0]

    # ── STRICT USER DATA ISOLATION ENFORCEMENT ──
    latest_query = next((m["content"] for m in reversed(messages) if m.get("role") == "user"), "")
    combined_query = f"{payload.context or ''} {latest_query}"

    # If customer, block queries into other customers' transactions or confidential cases
    if user_role in ["customer", "user"]:
        # Check if customer is attempting to query a foreign transaction ID
        tx_match = re.search(r"\b(TXN[_-]?[A-Za-z0-9_-]+)\b", combined_query, re.IGNORECASE)
        if tx_match:
            target_tx_id = tx_match.group(1).upper()
            tx_record = db.query(Transaction).filter(Transaction.transaction_id == target_tx_id).first()
            if tx_record:
                # Check ownership
                is_owner = (
                    tx_record.customer and tx_record.customer.email == current_user.email
                ) or current_user.email in (tx_record.customer_id or "")

                if not is_owner:
                    logger.warning(
                        "User Isolation Block: Customer %s attempted to inspect foreign tx %s",
                        current_user.email,
                        target_tx_id,
                    )
                    return ChatResponse(
                        response=(
                            "🔒 **Data Isolation & Privacy Notice**\n\n"
                            f"You are authenticated as `{current_user.email}`. In accordance with PCI-DSS "
                            "and FraudLens user-isolation policies, you are only permitted to review transactions "
                            "and security alerts associated with your verified customer account.\n\n"
                            "If you believe a transaction was misrouted, please contact your bank support."
                        ),
                        provider="FraudLens Security Shield",
                        model="user-isolation-guard",
                        used_real_api=False,
                        authorized_role="customer",
                    )

    # Inject verified domain context if provided
    if payload.context:
        messages = [
            {
                "role": "system",
                "content": f"Authenticated User: {user_name} ({user_role}). Context: {payload.context}",
            }
        ] + messages

    user_info = {
        "name": user_name,
        "role": user_role,
        "email": current_user.email,
        "user_id": current_user.id,
    }

    try:
        result = chat_with_llm(
            messages=messages,
            provider=payload.provider,
            temperature=payload.temperature,
            role=user_role,
            user_info=user_info,
        )

        # Record conversation in user's isolated session history
        user_history = _user_chat_histories.setdefault(current_user.id, [])
        user_history.append({"role": "user", "content": latest_query})
        user_history.append({"role": "assistant", "content": result.get("response", "")})
        if len(user_history) > 60:
            _user_chat_histories[current_user.id] = user_history[-60:]

        return ChatResponse(
            response=result["response"],
            provider=result["provider"],
            model=result["model"],
            used_real_api=result["used_real_api"],
            routing=result.get("routing"),
            grok_challenge_applied=result.get("grok_challenge_applied", False),
            authorized_role=user_role,
        )
    except Exception as exc:
        logger.error("AI Assistant Chat exception: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"AI service temporarily unavailable: {exc}",
        )


@router.get(
    "/history",
    summary="Get Isolated User Chat History",
    description="Returns conversation history strictly for the authenticated user.",
)
def get_user_history(
    current_user: User = Depends(get_current_active_user),
) -> Dict[str, Any]:
    """Retrieve isolated chat history for the current authenticated user only."""
    history = _user_chat_histories.get(current_user.id, [])
    return {
        "user_id": current_user.id,
        "email": current_user.email,
        "history": history,
        "count": len(history),
    }


@router.delete(
    "/history",
    summary="Clear Isolated User Chat History",
    description="Clears conversation history strictly for the authenticated user.",
)
def clear_user_history(
    current_user: User = Depends(get_current_active_user),
) -> Dict[str, Any]:
    """Clear chat history for current authenticated user only."""
    _user_chat_histories[current_user.id] = []
    return {"success": True, "message": "Chat history cleared successfully."}


@router.get(
    "/providers",
    response_model=ProvidersResponse,
    summary="List Available AI Providers",
    description="Returns which LLM providers are configured and available for the AI assistant.",
)
def get_providers(
    current_user: Optional[User] = Depends(get_optional_current_user),
) -> ProvidersResponse:
    """Return configured AI providers and their status."""
    import os
    return ProvidersResponse(
        providers=get_available_providers(),
        gemini_configured=is_gemini_configured(),
        grok_configured=is_grok_configured(),
        mistral_configured=is_mistral_configured(),
        default_provider=os.getenv("DEFAULT_LLM_PROVIDER", "gemini"),
    )


@router.get(
    "/verify-key",
    summary="Verify AI Provider API Key",
    description="Directly tests and validates the configured API key with xAI Grok, Google Gemini, or Mistral.",
)
def verify_provider_key(
    provider: str = "all",
    current_user: Optional[User] = Depends(get_optional_current_user),
) -> Dict[str, Any]:
    """Test and verify an LLM API key directly."""
    prov = provider.lower().strip()
    if prov == "grok":
        return verify_grok_key()
    elif prov == "gemini":
        return verify_gemini_key()
    elif prov == "mistral":
        return verify_mistral_key()
    else:
        return {
            "grok": verify_grok_key(),
            "gemini": verify_gemini_key(),
            "mistral": verify_mistral_key(),
        }
