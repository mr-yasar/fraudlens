"""LLM Gateway Service — Real Gemini + Grok API integration with smart fallback.

This service routes AI chat/explanation requests to:
1. Google Gemini 2.0 Flash (via google-generativeai SDK)
2. xAI Grok-2 (via OpenAI-compatible API at https://api.x.ai/v1)
3. Intelligent template fallback (when no API key is configured)

Configure in .env:
    GEMINI_API_KEY=your-google-ai-studio-key
    GROK_API_KEY=your-xai-api-key
    DEFAULT_LLM_PROVIDER=gemini   # or grok
"""

import os
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Environment
# ─────────────────────────────────────────────────────────────────────────────
GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
GROK_API_KEY: str = os.getenv("GROK_API_KEY", "")
DEFAULT_PROVIDER: str = os.getenv("DEFAULT_LLM_PROVIDER", "gemini").lower()

# ─────────────────────────────────────────────────────────────────────────────
# System Prompt – makes both models behave as FraudLens domain experts
# ─────────────────────────────────────────────────────────────────────────────
FRAUDLENS_SYSTEM_PROMPT = """You are FraudLens AI Assistant — an expert in financial fraud detection,
explainable AI (XAI), TreeSHAP game-theoretic Shapley values, digital payment systems (UPI, IMPS,
card-not-present), and enterprise risk management.

FraudLens context:
- 4 active AI models: XGBoost (Champion), Random Forest, Logistic Regression, Ensemble Stacking
- TreeSHAP provides mathematical attribution for every transaction decision
- 29 canonical merchants across 10 retail categories
- 3 customer personas: Monisha (3% fraud rate), Mohana (12%), Sowmiya (26%)
- Real-time pre-authorization gateway with <4ms latency
- Mobile OTP step-up for medium-risk transactions (30–70 score)

Answer questions clearly and helpfully. For non-fraud/finance topics, still be helpful but gently
guide back to fraud detection concepts. Keep responses concise (max 4 paragraphs) unless the user
asks for detailed explanations. Use simple language for customers, technical depth for investigators.
Format bullet lists neatly. Do NOT use markdown headers (# ## ###) in your response."""


# ─────────────────────────────────────────────────────────────────────────────
# Gemini
# ─────────────────────────────────────────────────────────────────────────────
def _call_gemini(messages: List[Dict], temperature: float = 0.7) -> str:
    """Call Google Gemini 2.0 Flash API."""
    try:
        import google.generativeai as genai  # type: ignore

        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel(
            model_name="gemini-2.0-flash-exp",
            system_instruction=FRAUDLENS_SYSTEM_PROMPT,
        )

        # Convert to Gemini chat history format
        history = []
        last_user_msg = ""
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "user":
                if history or not last_user_msg:
                    last_user_msg = content
                history.append({"role": "user", "parts": [content]})
            elif role == "assistant":
                history.append({"role": "model", "parts": [content]})

        # Remove last user message from history (send it as the prompt)
        if history and history[-1]["role"] == "user":
            history = history[:-1]

        chat = model.start_chat(history=history)
        response = chat.send_message(
            last_user_msg,
            generation_config=genai.types.GenerationConfig(
                temperature=temperature,
                max_output_tokens=1024,
            ),
        )
        return response.text.strip()
    except ImportError:
        raise RuntimeError("google-generativeai not installed. Run: pip install google-generativeai")
    except Exception as exc:
        logger.error("Gemini API error: %s", exc)
        raise


# ─────────────────────────────────────────────────────────────────────────────
# Grok (xAI — OpenAI-compatible endpoint)
# ─────────────────────────────────────────────────────────────────────────────
def _call_grok(messages: List[Dict], temperature: float = 0.7) -> str:
    """Call xAI Grok-2 via OpenAI-compatible REST API."""
    try:
        from openai import OpenAI  # type: ignore

        client = OpenAI(
            api_key=GROK_API_KEY,
            base_url="https://api.x.ai/v1",
        )

        # Prepend system message
        full_messages = [{"role": "system", "content": FRAUDLENS_SYSTEM_PROMPT}] + messages

        completion = client.chat.completions.create(
            model="grok-2-1212",
            messages=full_messages,  # type: ignore[arg-type]
            temperature=temperature,
            max_tokens=1024,
        )
        return completion.choices[0].message.content.strip()
    except ImportError:
        raise RuntimeError("openai package not installed. Run: pip install openai")
    except Exception as exc:
        logger.error("Grok API error: %s", exc)
        raise


