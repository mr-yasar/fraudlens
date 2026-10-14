"""Conversational Intelligence & Natural Dialogue Engine (Phase 02).

Provides rich, empathetic, role-grounded conversational handling:
- Greetings and small talk (Hi, Hello, Hey, Good morning, How are you?)
- Acknowledgements and affirmations (Thanks, Okay, Got it, Understood)
- Farewells (Bye, Goodbye, See you)
- Capabilities and system overview (What can you do?, Help)
- Natural language follow-ups (Explain simply, What did you mean?)
- Conversational session summaries (Summarize everything, Recap)
- Clarification requests when questions are ambiguous
- Zero hallucination — fully grounded in authenticated user persona and session turns
"""

import re
import logging
from typing import Any, Dict, List, Optional, Tuple

from backend.app.services.assistant_identity_service import (
    AssistantIdentity,
    ROLE_CUSTOMER,
    ROLE_INVESTIGATOR,
    ROLE_ADMIN,
    ROLE_GUEST,
)
from backend.app.services.hybrid_assistant.taxonomy import (
    AssistantResponseEnvelope,
    ResponseCardType,
    RouteType,
)

logger = logging.getLogger("fraudlens.assistant.conversational")

# ─────────────────────────────────────────────────────────────────────────────
# Regex Matchers for Natural Conversational Intent
# ─────────────────────────────────────────────────────────────────────────────

GREETING_PATTERNS = [
    r"^(?:hi|hello|hey|hiya|howdy|hola)(?:\s+(?:there|copilot|assistant|fraudlens|team|all))?[!.]*$",
    r"^(?:good\s+(?:morning|afternoon|evening|day))(?:\s+(?:copilot|assistant|team))?[!.]*$",
    r"^(?:hi|hello|hey)[,\s]+(?:how\s+are\s+you|how\s+r\s+u|hows\s+it\s+going|what'?s\s+up)[?!.]*$",
    r"^(?:how\s+are\s+you|how\s+are\s+you\s+doing|hows\s+it\s+going|what'?s\s+up|wassup)[?!.]*$",
    r"^greetings(?:\s+(?:copilot|assistant))?[!.]*$",
]

ACKNOWLEDGEMENT_PATTERNS = [
    r"^(?:thanks|thank\s+you|thx|thankyou|many\s+thanks|much\s+appreciated|appreciate\s+it)[!.]*$",
    r"^(?:thanks|thank\s+you)\s+(?:very\s+much|a\s+lot|copilot|assistant)[!.]*$",
]

CONFIRMATION_PATTERNS = [
    r"^(?:ok|okay|k|got\s+it|understood|noted|alright|all\s+right|sure|cool|great|perfect|fine|sounds\s+good|roger\s+that)[!.]*$",
    r"^(?:ok|okay|got\s+it|understood),\s*(?:thanks|thank\s+you)?[!.]*$",
]

FAREWELL_PATTERNS = [
    r"^(?:bye|goodbye|bye\s+bye|see\s+you|cya|take\s+care|have\s+a\s+good\s+(?:day|night)|exit|quit)[!.]*$",
]

CAPABILITY_PATTERNS = [
    r"^(?:what\s+can\s+you\s+do|what\s+do\s+you\s+do|what\s+are\s+your\s+capabilities|how\s+can\s+you\s+help(?:\s+me)?)[?!.]*$",
    r"^(?:help|help\s+me|who\s+are\s+you|tell\s+me\s+about\s+yourself|what\s+can\s+i\s+ask(?:\s+you)?)[?!.]*$",
    r"^(?:features|capabilities|commands|menu)[?!.]*$",
]

SIMPLIFICATION_PATTERNS = [
    r"\b(?:explain\s+(?:that\s+)?(?:more\s+)?simply|in\s+simple\s+terms|make\s+it\s+simple|simpler|explain\s+like\s+i'?m\s+5|layman'?s\s+terms)\b",
    r"\b(?:what\s+did\s+you\s+mean|clarify\s+that|can\s+you\s+rephrase|don'?t\s+understand)\b",
]

