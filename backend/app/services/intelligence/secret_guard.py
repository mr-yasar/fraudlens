"""Secret Redaction Guard — Critical Security & Zero-Leak Information Disclosure Defense.

Sections 22, 23, 24, 25, 26, 31 compliance:
- ABSOLUTE NON-NEGOTIABLE RULE: Never reveal, expose, or summarize API keys, bearer tokens,
  passwords, hidden system prompts, private routing instructions, internal reasoning traces,
  or infrastructure credentials under any circumstance.
- Pre-flight interceptor detects attempts to extract secrets or hidden prompts.
- Post-flight response sanitizer scrubs any accidental key or credential patterns.
"""

import os
import re
import logging
from typing import Optional, Tuple

logger = logging.getLogger("fraudlens.intelligence.secret_guard")

SAFE_SECRET_REFUSAL = (
    "I can explain FraudLens AI detection architecture, machine learning models, and fraud risk "
    "concepts, but internal API credentials, hidden instructions, and system secrets are strictly "
    "protected under financial cybersecurity policies."
)

SAFE_PROMPT_REFUSAL = (
    "I can explain FraudLens AI assistant capabilities, fraud detection workflows, and TreeSHAP "
    "explainability, but internal system instructions and private orchestration prompts are protected."
)

SAFE_AUTH_REFUSAL = (
    "Sensitive authentication headers, internal request payloads, and security credentials are protected "
    "and cannot be disclosed."
)

# Common extraction trigger patterns
SECRET_EXTRACTION_PATTERNS = [
    r"\b(?:show|give|tell|print|reveal|display|output|leak|share|dump|read|get)\b.*?\b(?:api[_\s-]?key|secret[_\s-]?key|gemini[_\s-]?key|grok[_\s-]?key|xai[_\s-]?key|token|bearer|password|credential|env|environ|\.env)\b",
    r"\b(?:what\s+is|what's)\s+(?:the\s+)?(?:gemini|grok|xai|backend|system|api|secret)\s+(?:api[_\s-]?key|key|token|secret|password)\b",
    r"\b(?:api[_\s-]?key|secret[_\s-]?key)\s*(?:=|:|\?)\b",
    r"\b(?:export|printenv|cat\s+\.env|type\s+\.env)\b",
]

PROMPT_EXTRACTION_PATTERNS = [
    r"\b(?:show|give|tell|print|reveal|display|output|repeat|quote|dump)\b.*?\b(?:hidden\s+prompt|system\s+prompt|developer\s+instruction|system\s+instructions?|initial\s+prompt|secret\s+prompt|base\s+prompt|routing\s+prompt)\b",
    r"\b(?:what\s+are\s+your|what\s+is\s+your)\s+(?:system\s+instructions?|system\s+prompt|initial\s+prompt|hidden\s+instructions?)\b",
    r"\b(?:ignore\s+all\s+previous\s+instructions\s+and\s+show|repeat\s+everything\s+above)\b",
    r"\bprint\s+(?:your\s+|the\s+)?system\s+instructions?\b",
]

AUTH_HEADER_PATTERNS = [
    r"\b(?:show|reveal|print|display)\b.*?\b(?:headers?|authorization|auth\s+header|bearer\s+token\s+headers?|jwt|raw\s+request)\b",
]


class SecretRedactionGuard:
    """Enterprise-grade security gatekeeper enforcing zero-leak boundaries."""

    @classmethod
    def check_preflight_leak_attempt(cls, query: str) -> Tuple[bool, Optional[str]]:
        """Inspect user query for unauthorized secret or prompt extraction attempts.
        
        Returns (is_attempt, safe_refusal_message).
        """
        if not query:
            return False, None

        q_clean = query.lower().strip()

        # Check auth header extraction first (specific to headers)
        for pat in AUTH_HEADER_PATTERNS:
            if re.search(pat, q_clean, re.IGNORECASE):
                logger.warning("Intercepted auth/header extraction attempt: %s", query[:60])
                return True, SAFE_AUTH_REFUSAL

        # Check prompt extraction
        for pat in PROMPT_EXTRACTION_PATTERNS:
            if re.search(pat, q_clean, re.IGNORECASE):
                logger.warning("Intercepted prompt extraction attempt: %s", query[:60])
                return True, SAFE_PROMPT_REFUSAL

        # Check secret / API key extraction
        for pat in SECRET_EXTRACTION_PATTERNS:
            if re.search(pat, q_clean, re.IGNORECASE):
                logger.warning("Intercepted API key/secret extraction attempt: %s", query[:60])
                return True, SAFE_SECRET_REFUSAL

        return False, None

    @classmethod
    def sanitize(cls, text: str) -> str:
        """Post-flight scrubber: Remove any accidental keys, tokens, or credentials from output."""
        if not text:
            return ""

        sanitized = text

        # 1. Scrub actual loaded environment secrets
        loaded_secrets = [
            os.getenv("GEMINI_API_KEY", "").strip(),
            os.getenv("GROK_API_KEY", "").strip(),
            os.getenv("XAI_API_KEY", "").strip(),
            os.getenv("MISTRAL_API_KEY", "").strip(),
            os.getenv("SECRET_KEY", "").strip(),
            os.getenv("DATABASE_URL", "").strip(),
        ]
        for sec in loaded_secrets:
            if sec and len(sec) >= 8:
                sanitized = sanitized.replace(sec, "[PROTECTED_CREDENTIAL]")

        # 2. Regex scrubber for standard API key formats
        # Gemini / Google API keys: AIza... or AQ....
        sanitized = re.sub(r"\bAIza[0-9A-Za-z_-]{35}\b", "[PROTECTED_API_KEY]", sanitized)
        sanitized = re.sub(r"\bAQ\.[a-zA-Z0-9_-]{30,}\b", "[PROTECTED_API_KEY]", sanitized)

        # xAI / Grok keys: xai-...
        sanitized = re.sub(r"\bxai-[a-zA-Z0-9_-]{40,}\b", "[PROTECTED_API_KEY]", sanitized)

        # Mistral AI keys: mstrl_...
        sanitized = re.sub(r"\bmstrl_[a-zA-Z0-9_-]{20,}\b", "[PROTECTED_API_KEY]", sanitized)

        # OpenAI / generic bearer tokens: sk-...
        sanitized = re.sub(r"\bsk-[a-zA-Z0-9]{20,}\b", "[PROTECTED_API_KEY]", sanitized)

        # Database URLs with credentials
        sanitized = re.sub(
            r"postgresql(?:\+psycopg2)?:\/\/[^:]+:[^@]+@[^\/]+\/[^\s\?]+",
            "postgresql://[PROTECTED_USER]:[PROTECTED_PWD]@[PROTECTED_HOST]/[DB]",
            sanitized,
        )

        # JWT Tokens (3 base64 chunks separated by dots)
        sanitized = re.sub(
            r"\beyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b",
            "[PROTECTED_JWT_TOKEN]",
            sanitized,
        )

        # Scrub 16-digit credit card patterns
        sanitized = re.sub(r"\b(?:\d{4}[ -]?){3}\d{4}\b", "****-****-****-****", sanitized)

        return sanitized