# ─────────────────────────────────────────────────────────────────────────────
# Smart Fallback (template-based, zero external dependency)
# ─────────────────────────────────────────────────────────────────────────────
_FALLBACK_KB: Dict[str, str] = {
    "fraud": (
        "Financial fraud is the deliberate, unauthorized diversion of money or credentials through deception. "
        "In UPI and card payment systems it happens in milliseconds via Account Takeover (ATO), Card-Not-Present (CNP) theft, "
        "velocity bursts, or geo-location jumps. FraudLens AI intercepts suspicious payments before funds are committed, "
        "typically in under 4ms, using 4 ML models and TreeSHAP mathematical explainability."
    ),
    "shap": (
        "SHAP (SHapley Additive exPlanations) uses cooperative game theory to fairly distribute the 'credit' of a model's "
        "prediction across input features. For each transaction, TreeSHAP computes exact Shapley values — positive values push "
        "fraud probability up (red bars) while negative values lower it (green bars). The sum of all SHAP values plus the base "
        "expected value equals the model's raw output, making every decision fully auditable."
    ),
    "model": (
        "FraudLens runs 4 AI models simultaneously: (1) XGBoost — gradient-boosted decision trees, the champion model with 99.1% ROC-AUC. "
        "(2) Random Forest — 100-tree bagging ensemble for variance reduction. (3) Logistic Regression — calibrated linear model for interpretability. "
        "(4) Ensemble Stacking — meta-learner fusing all three for maximum accuracy. All use TreeSHAP for per-transaction attribution."
    ),
    "risk": (
        "The composite risk score (0–100) combines: ML fraud probability, behavioral velocity deviation, device trust score, "
        "geo-location anomaly, Isolation Forest unsupervised anomaly detection, and rule engine signals. "
        "Score < 30: auto-approved. 30–70: Mobile OTP step-up challenge. ≥70: immediate block."
    ),
    "otp": (
        "Mobile OTP Step-Up is the adaptive friction layer. When risk score falls between 30 and 70, FraudLens sends a "
        "6-digit OTP to the customer's verified mobile number. The transaction is held in a protected state until the customer "
        "confirms the code. Fraud actors cannot complete the transfer without physically possessing the customer's phone."
    ),
    "customer": (
        "FraudLens tests against 3 real customer personas: Monisha (3% fraud rate — routine shopper at NovaMart Fresh, trusted iOS device), "
        "Mohana (12% fraud rate — velocity spikes at electronics merchants triggering OTP step-up), and "
        "Sowmiya (26% fraud rate — actively targeted by botnets attempting midnight gold bullion purchases, hard-blocked by AI)."
    ),
    "merchant": (
        "FraudLens has 29 canonical merchants across 10 categories: Grocery & Supermarkets, Electronics & Gadgets, "
        "Fashion & Apparel, Pharmaceuticals & Health, Jewellery & Bullion, Digital Goods & Subscriptions, "
        "Food Delivery & QSR, Travel & Transport, Healthcare & Wellness, and Financial Services & Wallets. "
        "Each merchant has an independently calibrated behavioral baseline."
    ),
}


def _fallback_response(query: str) -> str:
    """Intelligent keyword-matching fallback when no API key is configured."""
    q_lower = query.lower()

    # Find best matching knowledge base entry
    best_key = None
    best_score = 0
    keyword_map = {
        "fraud": ["fraud", "scam", "theft", "steal", "hack"],
        "shap": ["shap", "shapley", "treeshap", "explai", "xai", "attribution", "feature"],
        "model": ["model", "xgboost", "random forest", "logistic", "ensemble", "ml", "ai", "machine learning"],
        "risk": ["risk", "score", "probability", "danger", "alert", "block"],
        "otp": ["otp", "mobile", "phone", "verification", "step-up", "sms", "code"],
        "customer": ["customer", "monisha", "mohana", "sowmiya", "persona", "user"],
        "merchant": ["merchant", "shop", "store", "novamart", "retailer", "mcc"],
    }

    for key, keywords in keyword_map.items():
        score = sum(1 for kw in keywords if kw in q_lower)
        if score > best_score:
            best_score = score
            best_key = key

    if best_key and best_score > 0:
        base = _FALLBACK_KB[best_key]
    else:
        base = (
            "FraudLens AI is a real-time explainable fraud detection platform. It evaluates every transaction "
            "using 4 ML models (XGBoost, Random Forest, Logistic Regression, Ensemble Stacking) and TreeSHAP "
            "game-theoretic Shapley values for mathematical transparency. Ask me about fraud types, SHAP explanations, "
            "risk scoring, OTP verification, AI models, customer personas, or merchant baselines!"
        )

    return (
        f"[FraudLens AI Assistant — Smart Mode]\n\n{base}\n\n"
        f"💡 Tip: Configure GEMINI_API_KEY or GROK_API_KEY in your .env file to unlock full conversational AI "
        f"with real-time fraud analysis powered by Google Gemini or xAI Grok."
    )