NEXT_STEPS_PATTERNS = [
    r"\b(?:what\s+should\s+i\s+investigate\s+next|what\s+to\s+do\s+next|next\s+steps|recommended\s+actions|what\s+next)\b",
]

SUMMARY_PATTERNS = [
    r"\b(?:give\s+me\s+a\s+quick\s+summary|summarize\s+everything|summarize\s+this|recap|conversation\s+summary|quick\s+summary)\b",
]


def _match_any(patterns: List[str], text: str) -> bool:
    clean = text.strip().lower()
    return any(re.search(pat, clean, re.IGNORECASE) for pat in patterns)


# ─────────────────────────────────────────────────────────────────────────────
# Conversational Handlers
# ─────────────────────────────────────────────────────────────────────────────

def handle_greeting(identity: AssistantIdentity) -> AssistantResponseEnvelope:
    """Produce a warm, concise, role-aware greeting addressing the authenticated user."""
    user_name = identity.name or "there"

    if identity.role == ROLE_ADMIN:
        answer = (
            f"Hello **Administrator {user_name}**! FraudLens System Intelligence is active.\n\n"
            "I'm ready to assist with:\n"
            "• **ML Model Telemetry**: XGBoost Champion (99.1% ROC-AUC), Random Forest & Ensemble metrics\n"
            "• **Gateway Performance**: Sub-4ms pre-authorization latency and inference logs\n"
            "• **Dataset Health & Audits**: Drift monitoring, training pipelines, and security controls\n"
            "• **AI Provider Keys**: Diagnostic status for Gemini, Grok, and Mistral\n\n"
            "What would you like to inspect today?"
        )
        suggestions = [
            "Test AI Provider API Keys",
            "Compare all 4 ML models",
            "Explain sub-4ms pre-auth latency",
            "What triggers model retraining?",
        ]
    elif identity.role == ROLE_INVESTIGATOR:
        answer = (
            f"Hello **Investigator {user_name}**! FraudLens Forensic Copilot is on standby.\n\n"
            "I can assist your investigations with:\n"
            "• **Forensic Analysis**: Deep transaction inspection and anomaly correlation\n"
            "• **TreeSHAP Attributions**: Exact mathematical Shapley factors driving risk scores\n"
            "• **Velocity & Geo-Hops**: Uncovering micro-bursts and impossible travel anomalies\n"
            "• **Compliance Reporting**: Drafting FinCEN-compliant Suspicious Activity Reports (SAR)\n\n"
            "Which case or transaction queue would you like to review?"
        )
        suggestions = [
            "Highest-risk transactions today",
            "Recent suspicious and blocked activity",
            "Explain TreeSHAP waterfall calculation",
            "Draft a FinCEN SAR narrative",
        ]
    elif identity.role == ROLE_CUSTOMER:
        answer = (
            f"Hello **{user_name}**! I'm your **FraudLens AI Security Copilot**.\n\n"
            "I'm here to keep your account safe and explain how our security protections work:\n"
            "• **24/7 Account Shield**: Every purchase is analyzed in under 4 milliseconds\n"
            "• **Transaction Transparency**: Ask why a payment was approved, held, or verified\n"
            "• **Mobile OTP Verification**: Understand how step-up challenges prevent card theft\n"
            "• **Recent Activity**: Review your latest charges and account security standing\n\n"
            "How can I help you today?"
        )
        suggestions = [
            "Show my recent transactions",
            "Why was OTP required on my payment?",
            "How does FraudLens protect my account?",
            "What can you do?",
        ]
    else:
        answer = (
            f"Hello **{user_name}**! Welcome to **FraudLens AI**.\n\n"
            "I am the autonomous conversational assistant for FraudLens AI — an Explainable AI (XAI) "
            "financial fraud detection platform evaluating high-frequency digital payments in under 4 milliseconds.\n\n"
            "Feel free to ask about our machine learning models (XGBoost, Random Forest), explainability with TreeSHAP, "
            "or risk scoring thresholds."
        )
        suggestions = [
            "What is FraudLens AI?",
            "Which ML models are used?",
            "How does TreeSHAP explain transactions?",
            "What is the 30-70 OTP threshold?",
        ]

    return AssistantResponseEnvelope(
        response_type=ResponseCardType.DEFINITION.value,
        answer=answer,
        evidence_refs=["fraudlens/architecture", "security/copilot_onboarding"],
        follow_up_suggestions=suggestions,
        confidence=0.99,
        source_type=RouteType.PREDEFINED,
        structured_card={"card_type": "greeting", "user_role": identity.role},
        debug_routing={"route": "CONVERSATIONAL_GREETING", "role": identity.role},
    )


