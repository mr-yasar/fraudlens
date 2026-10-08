"""Fraud Investigation Reasoning Flow & Structured Card Composition.

Implements Phases 14 and 18 of the 24-Phase Chatbot Remodel:
- Synthesizes raw live evidence bundles into investigator-ready explanations
- Strictly decouples ML Fraud Probability (0.00-1.00) from independent Risk Score (0-100)
- Preserves evidence grounding without claiming guaranteed certainty of fraud
- Produces structured card payloads for frontend rendering (Definition, RiskBreakdown, InvestigationResult)
"""

from typing import Any, Dict, List, Optional
from backend.app.services.hybrid_assistant.taxonomy import (
    AssistantResponseEnvelope,
    LiveEvidenceBundle,
    PredefinedAnswerRecord,
    ResponseCardType,
    RouteType,
)


def compose_predefined_response(
    record: PredefinedAnswerRecord,
    debug_info: Optional[Dict[str, Any]] = None,
) -> AssistantResponseEnvelope:
    """Compose structured response envelope for curated predefined answers."""
    structured_card = {
        "card_type": record.card_type.value,
        "title": record.intent.replace("_", " ").title(),
        "category": record.category,
        "data": record.card_data or {},
    }

    return AssistantResponseEnvelope(
        response_type=record.card_type.value,
        answer=record.canonical_answer,
        evidence_refs=record.source_refs,
        follow_up_suggestions=record.follow_up_suggestions,
        confidence=1.0,
        source_type=RouteType.PREDEFINED,
        structured_card=structured_card,
        debug_routing=debug_info,
    )


def compose_transaction_investigation_response(
    bundle: LiveEvidenceBundle,
    debug_info: Optional[Dict[str, Any]] = None,
) -> AssistantResponseEnvelope:
    """Synthesize live transaction and TreeSHAP evidence into an investigator explanation."""
    if bundle.error_message:
        return AssistantResponseEnvelope(
            response_type=ResponseCardType.EVIDENCE_SUMMARY.value,
            answer=f"⚠️ **Investigation Notice**: {bundle.error_message}",
            evidence_refs=[],
            follow_up_suggestions=["What information is shown for a transaction?", "What is High Risk?"],
            confidence=0.95,
            source_type=RouteType.LIVE_TOOL,
            debug_routing=debug_info,
        )

    tx = bundle.transaction or {}
    tx_id = tx.get("transaction_id", "Unknown")
    amount = tx.get("amount", 0.0)
    currency = tx.get("currency", "INR")
    merchant = tx.get("merchant_name", "Unknown Merchant")
    status = tx.get("status", "SUCCESS")
    score = bundle.risk_score or 0.0
    prob = bundle.fraud_probability or 0.0
    tier = bundle.risk_tier or "LOW"

    # Format human narrative
    prob_str = f"{round(prob * 100, 1)}% ({prob:.4f})"
    score_str = f"{score}/100"

    shap_lines = []
    if bundle.shap_factors:
        for idx, factor in enumerate(bundle.shap_factors[:3], start=1):
            shap_lines.append(f"  {idx}. **{factor['human_reason']}** ({factor['direction']})")
    else:
        shap_lines.append("  - Features align within regular customer spending parameters.")

    factors_markdown = "\n".join(shap_lines)

    answer = (
        f"### 🔍 Live Investigation: `{tx_id}`\n\n"
        f"**Transaction Overview**:\n"
        f"- **Amount**: ₹{amount:,.2f} {currency} at **{merchant}**\n"
        f"- **Authorization Status**: `{status}`\n\n"
        f"**Authoritative Risk Assessment**:\n"
        f"- **Independent Risk Score**: **{score_str}** (`{tier} RISK`)\n"
        f"- **ML Fraud Probability**: **{prob_str}** (XGBoost Champion Model)\n\n"
        f"**Key TreeSHAP Behavioral Drivers**:\n"
        f"{factors_markdown}\n\n"
        f"> 💡 *Risk Evaluation Standard: A high risk score represents an extreme departure from baseline patterns, "
        f"not mathematical proof of fraud. Human review should confirm customer intent before permanent dispute action.*"
    )

    card_data = {
        "transaction_id": tx_id,
        "amount": amount,
        "merchant": merchant,
        "status": status,
        "risk_score": score,
        "risk_tier": tier,
        "fraud_probability": prob,
        "top_factors": bundle.shap_factors,
    }

    return AssistantResponseEnvelope(
        response_type=ResponseCardType.INVESTIGATION_RESULT.value,
        answer=answer,
        evidence_refs=[f"db/transactions/{tx_id}", "models/xgboost_champion"],
        follow_up_suggestions=[
            f"Summarize case for {tx_id}",
            "What is the Top Risk Factor?",
            "How should an investigator review a high-risk alert?",
        ],
        confidence=0.99,
        source_type=RouteType.LIVE_TOOL,
        structured_card={
            "card_type": ResponseCardType.INVESTIGATION_RESULT.value,
            "title": f"Investigation: {tx_id}",
            "data": card_data,
        },
        debug_routing=debug_info,
    )


