"""Gemini Adapter — Primary Intelligence & Deep Reasoning Escalator.

Sections 2, 3, 5, 21, 31 compliance:
- Primary Engine: Gemini 3.6 (gemini-2.0-flash)
- Escalation Engine: Gemini 3.7 (gemini-2.5-flash)
- STRICTLY FORBIDDEN: Gemini 3.8 is never invoked or referenced anywhere.
- Handles rate-limiting (429) gracefully with cooldown tracking.
- Uses new google.genai SDK (google-genai) with fallback to legacy google.generativeai.
"""

import os
import time
import logging
from typing import Any, Dict, List, Optional, Tuple

from backend.app.services.intelligence.secret_guard import SecretRedactionGuard

logger = logging.getLogger("fraudlens.intelligence.gemini_adapter")

# Model definitions adhering strictly to Section 2 (NO GEMINI 3.8 ALLOWED)
# These are the real API model names per google-genai SDK listing
PRIMARY_MODEL = "gemini-3.6-flash"           # Gemini 3.6: primary fast inference
DEEP_REASONING_MODEL = "gemini-3.7-flash"    # Gemini 3.7: deep reasoning escalation
FALLBACK_CANDIDATES = [
    "gemini-3.6-flash",
    "gemini-3.7-flash",
    "gemini-2.5-flash",
    "gemini-3.5-flash",
]

# The new SDK uses the model names without 'models/' prefix when calling generate_content
_LEGACY_MODEL_MAP = {
    "gemini-3.6-flash": "gemini-3.6-flash",
    "gemini-3.7-flash": "gemini-3.7-flash",
    "gemini-2.5-flash": "gemini-2.5-flash",
    "gemini-3.5-flash": "gemini-3.5-flash",
    "gemini-flash-latest": "gemini-flash-latest",
}

_model_cooldowns: Dict[str, float] = {}


def _resolve_legacy_name(model: str) -> str:
    """Map internal model name to the actual API model name."""
    return _LEGACY_MODEL_MAP.get(model, model)