# ─────────────────────────────────────────────────────────────────────────────
# Public Gateway
# ─────────────────────────────────────────────────────────────────────────────
def chat_with_llm(
    messages: List[Dict],
    provider: Optional[str] = None,
    temperature: float = 0.7,
) -> Dict[str, Any]:
    """
    Route a chat conversation to the best available LLM.

    Args:
        messages: List of {"role": "user"|"assistant", "content": str}
        provider: "gemini" | "grok" | None (auto-select)
        temperature: Sampling temperature (0.0–1.0)

    Returns:
        {"response": str, "provider": str, "model": str, "used_real_api": bool}
    """
    chosen = (provider or DEFAULT_PROVIDER).lower().strip()

    # Auto-select: prefer gemini, fallback to grok, then template
    if not GEMINI_API_KEY and not GROK_API_KEY:
        query = next((m["content"] for m in reversed(messages) if m.get("role") == "user"), "")
        return {
            "response": _fallback_response(query),
            "provider": "FraudLens Smart Fallback",
            "model": "template-engine-v1",
            "used_real_api": False,
        }

    # Try requested or default provider
    attempts = []
    if chosen == "grok" and GROK_API_KEY:
        attempts = [("grok", _call_grok)]
        if GEMINI_API_KEY:
            attempts.append(("gemini", _call_gemini))
    else:
        if GEMINI_API_KEY:
            attempts = [("gemini", _call_gemini)]
        if GROK_API_KEY:
            attempts.append(("grok", _call_grok))

    provider_labels = {
        "gemini": ("Google Gemini 2.0 Flash", "gemini-2.0-flash-exp"),
        "grok": ("xAI Grok-2 Enterprise", "grok-2-1212"),
    }

    last_error: Exception = RuntimeError("No LLM provider available")
    for prov_key, call_fn in attempts:
        try:
            text = call_fn(messages, temperature)
            label, model_id = provider_labels.get(prov_key, (prov_key, prov_key))
            return {
                "response": text,
                "provider": label,
                "model": model_id,
                "used_real_api": True,
            }
        except Exception as exc:
            logger.warning("Provider %s failed: %s — trying next…", prov_key, exc)
            last_error = exc

    # All real providers failed — use fallback
    query = next((m["content"] for m in reversed(messages) if m.get("role") == "user"), "")
    logger.error("All LLM providers failed (%s), using fallback.", last_error)
    return {
        "response": _fallback_response(query),
        "provider": "FraudLens Smart Fallback",
        "model": "template-engine-v1",
        "used_real_api": False,
    }


def is_gemini_configured() -> bool:
    return bool(GEMINI_API_KEY)


def is_grok_configured() -> bool:
    return bool(GROK_API_KEY)


def get_available_providers() -> List[Dict[str, Any]]:
    """Return list of configured providers for the frontend status display."""
    providers = []
    if GEMINI_API_KEY:
        providers.append({
            "id": "gemini",
            "name": "Google Gemini 2.0 Flash",
            "model": "gemini-2.0-flash-exp",
            "status": "configured",
            "icon": "✨",
        })
    if GROK_API_KEY:
        providers.append({
            "id": "grok",
            "name": "xAI Grok-2 Enterprise",
            "model": "grok-2-1212",
            "status": "configured",
            "icon": "⚡",
        })
    if not providers:
        providers.append({
            "id": "fallback",
            "name": "FraudLens Smart AI",
            "model": "template-engine-v1",
            "status": "fallback",
            "icon": "🛡️",
        })
    return providers
