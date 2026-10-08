"""Hybrid Assistant Central Policy Router & Decision Engine.

Implements Phases 05, 10, 15, 16, and 17 of the 24-Phase Chatbot Remodel:
- Enforces strict Precedence:
  1. Action Safeguard (zero mutations: no money transfer, no OTP bypass)
  2. Data Isolation & RBAC Guard (server-side verification)
  3. Live Tool Engine (transaction IDs, customer lookups, ranking requests)
  4. Curated Predefined Answer Engine (deterministic, 85+ approved families, conf >= 0.72)
  5. Grounded Project RAG Engine (chunked verified corpus, score >= 0.45)
  6. Selective LLM Synthesis / Resilient Fallback
- Records non-sensitive telemetry on every turn
"""

import time
import logging
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from backend.app.services.assistant_identity_service import (
    AssistantIdentity,
    verify_and_enforce_isolation,
    ROLE_CUSTOMER,
    ROLE_INVESTIGATOR,
    ROLE_ADMIN,
)
from backend.app.services.assistant_intent_service import classify_user_intent, AssistantIntent
from backend.app.services.hybrid_assistant.taxonomy import (
    AssistantResponseEnvelope,
    ConfidenceBand,
    ResponseCardType,
    RouteType,
)
from backend.app.services.hybrid_assistant.normalizer import (
    normalize_query_text,
    extract_entities,
)
from backend.app.services.hybrid_assistant.matcher import match_intent, get_confidence_band
from backend.app.services.hybrid_assistant.rag_engine import (
    retrieve_rag_candidates,
    format_rag_answer,
)
from backend.app.services.hybrid_assistant.investigation_tools import (
    tool_lookup_transaction,
    tool_explain_transaction,
    tool_lookup_customer,
    tool_summarize_case,
    tool_get_highest_risk_transactions,
    tool_get_recent_suspicious_activity,
    tool_get_recent_customer_transactions,
)
from backend.app.services.hybrid_assistant.reasoning_composer import (
    compose_predefined_response,
    compose_transaction_investigation_response,
    compose_customer_profile_response,
    compose_ranking_response,
)
from backend.app.services.hybrid_assistant.telemetry import telemetry_service
from backend.app.services.llm_service import chat_with_llm

logger = logging.getLogger("fraudlens.assistant.router")