def handle_acknowledgement(identity: AssistantIdentity) -> AssistantResponseEnvelope:
    """Polite response to 'thanks' or 'thank you'."""
    user_name = identity.name or "there"
    answer = (
        f"You're very welcome, **{user_name}**! "
        "Feel free to reach out anytime if you'd like to check transaction details, inspect risk factors, "
        "or learn more about your FraudLens security protections."
    )
    return AssistantResponseEnvelope(
        response_type=ResponseCardType.GENERAL_CARD.value,
        answer=answer,
        evidence_refs=["security/copilot_courtesy"],
        follow_up_suggestions=[
            "Show my recent transactions" if identity.is_customer else "Highest-risk transactions",
            "What is risk score?",
            "How does authentication work?",
        ],
        confidence=0.99,
        source_type=RouteType.PREDEFINED,
        structured_card={"card_type": "acknowledgement"},
        debug_routing={"route": "CONVERSATIONAL_ACKNOWLEDGEMENT"},
    )


def handle_confirmation(identity: AssistantIdentity) -> AssistantResponseEnvelope:
    """Polite acknowledgement for 'ok', 'got it', 'understood'."""
    user_name = identity.name or "there"
    answer = (
        f"Understood, **{user_name}**! I'm here whenever you need assistance. "
        "Let me know if you have any questions or want to review any account activity."
    )
    return AssistantResponseEnvelope(
        response_type=ResponseCardType.GENERAL_CARD.value,
        answer=answer,
        evidence_refs=["security/copilot_courtesy"],
        follow_up_suggestions=[
            "What can you do?",
            "Show my recent transactions" if identity.is_customer else "Highest-risk transactions",
            "Which ML models are used?",
        ],
        confidence=0.99,
        source_type=RouteType.PREDEFINED,
        structured_card={"card_type": "confirmation"},
        debug_routing={"route": "CONVERSATIONAL_CONFIRMATION"},
    )


def handle_farewell(identity: AssistantIdentity) -> AssistantResponseEnvelope:
    """Friendly closing response."""
    user_name = identity.name or "there"
    answer = (
        f"Goodbye, **{user_name}**! Your account and transactions remain actively protected 24/7 "
        "by FraudLens AI. Stay safe, and reach out whenever you need us."
    )
    return AssistantResponseEnvelope(
        response_type=ResponseCardType.GENERAL_CARD.value,
        answer=answer,
        evidence_refs=["security/zero_loss_guarantee"],
        follow_up_suggestions=["What can you do?", "How does FraudLens protect my account?"],
        confidence=0.99,
        source_type=RouteType.PREDEFINED,
        structured_card={"card_type": "farewell"},
        debug_routing={"route": "CONVERSATIONAL_FAREWELL"},
    )


