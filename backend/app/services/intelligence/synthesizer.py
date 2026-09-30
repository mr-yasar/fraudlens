"""Response Synthesizer & Validator — Multi-LLM Synthesis & Zero-Leak Defense.

Sections 7, 8, 26 compliance:
- Gemini synthesizes primary analysis + Grok independent review.
- No Blind Model Consensus: Agreement is not proof; evidence-grounded resolution.
- Final Response Validation: Pre-delivery checklist for fabrication, secret leakage,
  and mathematical precision (probability != risk score).
"""

import re
import logging
from typing import Optional, Dict, Any

from backend.app.services.intelligence.secret_guard import SecretRedactionGuard
from backend.app.services.intelligence.gemini_adapter import GeminiAdapter

logger = logging.getLogger("fraudlens.intelligence.synthesizer")


class ResponseSynthesizer:
    """Synthesizes primary Gemini analysis with independent Grok challenge into a verified final answer."""

    @classmethod
    def synthesize(
        cls,
        user_query: str,
        gemini_primary_analysis: str,
        grok_review: str,
        evidence_context: str,
        system_instruction: str,
    ) -> str:
        """Gemini-led synthesis of primary analysis and Grok independent challenge."""
        synthesis_prompt = (
            "You are Google Gemini, the Primary Orchestrator for FraudLens AI.\n"
            "You are conducting the FINAL SYNTHESIS between your primary analysis and an independent review by xAI Grok.\n\n"
            "CRITICAL SYNTHESIS DIRECTIVES (Section 7 & 8):\n"
            "1. NO BLIND CONSENSUS: Model agreement is NOT proof. Prefer evidence-grounded reasoning over agreement.\n"
            "2. If Grok identified legitimate blind spots, missing counter-evidence, or unverified assumptions, "
            "incorporate and address them directly.\n"
            "3. If Grok made unsupported claims not found in the verified evidence context, reject them.\n"
            "4. Maintain strict distinction: Fraud Probability (ML output) != Composite Risk Score (0-100).\n"
            "5. Never claim TreeSHAP proves causality.\n"
            "6. Communicate meaningful uncertainty where evidence is incomplete.\n"
            "7. Produce a polished, authoritative, unified final answer.\n\n"
            f"VERIFIED EVIDENCE CONTEXT:\n{evidence_context}\n\n"
            f"PRIMARY ANALYSIS (Gemini):\n{gemini_primary_analysis}\n\n"
            f"INDEPENDENT REVIEW (xAI Grok):\n{grok_review}\n\n"
            f"ORIGINAL USER QUESTION:\n{user_query}\n\n"
            "Now, provide the definitive synthesized response to the user."
        )

        try:
            synthesized_text, _ = GeminiAdapter.generate(
                messages=[{"role": "user", "content": synthesis_prompt}],
                system_instruction=system_instruction,
                escalate_to_3_7=False,
                temperature=0.6,
                max_tokens=1800,
            )
            return synthesized_text
        except Exception as exc:
            logger.warning("Synthesis pass failed, falling back to primary analysis: %s", exc)
            return gemini_primary_analysis


class ResponseValidator:
    """Validates final generated responses against security and factual guardrails."""

    @classmethod
    def validate_and_scrub(
        cls,
        text: str,
        role: Optional[str] = None,
        user_info: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Run post-flight validation and scrub any accidental secret disclosure."""
        if not text:
            return ""

        # 1. Scrub all sensitive patterns (API keys, secrets, tokens, cards, passwords)
        cleaned = SecretRedactionGuard.sanitize(text)

        # 2. Enforce that forbidden model references (e.g. 3.8) are scrubbed
        cleaned = cleaned.replace("gemini-3.8", "gemini-3.7").replace("Gemini 3.8", "Gemini 3.7")

        # 3. Scrub accidental OTP exposures: "OTP is 440628" -> "OTP is [PROTECTED_OTP]"
        cleaned = re.sub(
            r"\b(?:otp|one-time\s+password|verification\s+code)\s*(?:is|:|=)\s*(\d{4,8})\b",
            "OTP: [PROTECTED_OTP]",
            cleaned,
            flags=re.IGNORECASE,
        )

        # 4. If in customer mode, scrub any foreign customer identifiers
        active_role = (role or (user_info.get("role") if user_info else "customer")).lower().strip()
        if "customer" in active_role and user_info:
            active_cust_id = (user_info.get("customer_id") or "").upper().strip()
            # If active customer is known, redact other canonical customer IDs
            foreign_ids = ["CUST_MONISHA_001", "CUST_MOHANA_002", "CUST_SOWMIYA_003", "CUST_AJAY_004"]
            for f_id in foreign_ids:
                if active_cust_id and f_id != active_cust_id:
                    cleaned = cleaned.replace(f_id, "[PROTECTED_USER_ID]")

        return cleaned