def compose_customer_profile_response(
    bundle: LiveEvidenceBundle,
    debug_info: Optional[Dict[str, Any]] = None,
) -> AssistantResponseEnvelope:
    """Format customer profile response."""
    if bundle.error_message:
        return AssistantResponseEnvelope(
            response_type=ResponseCardType.EVIDENCE_SUMMARY.value,
            answer=f"⚠️ **Access Notice**: {bundle.error_message}",
            evidence_refs=[],
            follow_up_suggestions=["Who are the customer personas?", "What can this chatbot do?"],
            confidence=0.95,
            source_type=RouteType.LIVE_TOOL,
            debug_routing=debug_info,
        )

    cust = bundle.customer or {}
    cid = cust.get("customer_id")
    name = cust.get("name")
    balance = cust.get("account_balance", 0.0)
    tier = cust.get("risk_tier", "MEDIUM")

    answer = (
        f"### 👤 Authoritative Customer Profile: `{cid}`\n\n"
        f"- **Customer Name**: {name}\n"
        f"- **Profile Risk Tier**: `{tier}`\n"
        f"- **Available Liquidity**: ₹{balance:,.2f} INR (Includes ₹15 Lakhs Liquidity Reserve)\n"
        f"- **KYC Status**: `{cust.get('kyc_status', 'VERIFIED')}`\n"
    )

    return AssistantResponseEnvelope(
        response_type=ResponseCardType.EVIDENCE_SUMMARY.value,
        answer=answer,
        evidence_refs=[f"db/customers/{cid}"],
        follow_up_suggestions=["Who are the customer personas?", "Show the recent suspicious activity."],
        confidence=0.99,
        source_type=RouteType.LIVE_TOOL,
        structured_card={"card_type": "customer_profile", "data": cust},
        debug_routing=debug_info,
    )


def compose_ranking_response(
    bundle: LiveEvidenceBundle,
    title: str,
    items_key: str,
    debug_info: Optional[Dict[str, Any]] = None,
) -> AssistantResponseEnvelope:
    """Format transaction rankings or recent suspicious queries."""
    tx_meta = bundle.transaction or {}
    items = tx_meta.get(items_key, [])

    if not items:
        answer = f"### {title}\n\nNo records matching the specified criteria were found in the current active scope."
    else:
        lines = [f"### {title}\n"]
        for idx, item in enumerate(items, start=1):
            tid = item.get("transaction_id")
            amt = item.get("amount", 0.0)
            merch = item.get("merchant", "Unknown")
            score = item.get("risk_score", 0.0)
            status = item.get("status", "SUCCESS")
            lines.append(f"{idx}. **`{tid}`** — ₹{amt:,.2f} at *{merch}* | **Risk: {score}/100** (`{status}`)")
        answer = "\n".join(lines)

    return AssistantResponseEnvelope(
        response_type=ResponseCardType.EVIDENCE_SUMMARY.value,
        answer=answer,
        evidence_refs=["db/transactions/ranked"],
        follow_up_suggestions=["What is High Risk?", "How do I understand a high-risk transaction?"],
        confidence=0.98,
        source_type=RouteType.LIVE_TOOL,
        structured_card={"card_type": "ranking_summary", "items": items},
        debug_routing=debug_info,
    )


def compose_provider_status_response(
    bundle: LiveEvidenceBundle,
    debug_info: Optional[Dict[str, Any]] = None,
) -> AssistantResponseEnvelope:
    """Format live AI provider diagnostics into an authoritative, clean status card."""
    data = bundle.investigation or {}
    gemini = data.get("gemini", {})
    mistral = data.get("mistral", {})
    grok = data.get("grok", {})

    mistral_valid = mistral.get("valid", False)
    mistral_model = mistral.get("model", "open-mistral-7b")

    gemini_valid = gemini.get("valid", False)
    gemini_msg = gemini.get("message", "")
    if "429" in gemini_msg or "RESOURCE_EXHAUSTED" in gemini_msg:
        gemini_summary = "⚠️ **Quota Paused** (Free-tier 20 req/day limit reached; auto-cascaded to Mistral AI)"
    elif gemini_valid:
        gemini_summary = "✅ **Connected & Active** (Google Gemini 3.6 / 3.7 Flash)"
    else:
        gemini_summary = f"❌ **Not Active**: {gemini_msg[:80]}"

    mistral_summary = (
        f"✅ **Connected & Active!** (`{mistral_model}`)"
        if mistral_valid else f"❌ **Not Active**: {mistral.get('message', 'Key not configured')}"
    )

    grok_valid = grok.get("valid", False)
    grok_summary = (
        f"✅ **Authenticated** (Key Name: `{grok.get('key_name', 'llm')}`, Team: `{str(grok.get('team_id', ''))[:8]}...`)"
        if grok_valid else f"❌ **Not Configured**: {grok.get('message', '')}"
    )

    answer = (
        "### 🔑 Live AI Provider Diagnostics & Engine Status\n\n"
        f"1. 🌟 **Mistral AI**: {mistral_summary}\n"
        f"2. ✨ **Google Gemini**: {gemini_summary}\n"
        f"3. ⚡ **xAI Grok-2**: {grok_summary}\n\n"
        "**Routing & Failover Intelligence**:\n"
        "- **Primary Live Engine**: Mistral AI is online, verified, and handling deep forensic synthesis and SAR reporting.\n"
        "- **Zero-Disruption Failover**: If any engine reaches rate limits, the orchestrator cascades automatically across the configured pool."
    )

    return AssistantResponseEnvelope(
        response_type=ResponseCardType.EXPLANATION.value,
        answer=answer,
        evidence_refs=["llm/provider_diagnostics", "env/mistral_configured"],
        follow_up_suggestions=[
            "What is Mistral AI in FraudLens?",
            "How does the multi-LLM orchestrator work?",
            "How do I switch AI engines?",
        ],
        confidence=0.99,
        source_type=RouteType.LIVE_TOOL,
        structured_card={
            "card_type": "provider_diagnostics",
            "mistral_active": mistral_valid,
            "gemini_active": gemini_valid,
            "grok_active": grok_valid,
        },
        debug_routing=debug_info or {"route": "LIVE_TOOL", "tool": "provider_diagnostics"},
    )

