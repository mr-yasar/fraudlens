"""Grok (xAI) Adapter — Complementary Intelligence & Independent Reviewer.

Sections 6, 7, 8 compliance:
- Specialized task routing: Independent review, challenging assumptions, alternative reasoning.
- Never called automatically for every question — used when there is real intelligence benefit.
- No blind consensus: Agreement is not proof.
"""

import os
import logging
from typing import Any, Dict, List, Optional, Tuple

from backend.app.services.intelligence.secret_guard import SecretRedactionGuard

logger = logging.getLogger("fraudlens.intelligence.grok_adapter")

GROK_MODELS = ["grok-2-1212", "grok-2", "grok-beta"]


class GrokAdapter:
    """Interface to xAI Grok API for independent analysis and adversarial challenges."""

    @classmethod
    def get_api_key(cls) -> str:
        key = os.getenv("GROK_API_KEY", "").strip() or os.getenv("XAI_API_KEY", "").strip()
        if not key:
            try:
                from backend.app.core.config import settings
                key = (settings.GROK_API_KEY or "").strip()
            except Exception:
                pass
        if key and key != "your_grok_api_key_here":
            return key
        return ""

    @classmethod
    def is_configured(cls) -> bool:
        return bool(cls.get_api_key())

    @classmethod
    def generate(
        cls,
        messages: List[Dict[str, str]],
        system_instruction: str,
        temperature: float = 0.7,
        max_tokens: int = 1800,
    ) -> Tuple[str, str]:
        """Call xAI Grok API for completions."""
        api_key = cls.get_api_key()
        if not api_key:
            raise ValueError("GROK_API_KEY is not configured in .env")

        try:
            from openai import OpenAI

            client = OpenAI(
                api_key=api_key,
                base_url="https://api.x.ai/v1",
                timeout=25.0,
            )

            # Build full message payload
            full_messages = [{"role": "system", "content": system_instruction}]
            for m in messages:
                m_role = m.get("role", "user")
                c = m.get("content", "").strip()
                if not c:
                    continue
                full_messages.append({"role": "user" if m_role == "user" else "assistant", "content": c})

            last_error = None
            for model_name in GROK_MODELS:
                try:
                    completion = client.chat.completions.create(
                        model=model_name,
                        messages=full_messages,  # type: ignore[arg-type]
                        temperature=temperature,
                        max_tokens=max_tokens,
                    )
                    text = completion.choices[0].message.content or ""
                    clean_text = SecretRedactionGuard.sanitize(text.strip())
                    return clean_text, model_name
                except Exception as exc:
                    last_error = exc
                    err_lower = str(exc).lower()
                    if "credits" in err_lower or "spending limit" in err_lower or "403" in err_lower:
                        logger.warning("xAI Grok account quota/credit balance exhausted: %s", exc)
                        raise exc
                    continue

            raise last_error or RuntimeError("All xAI Grok models failed.")

        except ImportError:
            raise RuntimeError("openai package not installed.")

    @classmethod
    def review_and_challenge(
        cls,
        user_query: str,
        primary_analysis: str,
        evidence_context: str,
    ) -> Tuple[Optional[str], Optional[str]]:
        """Specialized independent review: Challenges assumptions and detects potential blind spots."""
        review_system = (
            "You are xAI Grok-2 acting as the Independent Adversarial Reviewer for FraudLens AI.\n"
            "Your objective is to provide a rigorous, independent challenge to the primary analysis.\n\n"
            "MANDATORY REVIEW RULES (Section 7 & 8):\n"
            "1. Challenge assumptions: Identify if the analysis assumed fraud without sufficient proof.\n"
            "2. Distinguish statistical probability from facts: Ensure ML fraud probability is not treated as guaranteed guilt.\n"
            "3. Enforce SHAP boundaries: Ensure TreeSHAP feature attributions are not claimed to 'prove causality'.\n"
            "4. Verify distinction: Fraud probability (0-1) != Risk score (0-100).\n"
            "5. Detect counter-evidence: Note habitual patterns (e.g. trusted iOS device, regular merchant).\n"
            "6. Keep your challenge concise, rigorous, and evidence-grounded.\n\n"
            f"VERIFIED EVIDENCE CONTEXT:\n{evidence_context}"
        )

        review_prompt = (
            f"USER QUERY:\n{user_query}\n\n"
            f"PRIMARY ANALYSIS TO REVIEW:\n{primary_analysis}\n\n"
            "Please provide your independent review, identifying any potential blind spots, unsupported assumptions, "
            "or alternative interpretations grounded strictly in project evidence."
        )

        try:
            return cls.generate(
                messages=[{"role": "user", "content": review_prompt}],
                system_instruction=review_system,
                temperature=0.5,
                max_tokens=900,
            )
        except Exception as exc:
            logger.warning("Grok review could not be completed: %s", exc)
            return None, None
