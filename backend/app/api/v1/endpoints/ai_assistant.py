"""AI Assistant & Role-Aware Help Desk Endpoint.

Provides:
- Multi-LLM Chat Routing (Gemini 3.6/3.7, Grok-2, Mistral AI, AUTO Failover)
- Role-Aware Help Desk Context & Permission Resolution from Backend JWT
- Strict User Data Isolation (Customer vs Investigator vs Admin)
- Zero-Leak Security Boundaries (PCI-DSS & GDPR Compliance)
- Per-User Isolated Conversation History
"""

import re
import time
import json
import logging
from typing import Any, Dict, List, Optional, Union
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

from backend.app.services.assistant_session_service import session_memory, MAX_CONVERSATION_TURNS

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
    context: Optional[Union[str, Dict[str, Any]]] = Field(
        None,
        description="Optional domain context (e.g. transaction_id, current_view, or case object)",
    )
    role: Optional[str] = Field(
        None,
        description="Client hint (backend verifies against authenticated User.role)",
    )
    session_id: Optional[str] = Field(
        None,
        description="Conversation or session identifier for context scoping",
    )
    ui_context: Optional[Dict[str, Any]] = Field(
        None,
        description="Optional UI and current module context",
    )


class ChatResponse(BaseModel):
    response: str
    provider: str
    model: str
    used_real_api: bool
    routing: Optional[Dict[str, Any]] = None
    grok_challenge_applied: bool = False
    authorized_role: str = "customer"
    session_id: Optional[str] = None
    error_category: Optional[str] = None
    structured_metadata: Optional[Dict[str, Any]] = None


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
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: Session = Depends(get_db),
) -> HelpDeskContextResponse:
    """Return backend-verified role context and accessible modules for Help Desk."""
    if not current_user:
        return HelpDeskContextResponse(
            user_id=0,
            user_name="Guest Visitor",
            user_email="guest@fraudlens.public",
            authenticated_role="Public Guest",
            is_admin=False,
            is_investigator=False,
            is_customer=False,
            authorized_modules=[
                "AI Investigation Command Center",
                "Transaction Risk Analyzer",
                "Live Transaction Monitor",
                "Explainable AI",
                "Help Desk & Guide",
            ],
            accessible_entities={"scope": "PUBLIC_DEMO", "customer_records_masked": True},
            suggested_prompts=[
                {"label": "🤖 How does FraudLens detect fraud?", "query": "Explain how FraudLens detects financial fraud in under 4 milliseconds."},
                {"label": "🌲 XGBoost Champion", "query": "Why was XGBoost selected as the champion model over Random Forest?"},
                {"label": "🔍 Explainable AI (TreeSHAP)", "query": "How does TreeSHAP explain individual transaction risk scores?"},
                {"label": "📱 OTP Step-Up Threshold", "query": "Explain how the 30-70 threshold triggers mobile step-up verification."},
            ],
            security_clearance="PUBLIC_GUEST_ACCESS",
        )

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
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: Session = Depends(get_db),
) -> ChatResponse:
    """Route a chat conversation to the configured LLM with strict user isolation."""
    messages = [{"role": m.role, "content": m.content} for m in payload.messages]

    # Handle context whether passed as a dict or string
    if isinstance(payload.context, dict):
        context_str = " | ".join(f"{k}: {v}" for k, v in payload.context.items() if v is not None)
    elif payload.context:
        context_str = str(payload.context)
    else:
        context_str = ""

    from backend.app.services.assistant_identity_service import (
        resolve_assistant_identity,
        verify_and_enforce_isolation,
    )

    # Phase 4: Derive trusted identity context from authenticated JWT session
    identity = resolve_assistant_identity(current_user, db, session_id=payload.session_id)
    user_role = identity.role
    user_name = identity.name
    user_email = identity.email
    user_id = identity.user_id
    authorized_role = identity.role

    # ── PHASES 5 & 6: STRICT USER DATA ISOLATION & SCOPE ENFORCEMENT ──
    latest_query = next((m["content"] for m in reversed(messages) if m.get("role") == "user"), "")
    combined_query = f"{context_str} {latest_query}"

    is_allowed, refusal_msg = verify_and_enforce_isolation(
        identity=identity,
        user_prompt=combined_query,
        db=db,
    )
    if not is_allowed:
        return ChatResponse(
            response=refusal_msg or "I can't provide another user's account information. I can help you review your own transactions instead.",
            provider="FraudLens Security Shield",
            model="user-isolation-guard",
            used_real_api=False,
            authorized_role=authorized_role,
            session_id=payload.session_id,
            error_category="unauthorized_scope",
        )

    # ── PHASES 13-15: INTENT CLASSIFICATION & MUTATING ACTION HANDOFF ──
    from backend.app.services.assistant_intent_service import classify_user_intent
    intent_res = classify_user_intent(combined_query, identity, payload.ui_context)
    if intent_res.is_mutating_attempt:
        return ChatResponse(
            response=intent_res.handoff_message or "The assistant is strictly read-only and cannot execute payments or bypass security verifications.",
            provider="FraudLens Action Guard",
            model="read-only-safeguard",
            used_real_api=False,
            authorized_role=authorized_role,
            session_id=payload.session_id,
            error_category="mutating_action_prohibited",
        )

    from backend.app.services.assistant_financial_context_service import (
        build_safe_context_envelope,
        format_context_for_prompt,
    )

    # Phase 7-9: Build safe, minimal, auditable financial & transaction context envelope
    context_envelope = build_safe_context_envelope(
        identity=identity,
        user_query=combined_query,
        db=db,
        ui_context=payload.ui_context,
    )
    safe_evidence_prompt = format_context_for_prompt(context_envelope)

    # Inject verified domain context and clock into system instruction
    system_context_block = f"VERIFIED APPLICATION CONTEXT:\n{safe_evidence_prompt}"
    if context_str:
        system_context_block += f"\nUI State: {context_str}"

    # Phase 19: Prune incoming conversation history to bounded turn window (max 6 turns)
    bounded_turns = session_memory.prune_incoming_messages(messages, max_turns=MAX_CONVERSATION_TURNS)

    messages = [
        {
            "role": "system",
            "content": f"User: {user_name} ({user_role}).\n{system_context_block}",
        }
    ] + bounded_turns

    user_info = {
        "name": user_name,
        "role": user_role,
        "email": user_email,
        "user_id": user_id,
        "context_envelope": context_envelope,
    }

    start_time = time.time()
    try:
        result = chat_with_llm(
            messages=messages,
            provider=payload.provider,
            temperature=payload.temperature,
            role=user_role,
            user_info=user_info,
        )

        latency_ms = round((time.time() - start_time) * 1000, 2)

        # Record conversation in user's isolated session history
        if current_user:
            session_memory.record_turn(
                user_id=current_user.id,
                session_id=payload.session_id,
                user_msg=latest_query,
                assistant_msg=result.get("response", ""),
            )
            try:
                from backend.app.models.audit_log import AuditLog
                audit_entry = AuditLog(
                    user_id=current_user.id,
                    action="AI_ASSISTANT_QUERY",
                    resource_type="AI_ASSISTANT",
                    resource_id=payload.session_id or "default",
                    details=json.dumps({
                        "provider": result.get("provider"),
                        "model": result.get("model"),
                        "used_real_api": result.get("used_real_api"),
                        "role": user_role,
                        "latency_ms": latency_ms,
                        "session_id": payload.session_id,
                    }),
                )
                db.add(audit_entry)
                db.commit()
            except Exception as audit_err:
                logger.warning("Failed to record assistant audit log: %s", audit_err)

        return ChatResponse(
            response=result["response"],
            provider=result["provider"],
            model=result["model"],
            used_real_api=result["used_real_api"],
            routing=result.get("routing"),
            grok_challenge_applied=result.get("grok_challenge_applied", False),
            authorized_role=authorized_role,
            session_id=payload.session_id,
            error_category=None,
            structured_metadata=context_envelope,
        )
    except Exception as exc:
        logger.error("AI Assistant Chat exception: %s", exc, exc_info=True)
        return ChatResponse(
            response=(
                "AI service is temporarily unavailable. Please try again in a moment."
            ),
            provider="FraudLens Fallback Guardian",
            model="autonomous-failover-v2",
            used_real_api=False,
            authorized_role=authorized_role,
            session_id=payload.session_id,
            error_category="provider_error",
        )


@router.get(
    "/history",
    summary="Get Isolated User Chat History",
    description="Returns conversation history strictly for the authenticated user.",
)
def get_user_history(
    session_id: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
) -> Dict[str, Any]:
    """Retrieve isolated chat history for the current authenticated user only."""
    history = session_memory.get_history(current_user.id, session_id=session_id)
    return {
        "user_id": current_user.id,
        "email": current_user.email,
        "session_id": session_id,
        "history": history,
        "count": len(history),
    }


@router.delete(
    "/history",
    summary="Clear Isolated User Chat History",
    description="Clears conversation history strictly for the authenticated user.",
)
@router.post(
    "/session/clear",
    summary="Clear Isolated User Session",
    description="Clears session memory immediately upon logout or reset.",
)
def clear_user_history(
    session_id: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
) -> Dict[str, Any]:
    """Clear chat history for current authenticated user only."""
    purged = session_memory.purge_session(current_user.id, session_id=session_id)
    return {"success": True, "purged_count": purged, "message": "Chat history cleared successfully."}


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