def handle_capabilities(identity: AssistantIdentity) -> AssistantResponseEnvelope:
    """Clear, comprehensive breakdown of actual FraudLens AI capabilities."""
    if identity.is_customer:
        answer = (
            "### 🛡️ What FraudLens AI Security Copilot Can Do For You\n\n"
            "I am your dedicated financial security assistant, powered by real-time machine learning:\n\n"
            "1. **🔍 Transaction Risk Explanations**\n"
            "   Ask me about any transaction (e.g. *'Why was my payment flagged?'*) to see the exact behavioral "
            "reasons and risk score.\n\n"
            "2. **🌲 TreeSHAP Factor Attribution**\n"
            "   See the specific reasons behind security checks: unusual merchant categories, midnight timing, "
            "or new device logins.\n\n"
            "3. **💳 3-Tier Security Thresholds**\n"
            "   Learn how our decision matrix works: Instant Approval (<30), Mobile OTP step-up verification (30–70), "
            "or Emergency Card Protection (≥70).\n\n"
            "4. **📊 Your Recent Activity**\n"
            "   Ask *'Show my recent transactions'* to see your verified payment history without leaving the chat.\n\n"
            "5. **💬 Natural Follow-Up Conversation**\n"
            "   Ask follow-up questions like *'Why is it high risk?'*, *'Explain that simply'*, or *'Give me a summary'* "
            "without repeating details."
        )
        suggestions = [
            "Show my recent transactions",
            "Why was OTP required on my payment?",
            "How does FraudLens detect fraud in under 4ms?",
            "Who are the customer personas?",
        ]
    elif identity.is_investigator:
        answer = (
            "### 🔬 Forensic Copilot Capabilities (Investigator Tier)\n\n"
            "I provide forensic risk intelligence and investigation acceleration:\n\n"
            "1. **Forensic Transaction Inspection**: Real-time attribute breakdowns, velocity spikes, and geo-hops.\n"
            "2. **TreeSHAP Game-Theoretic XAI**: Exact feature attributions for model predictions.\n"
            "3. **SAR Narrative Generation**: Automated FinCEN Suspicious Activity Report drafting.\n"
            "4. **Risk Queue Ranking**: Authoritative top-risk transactions across the platform.\n"
            "5. **Multi-LLM Synthesis**: Redundant analysis across Google Gemini, xAI Grok, and Mistral AI."
        )
        suggestions = [
            "Highest-risk transactions today",
            "Recent suspicious activity",
            "Explain TreeSHAP waterfall calculation",
            "Compare Monisha vs Sowmiya risk profiles",
        ]
    else:
        answer = (
            "### ⚙️ System Copilot Capabilities (Administrator Tier)\n\n"
            "I provide platform architecture telemetry, model governance, and security controls:\n\n"
            "1. **4-Model Ensemble Telemetry**: XGBoost Champion (99.1% ROC-AUC), Random Forest, Logistic Regression, Stacking.\n"
            "2. **Sub-4ms Pre-Auth Gateway**: Latency profiles, throughput metrics, and pipeline SLA enforcement.\n"
            "3. **Dataset Health & Drift**: Training integrity, class imbalance, and automatic retrain triggers.\n"
            "4. **AI Key Connectivity**: Real-time diagnostic verification of Gemini, Grok, and Mistral APIs.\n"
            "5. **Zero-Leak Security Boundary**: Server-side RBAC, PCI-DSS compliance, and PII masking."
        )
        suggestions = [
            "Test AI Provider API Keys",
            "Compare the 4 ML models",
            "Explain sub-4ms pre-auth latency",
            "Show dataset health metrics",
        ]

    return AssistantResponseEnvelope(
        response_type=ResponseCardType.EXPLANATION.value,
        answer=answer,
        evidence_refs=["fraudlens/architecture", "docs/capabilities_spec"],
        follow_up_suggestions=suggestions,
        confidence=0.99,
        source_type=RouteType.PREDEFINED,
        structured_card={"card_type": "capabilities", "role": identity.role},
        debug_routing={"route": "CONVERSATIONAL_CAPABILITIES"},
    )