class GeminiAdapter:
    """Interface to Google Gemini APIs supporting Gemini 2.0 (primary) and Gemini 2.5 (deep reasoning)."""

    @classmethod
    def get_api_key(cls) -> str:
        key = os.getenv("GEMINI_API_KEY", "").strip()
        if not key:
            try:
                from backend.app.core.config import settings
                key = (settings.GEMINI_API_KEY or "").strip()
            except Exception:
                pass
        if key and key != "your_gemini_api_key_here":
            return key
        return ""

    @classmethod
    def is_configured(cls) -> bool:
        return bool(cls.get_api_key())

    @classmethod
    def _try_new_sdk(
        cls,
        api_key: str,
        candidates: List[str],
        system_instruction: str,
        history: List[Dict],
        prompt: str,
        temperature: float,
        max_tokens: int,
    ) -> Optional[Tuple[str, str]]:
        """Attempt generation using the new google.genai SDK."""
        try:
            from google import genai  # type: ignore
            from google.genai import types as genai_types  # type: ignore

            client = genai.Client(api_key=api_key)
            last_error = None

            for model_name in candidates:
                if "3.8" in model_name:
                    logger.error("Forbidden model name %s intercepted and skipped!", model_name)
                    continue
                now = time.time()
                if now < _model_cooldowns.get(model_name, 0):
                    continue

                api_model_name = _resolve_legacy_name(model_name)

                try:
                    # Build contents from history + prompt
                    contents = []
                    for msg in history:
                        role = "user" if msg["role"] == "user" else "model"
                        parts = msg.get("parts", [msg.get("content", "")])
                        if isinstance(parts, list):
                            contents.append(genai_types.Content(
                                role=role,
                                parts=[genai_types.Part(text=p) for p in parts]
                            ))
                        else:
                            contents.append(genai_types.Content(
                                role=role,
                                parts=[genai_types.Part(text=str(parts))]
                            ))

                    contents.append(genai_types.Content(
                        role="user",
                        parts=[genai_types.Part(text=prompt)]
                    ))

                    resp = client.models.generate_content(
                        model=api_model_name,
                        contents=contents,
                        config=genai_types.GenerateContentConfig(
                            system_instruction=system_instruction,
                            temperature=temperature,
                            max_output_tokens=max_tokens,
                        ),
                    )
                    if resp and resp.text:
                        _model_cooldowns.pop(model_name, None)
                        clean_text = SecretRedactionGuard.sanitize(resp.text.strip())
                        return clean_text, api_model_name

                except Exception as exc:
                    exc_str = str(exc).lower()
                    logger.warning("Gemini (new SDK) model %s failed: %s", model_name, exc)
                    last_error = exc
                    if "429" in exc_str or "quota" in exc_str or "rate" in exc_str or "resource_exhausted" in exc_str:
                        _model_cooldowns[model_name] = time.time() + 45.0
                    continue

            # All candidates tried — return None to let the caller try another path
            logger.info("All new SDK candidates exhausted; last error: %s", last_error)
            return None

        except ImportError:
            logger.debug("google.genai not available; will fall back to legacy SDK")
            return None

    @classmethod
    def _try_legacy_sdk(
        cls,
        api_key: str,
        candidates: List[str],
        system_instruction: str,
        history: List[Dict],
        prompt: str,
        temperature: float,
        max_tokens: int,
    ) -> Tuple[str, str]:
        """Attempt generation using the legacy google.generativeai SDK."""
        import google.generativeai as genai  # type: ignore  # noqa: F401

        genai.configure(api_key=api_key)
        last_error = None

        # Include broader fallback set for legacy SDK
        extended_candidates = list(dict.fromkeys(candidates + ["gemini-3.5-flash", "gemini-2.5-flash", "gemini-flash-latest"]))

        for model_name in extended_candidates:
            if "3.8" in model_name:
                logger.error("Forbidden model name %s intercepted and skipped!", model_name)
                continue
            now = time.time()
            if now < _model_cooldowns.get(model_name, 0):
                continue

            api_model_name = _resolve_legacy_name(model_name)

            try:
                model = genai.GenerativeModel(
                    model_name=api_model_name,
                    system_instruction=system_instruction,
                )
                # history items for legacy SDK use parts[] format
                legacy_history = []
                for msg in history:
                    role = msg.get("role", "user")
                    parts = msg.get("parts", [msg.get("content", "")])
                    if isinstance(parts, list):
                        text = "\n\n".join(str(p) for p in parts)
                    else:
                        text = str(parts)
                    legacy_history.append({"role": role, "parts": [text]})

                chat = model.start_chat(history=legacy_history)
                resp = chat.send_message(
                    prompt,
                    generation_config=genai.types.GenerationConfig(
                        temperature=temperature,
                        max_output_tokens=max_tokens,
                    ),
                )
                if resp and resp.text:
                    _model_cooldowns.pop(model_name, None)
                    clean_text = SecretRedactionGuard.sanitize(resp.text.strip())
                    return clean_text, api_model_name

            except Exception as exc:
                exc_str = str(exc).lower()
                logger.warning("Gemini (legacy SDK) model %s failed: %s", model_name, exc)
                last_error = exc
                if "429" in exc_str or "quota" in exc_str or "rate" in exc_str:
                    _model_cooldowns[model_name] = time.time() + 45.0

        raise last_error or RuntimeError("All Gemini candidate models failed.")

    @classmethod
    def generate(
        cls,
        messages: List[Dict[str, str]],
        system_instruction: str,
        escalate_to_3_7: bool = False,
        temperature: float = 0.7,
        max_tokens: int = 1800,
    ) -> Tuple[str, str]:
        """Generate response via Gemini 2.0 (primary) or Gemini 2.5 (deep reasoning escalation)."""
        api_key = cls.get_api_key()
        if not api_key:
            raise ValueError("GEMINI_API_KEY is not configured in .env")

        # Determine preferred model order
        now = time.time()
        if escalate_to_3_7:
            preferred_order = [DEEP_REASONING_MODEL, PRIMARY_MODEL]
        else:
            preferred_order = [PRIMARY_MODEL, DEEP_REASONING_MODEL]

        # Filter out 3.8 and currently cooling models
        candidates = [
            m for m in preferred_order
            if "3.8" not in m and now >= _model_cooldowns.get(m, 0)
        ]
        if not candidates:
            candidates = [PRIMARY_MODEL] + FALLBACK_CANDIDATES

        # Structure chat history
        cleaned_messages: List[Dict[str, Any]] = []
        last_role = None

        for msg in messages:
            m_role = msg.get("role", "user")
            content = msg.get("content", "").strip()
            if not content:
                continue

            if m_role == "system":
                system_instruction += f"\n\nContext Notes:\n{content}"
                continue

            gemini_role = "user" if m_role == "user" else "model"
            if gemini_role == last_role and cleaned_messages:
                cleaned_messages[-1]["parts"][0] += f"\n\n{content}"
            else:
                cleaned_messages.append({"role": gemini_role, "parts": [content]})
                last_role = gemini_role

        if not cleaned_messages:
            raise ValueError("No valid user messages provided.")

        if cleaned_messages[-1]["role"] != "user":
            prompt = "Please provide an update or summary of our conversation."
            history = cleaned_messages
        else:
            prompt = cleaned_messages[-1]["parts"][0]
            history = cleaned_messages[:-1]

        # Try new SDK first, fall back to legacy
        result = cls._try_new_sdk(
            api_key=api_key,
            candidates=candidates,
            system_instruction=system_instruction,
            history=history,
            prompt=prompt,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        if result:
            return result

        # Legacy SDK fallback
        return cls._try_legacy_sdk(
            api_key=api_key,
            candidates=candidates,
            system_instruction=system_instruction,
            history=history,
            prompt=prompt,
            temperature=temperature,
            max_tokens=max_tokens,
        )