def route_and_execute_query(
    query: str,
    identity: AssistantIdentity,
    db: Session,
    ui_context: Optional[Dict[str, Any]] = None,
    conversation_context: Optional[Dict[str, Any]] = None,
    provider: Optional[str] = None,
) -> AssistantResponseEnvelope:
    """Execute end-to-end routing policy over incoming user query."""
    start_time = time.time()
    norm_query = normalize_query_text(query)

    # ─────────────────────────────────────────────────────────────────────────
    # STEP 1: MUTATING ACTION SAFEGUARD (Phase 16)
    # ─────────────────────────────────────────────────────────────────────────
    intent_check = classify_user_intent(query, identity, ui_context)
    if intent_check.is_mutating_attempt:
        latency = round((time.time() - start_time) * 1000, 2)
        telemetry_service.record_interaction(
            query=query,
            route=RouteType.MUTATING_BLOCKED.value,
            intent="MUTATING_ACTION_ATTEMPT",
            confidence=0.99,
            latency_ms=latency,
        )
        return AssistantResponseEnvelope(
            response_type=ResponseCardType.NEXT_STEP.value,
            answer=intent_check.handoff_message or "FraudLens Assistant is strictly read-only and cannot execute payments or bypass security verifications.",
            evidence_refs=["security/action_guard"],
            follow_up_suggestions=["What can this chatbot do?", "How does authentication work?"],
            confidence=0.99,
            source_type=RouteType.MUTATING_BLOCKED,
            structured_card={
                "card_type": "security_handoff",
                "action": intent_check.handoff_action or "ACTION_BLOCKED",
            },
            debug_routing={"rule": "MUTATING_ACTION_GUARD"},
        )

    # 1B. SECRET / API KEY EXFILTRATION GUARD
    lower_q = (query or "").lower()
    is_diagnostic_q = any(d in lower_q for d in ["test", "verify", "status", "check", "working", "health", "diagnostics", "active"])
    if not is_diagnostic_q and any(k in lower_q for k in ["api_key", "apikey", "secret_key", "secret key", "give me the secret", "gemini_api_key", "grok_api_key", "mistral_api_key", "private key"]):
        latency = round((time.time() - start_time) * 1000, 2)
        telemetry_service.record_interaction(
            query=query,
            route=RouteType.SECURITY_REFUSAL.value,
            intent="SECRET_EXFILTRATION_BLOCKED",
            confidence=0.99,
            latency_ms=latency,
        )
        return AssistantResponseEnvelope(
            response_type=ResponseCardType.EXPLANATION.value,
            answer="Internal API keys, database credentials, and security tokens cannot be disclosed under FraudLens zero-leak security policies. All keys remain protected in backend enclaves.",
            evidence_refs=["security/zero_leak"],
            follow_up_suggestions=["How does authentication work?", "What can this chatbot do?"],
            confidence=0.99,
            source_type=RouteType.SECURITY_REFUSAL,
            structured_card={"card_type": "security_refusal"},
            debug_routing={"rule": "SECRET_EXFILTRATION_GUARD"},
        )

    # ─────────────────────────────────────────────────────────────────────────
    # STEP 2: USER DATA ISOLATION GUARD (Phase 16)
    # ─────────────────────────────────────────────────────────────────────────
    is_allowed, refusal_msg = verify_and_enforce_isolation(identity, query, db)
    if not is_allowed:
        latency = round((time.time() - start_time) * 1000, 2)
        telemetry_service.record_interaction(
            query=query,
            route=RouteType.SECURITY_REFUSAL.value,
            intent="CROSS_USER_ACCESS",
            confidence=0.99,
            latency_ms=latency,
        )
        return AssistantResponseEnvelope(
            response_type=ResponseCardType.EXPLANATION.value,
            answer=refusal_msg or "I can't provide another user's account information. I can help you review your own transactions instead.",
            evidence_refs=["security/rbac_isolation"],
            follow_up_suggestions=["What can this chatbot do?", "How does the chatbot protect restricted data?"],
            confidence=0.99,
            source_type=RouteType.SECURITY_REFUSAL,
            structured_card={"card_type": "security_refusal"},
            debug_routing={"rule": "CROSS_USER_DATA_ISOLATION"},
        )

    # ─────────────────────────────────────────────────────────────────────────
    # STEP 3: ENTITY EXTRACTION & LIVE INVESTIGATION TOOL ROUTING (Phase 13)
    # ─────────────────────────────────────────────────────────────────────────
    entities = extract_entities(query, conversation_context)

    # 3A. Specific Transaction Inquiry / Explanation
    if entities.transaction_ids:
        target_tx_id = entities.transaction_ids[0]
        if entities.is_why_question or "explain" in norm_query or "risk" in norm_query:
            bundle = tool_explain_transaction(target_tx_id, identity, db)
        else:
            bundle = tool_lookup_transaction(target_tx_id, identity, db)

        latency = round((time.time() - start_time) * 1000, 2)
        telemetry_service.record_interaction(
            query=query,
            route=RouteType.LIVE_TOOL.value,
            intent="LIVE_TRANSACTION_INVESTIGATION",
            confidence=0.99,
            latency_ms=latency,
            tool_status="ERROR" if bundle.error_message else "SUCCESS",
        )
        return compose_transaction_investigation_response(
            bundle=bundle,
            debug_info={"route": "LIVE_TOOL", "target_tx": target_tx_id, "latency_ms": latency},
        )

    # 3B. Ranking Inquiries (e.g. "Highest-risk transaction today", "top risk payments")
    if entities.is_ranking_request and ("transaction" in norm_query or "payment" in norm_query or "risk" in norm_query):
        bundle = tool_get_highest_risk_transactions(identity, db, limit=5)
        latency = round((time.time() - start_time) * 1000, 2)
        telemetry_service.record_interaction(
            query=query,
            route=RouteType.LIVE_TOOL.value,
            intent="LIVE_RANKING_QUERY",
            confidence=0.98,
            latency_ms=latency,
        )
        return compose_ranking_response(
            bundle=bundle,
            title="Authoritative Highest-Risk Transactions",
            items_key="ranked_items",
            debug_info={"route": "LIVE_TOOL", "query_type": "ranking", "latency_ms": latency},
        )

    # 3C. Recent Suspicious Activity
    if "suspicious" in norm_query and ("activity" in norm_query or "transaction" in norm_query or "recent" in norm_query):
        bundle = tool_get_recent_suspicious_activity(identity, db, limit=5)
        latency = round((time.time() - start_time) * 1000, 2)
        telemetry_service.record_interaction(
            query=query,
            route=RouteType.LIVE_TOOL.value,
            intent="LIVE_SUSPICIOUS_QUERY",
            confidence=0.98,
            latency_ms=latency,
        )
        return compose_ranking_response(
            bundle=bundle,
            title="Recent Suspicious & Blocked Transactions",
            items_key="suspicious_items",
            debug_info={"route": "LIVE_TOOL", "query_type": "suspicious", "latency_ms": latency},
        )

    # 3C.2. Recent Transactions (e.g. "Show my recent transactions", "spending history")
    if any(k in norm_query for k in ["recent transaction", "my recent transaction", "transaction history", "my transaction", "spending history", "recent spend"]):
        bundle = tool_get_recent_customer_transactions(identity, db, limit=5)
        latency = round((time.time() - start_time) * 1000, 2)
        telemetry_service.record_interaction(
            query=query,
            route=RouteType.LIVE_TOOL.value,
            intent="LIVE_RECENT_TRANSACTIONS",
            confidence=0.98,
            latency_ms=latency,
        )
        return compose_ranking_response(
            bundle=bundle,
            title="Recent Account Transactions",
            items_key="recent_items",
            debug_info={"route": "LIVE_TOOL", "query_type": "recent_transactions", "latency_ms": latency},
        )

    # 3D. Customer Profile Lookup (e.g. "Customer Monisha", "Lookup CUST_001")
    if (entities.customer_ids or entities.customer_names) and any(w in norm_query for w in ["lookup", "customer", "profile", "who is"]):
        target_cust = entities.customer_ids[0] if entities.customer_ids else entities.customer_names[0]
        bundle = tool_lookup_customer(target_cust, identity, db)
        latency = round((time.time() - start_time) * 1000, 2)
        telemetry_service.record_interaction(
            query=query,
            route=RouteType.LIVE_TOOL.value,
            intent="LIVE_CUSTOMER_LOOKUP",
            confidence=0.98,
            latency_ms=latency,
        )
        return compose_customer_profile_response(
            bundle=bundle,
            debug_info={"route": "LIVE_TOOL", "customer": target_cust, "latency_ms": latency},
        )

    # 3E. Case Summary Lookup
    if entities.case_ids:
        target_case_id = entities.case_ids[0]
        bundle = tool_summarize_case(target_case_id, identity, db)
        latency = round((time.time() - start_time) * 1000, 2)
        telemetry_service.record_interaction(
            query=query,
            route=RouteType.LIVE_TOOL.value,
            intent="LIVE_CASE_LOOKUP",
            confidence=0.98,
            latency_ms=latency,
        )
        case_info = bundle.investigation or {}
        answer = (
            f"### 📋 Case Summary: `{case_info.get('case_id', target_case_id)}`\n\n"
            f"- **Associated Transaction**: `{case_info.get('transaction_id')}`\n"
            f"- **Priority**: `{case_info.get('priority')}`\n"
            f"- **Current Status**: `{case_info.get('status')}`\n"
            f"- **Assigned Investigator**: {case_info.get('assigned_to')}\n"
            f"- **Forensic Notes**: {case_info.get('notes')}\n"
        ) if not bundle.error_message else f"⚠️ **Notice**: {bundle.error_message}"

        return AssistantResponseEnvelope(
            response_type=ResponseCardType.INVESTIGATION_RESULT.value,
            answer=answer,
            evidence_refs=[f"db/cases/{target_case_id}"],
            follow_up_suggestions=["How should an investigator review a high-risk alert?", "What is an investigation case?"],
            confidence=0.98,
            source_type=RouteType.LIVE_TOOL,
            structured_card={"card_type": "case_summary", "data": case_info},
            debug_routing={"route": "LIVE_TOOL", "case_id": target_case_id, "latency_ms": latency},
        )

    # 3F. AI Provider Live Diagnostic Health Check
    if any(k in norm_query for k in [
        "test api key", "verify key", "provider status", "check api key",
        "verify provider", "is mistral working", "is gemini working",
        "is grok working", "ai engine status", "test mistral", "test gemini",
        "test grok", "key status", "test ai engines", "check providers", "test ai keys"
    ]):
        from backend.app.services.hybrid_assistant.investigation_tools import tool_check_provider_status
        from backend.app.services.hybrid_assistant.reasoning_composer import compose_provider_status_response
        bundle = tool_check_provider_status()
        latency = round((time.time() - start_time) * 1000, 2)
        telemetry_service.record_interaction(
            query=query,
            route=RouteType.LIVE_TOOL.value,
            intent="LIVE_PROVIDER_DIAGNOSTICS",
            confidence=0.99,
            latency_ms=latency,
        )
        return compose_provider_status_response(
            bundle=bundle,
            debug_info={"route": "LIVE_TOOL", "tool": "provider_diagnostics", "latency_ms": latency},
        )

    # ─────────────────────────────────────────────────────────────────────────
    # STEP 4: CURATED PREDEFINED ANSWER ENGINE (Phase 07 & 08)
    # ─────────────────────────────────────────────────────────────────────────
    match_result = match_intent(norm_query, threshold=0.72)
    if match_result:
        record, candidate = match_result
        latency = round((time.time() - start_time) * 1000, 2)
        telemetry_service.record_interaction(
            query=query,
            route=RouteType.PREDEFINED.value,
            intent=record.intent,
            confidence=candidate.confidence,
            latency_ms=latency,
        )
        return compose_predefined_response(
            record=record,
            debug_info={
                "route": "PREDEFINED",
                "intent": record.intent,
                "confidence": candidate.confidence,
                "latency_ms": latency,
            },
        )

    # ─────────────────────────────────────────────────────────────────────────
    # STEP 5: GROUNDED PROJECT RAG ENGINE (Phase 11 & 12)
    # ─────────────────────────────────────────────────────────────────────────
    rag_candidates = retrieve_rag_candidates(norm_query, top_k=2, min_score=0.45)
    if rag_candidates:
        grounded_answer, citations = format_rag_answer(rag_candidates, norm_query)
        latency = round((time.time() - start_time) * 1000, 2)
        telemetry_service.record_interaction(
            query=query,
            route=RouteType.RAG.value,
            intent="PROJECT_RAG_RETRIEVAL",
            confidence=rag_candidates[0][1],
            latency_ms=latency,
        )
        return AssistantResponseEnvelope(
            response_type=ResponseCardType.EXPLANATION.value,
            answer=grounded_answer,
            evidence_refs=citations,
            follow_up_suggestions=[
                "What is FraudLens AI?",
                "Which ML models are used?",
                "How does FraudLens detect suspicious transactions?",
            ],
            confidence=rag_candidates[0][1],
            source_type=RouteType.RAG,
            structured_card={
                "card_type": ResponseCardType.EVIDENCE_SUMMARY.value,
                "chunks": [c[0].title for c in rag_candidates],
            },
            debug_routing={
                "route": "RAG",
                "top_score": rag_candidates[0][1],
                "sources": citations,
                "latency_ms": latency,
            },
        )

    # ─────────────────────────────────────────────────────────────────────────
    # STEP 6: SAFE FALLBACK & GUIDED CLARIFICATION (Phase 10 & 17)
    # ─────────────────────────────────────────────────────────────────────────
    latency = round((time.time() - start_time) * 1000, 2)
    telemetry_service.record_interaction(
        query=query,
        route=RouteType.SAFE_FALLBACK.value,
        intent="UNKNOWN_FALLBACK",
        confidence=0.20,
        latency_ms=latency,
        fallback_reason="No high-confidence match in predefined library or project RAG corpus",
    )

    fallback_text = (
        "I couldn't locate an authoritative project match for that question in the FraudLens registry. "
        "To ensure 100% factual accuracy with zero AI hallucination, I only answer verified topics.\n\n"
        "**Here are topics I can help you with right now**:\n"
        "- 🔍 **Live Investigation**: Ask about any transaction ID (e.g., *'Why is TX-1042 high risk?'*)\n"
        "- 🌲 **Machine Learning & SHAP**: Ask *'Which ML models are used?'* or *'What is a SHAP value?'*\n"
        "- 🛡️ **Risk & Security**: Ask *'What is High Risk?'* or *'How does authentication work?'*\n"
        "- 👥 **Personas & Merchants**: Ask *'Who are the customer personas?'* or *'List the 29 merchants'*."
    )

    return AssistantResponseEnvelope(
        response_type=ResponseCardType.GENERAL_CARD.value,
        answer=fallback_text,
        evidence_refs=["registry/knowledge_boundary"],
        follow_up_suggestions=[
            "What is FraudLens AI?",
            "What is risk score?",
            "Which ML models are used?",
            "Can the chatbot explain a transaction?",
        ],
        confidence=0.30,
        source_type=RouteType.SAFE_FALLBACK,
        structured_card={"card_type": "fallback_guidance"},
        debug_routing={"route": "SAFE_FALLBACK", "latency_ms": latency},
    )