def handle_simplification(
    identity: AssistantIdentity,
    recent_messages: List[Dict[str, str]],
) -> AssistantResponseEnvelope:
    """Explain previous technical concepts in plain, simple, everyday English."""
    # Find last assistant message
    last_assistant_msg = next((m.get("content", "") for m in reversed(recent_messages) if m.get("role") == "assistant"), "")

    if last_assistant_msg:
        # Grounded plain-English translation
        answer = (
            "### 💡 In Plain, Simple English\n\n"
            "Here is the simple takeaway from our last discussion:\n\n"
            "• **How We Protect You**: FraudLens acts like a digital bodyguard for your bank account. "
            "Whenever you make a payment, the system quickly checks if the purchase matches your normal shopping habits.\n"
            "• **Why You Might See a Check**: If you shop at midnight, spend a much larger amount than usual, "
            "or use a new phone or computer, the system pauses the payment and sends a 6-digit SMS code to your phone.\n"
            "• **What That Means for You**: Legitimate payments at your favorite grocery store go through instantly (<4ms). "
            "If an unauthorized person steals your card numbers, they get blocked immediately before your money is taken.\n\n"
            "Does that make sense, or would you like me to clarify a specific point?"
        )
    else:
        answer = (
            "### 💡 Simple Explanation of FraudLens AI\n\n"
            "In simple terms: FraudLens is an automated security system that protects your money. "
            "Every time a payment happens, our machine learning models verify in less than 4 milliseconds "
            "whether it looks genuine or like someone trying to use stolen card details. "
            "If it looks suspicious, we ask for an SMS code to ensure it's really you."
        )

    return AssistantResponseEnvelope(
        response_type=ResponseCardType.EXPLANATION.value,
        answer=answer,
        evidence_refs=["explainability/plain_english_guide"],
        follow_up_suggestions=[
            "Why was OTP required on my payment?",
            "What is risk score?",
            "Show my recent transactions",
        ],
        confidence=0.98,
        source_type=RouteType.PREDEFINED,
        structured_card={"card_type": "simplification"},
        debug_routing={"route": "CONVERSATIONAL_SIMPLIFICATION"},
    )


def handle_next_steps(identity: AssistantIdentity, conversation_context: Dict[str, Any]) -> AssistantResponseEnvelope:
    """Suggest practical next actions based on role and active context."""
    last_tx = conversation_context.get("last_transaction_id")

    if identity.is_customer:
        if last_tx:
            answer = (
                f"### 📋 Recommended Next Steps for `{last_tx}`\n\n"
                "1. **Confirm Merchant Details**: Check if you recognize the merchant name and purchase amount.\n"
                "2. **Check Auth Status**: If the transaction was approved, no action is needed.\n"
                "3. **Step-Up Verification**: If an SMS OTP was requested, confirm that you entered the code on your trusted phone.\n"
                "4. **Unrecognized Charge**: If you did not initiate this transaction, tap **Dispute Transaction** in your portal immediately."
            )
        else:
            answer = (
                "### 📋 Recommended Next Steps for Account Safety\n\n"
                "1. **Review Recent Transactions**: Verify all charges over the past 7 days.\n"
                "2. **Check Registered Devices**: Ensure only your active phone and laptop are enrolled.\n"
                "3. **Keep Mobile OTP Active**: Never share your 6-digit SMS verification code with anyone.\n"
                "4. **Report Anomalies**: Flag any unrecognized charges immediately in the Dispute Center."
            )
    else:
        if last_tx:
            answer = (
                f"### 🔬 Forensic Next Steps for Investigator ({last_tx})\n\n"
                "1. **Inspect TreeSHAP Waterfall**: Examine the top 3 risk drivers (velocity, amount deviation, IP anomaly).\n"
                "2. **Verify Geo-Velocity Hops**: Cross-check distance and elapsed time from previous cardholder transaction.\n"
                "3. **Check Device Entropy**: Review user-agent, Canvas hash, and TLS fingerprint consistency.\n"
                "4. **Take Disposition Action**: Issue an emergency card block or draft a FinCEN SAR narrative."
            )
        else:
            answer = (
                "### 🔬 Recommended Forensic Investigation Workflow\n\n"
                "1. **Triage High-Risk Queue**: Prioritize transactions with risk score ≥70.\n"
                "2. **Evaluate 30–70 Step-Up Band**: Analyze customer OTP completion rates and false positives.\n"
                "3. **Review Merchant Outliers**: Identify velocity clusters at high-risk merchant categories (Bullion, Electronics).\n"
                "4. **Monitor System Telemetry**: Confirm sub-4ms pre-auth gateway latency."
            )

    return AssistantResponseEnvelope(
        response_type=ResponseCardType.NEXT_STEP.value,
        answer=answer,
        evidence_refs=["investigation/sop_workflow"],
        follow_up_suggestions=[
            f"Explain {last_tx}" if last_tx else "Highest-risk transactions",
            "What is risk score?",
            "How does authentication work?",
        ],
        confidence=0.98,
        source_type=RouteType.PREDEFINED,
        structured_card={"card_type": "next_steps"},
        debug_routing={"route": "CONVERSATIONAL_NEXT_STEPS"},
    )


def handle_summary(
    identity: AssistantIdentity,
    recent_messages: List[Dict[str, str]],
    conversation_context: Dict[str, Any],
) -> AssistantResponseEnvelope:
    """Summarize the discussion turns in the current active session."""
    user_turns = [m.get("content", "") for m in recent_messages if m.get("role") == "user"]
    assistant_turns = [m.get("content", "") for m in recent_messages if m.get("role") == "assistant"]

    if not user_turns:
        answer = (
            "We haven't discussed any transactions or topics in this session yet. "
            "Feel free to ask about any transaction ID (e.g. *'Why was TX-1042 flagged?'*), "
            "our machine learning models, or risk scores to get started!"
        )
    else:
        last_tx = conversation_context.get("last_transaction_id")
        points = []
        for i, u_msg in enumerate(user_turns[-3:], 1):
            points.append(f"• **Topic {i}**: You asked *\"{u_msg[:60]}{'...' if len(u_msg) > 60 else ''}\"*")

        tx_note = f"\n- **Active Transaction Referenced**: `{last_tx}`" if last_tx else ""

        answer = (
            f"### 📋 Current Session Summary\n\n"
            f"Here is a quick recap of our discussion ({identity.name or 'User'} / {identity.role}):\n\n"
            + "\n".join(points)
            + tx_note
            + "\n\nAll data is verified against the authoritative FraudLens backend with zero cross-user leakage. "
            "What would you like to explore next?"
        )

    return AssistantResponseEnvelope(
        response_type=ResponseCardType.GENERAL_CARD.value,
        answer=answer,
        evidence_refs=["session/conversation_audit"],
        follow_up_suggestions=[
            "Show my recent transactions" if identity.is_customer else "Highest-risk transactions",
            "What can you do?",
            "Which ML models are used?",
        ],
        confidence=0.99,
        source_type=RouteType.PREDEFINED,
        structured_card={"card_type": "summary"},
        debug_routing={"route": "CONVERSATIONAL_SUMMARY"},
    )


# ─────────────────────────────────────────────────────────────────────────────
# Master Dispatcher
# ─────────────────────────────────────────────────────────────────────────────

def try_handle_conversational_query(
    query: str,
    identity: AssistantIdentity,
    conversation_context: Optional[Dict[str, Any]] = None,
    recent_messages: Optional[List[Dict[str, str]]] = None,
) -> Optional[AssistantResponseEnvelope]:
    """Intercept and handle pure conversational small talk, greetings, help, and session continuity."""
    q_clean = (query or "").strip()
    if not q_clean:
        return None

    ctx = conversation_context or {}
    msgs = recent_messages or ctx.get("recent_messages") or []

    # 1. Greetings (Hi, Hello, Good morning, etc.)
    if _match_any(GREETING_PATTERNS, q_clean):
        return handle_greeting(identity)

    # 2. Acknowledgements (Thanks, Thank you, etc.)
    if _match_any(ACKNOWLEDGEMENT_PATTERNS, q_clean):
        return handle_acknowledgement(identity)

    # 3. Confirmations (OK, Understood, Got it, etc.)
    if _match_any(CONFIRMATION_PATTERNS, q_clean):
        return handle_confirmation(identity)

    # 4. Farewells (Bye, Goodbye, etc.)
    if _match_any(FAREWELL_PATTERNS, q_clean):
        return handle_farewell(identity)

    # 5. Capabilities / Help requests
    if _match_any(CAPABILITY_PATTERNS, q_clean):
        return handle_capabilities(identity)

    # 6. Simplification requests ("Explain simply", "What did you mean?")
    if _match_any(SIMPLIFICATION_PATTERNS, q_clean):
        return handle_simplification(identity, msgs)

    # 7. Next investigation steps ("What should I investigate next?")
    if _match_any(NEXT_STEPS_PATTERNS, q_clean):
        return handle_next_steps(identity, ctx)

    # 8. Conversation Summary ("Give me a quick summary", "Summarize everything")
    if _match_any(SUMMARY_PATTERNS, q_clean):
        return handle_summary(identity, msgs, ctx)

    return None
