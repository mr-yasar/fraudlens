"""AI Assistant Chat Endpoint — Gemini + Grok + Smart Fallback (Phase 15).

Provides a conversational AI assistant powered by Google Gemini 2.0 Flash or
xAI Grok-2 for user-facing fraud education and forensic explanation queries.
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from backend.app.api.deps import get_current_active_user, get_optional_current_user
from backend.app.models.user import User
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

router = APIRouter()


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
        description="Preferred LLM provider: 'gemini' | 'grok' | None (auto)",
    )
    temperature: float = Field(0.7, ge=0.0, le=1.0)
    context: Optional[str] = Field(
        None,
        description="Optional domain context (e.g. transaction_id, current_view)",
    )
    role: Optional[str] = Field(
        None,
        description="Active perspective/role: 'customer' | 'investigator' | 'admin' | 'merchant'",
    )


class ChatResponse(BaseModel):
    response: str
    provider: str
    model: str
    used_real_api: bool
    routing: Optional[Dict[str, Any]] = None
    grok_challenge_applied: bool = False


class ProvidersResponse(BaseModel):
    providers: List[Dict[str, Any]]
    gemini_configured: bool
    grok_configured: bool
    mistral_configured: bool = False
    default_provider: str


# ─────────────────────────────────────────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────────────────────────────────────────
@router.post(
    "/chat",
    response_model=ChatResponse,
    summary="AI Assistant Chat",
    description=(
        "Send a conversation to Google Gemini 2.0 Flash or xAI Grok-2 for fraud education, "
        "transaction explanation, and investigative assistance. Falls back to the smart template "
        "engine when no API key is configured."
    ),
)
def ai_chat(
    payload: ChatRequest,
    current_user: User = Depends(get_current_active_user),
) -> ChatResponse:
    """Route a chat conversation to the configured LLM."""
    messages = [{"role": m.role, "content": m.content} for m in payload.messages]

    # Inject domain context if provided
    if payload.context:
        messages = [
            {
                "role": "system",
                "content": f"Current context: {payload.context}",
            }
        ] + messages

    user_role = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
    user_name = current_user.name or current_user.email.split("@")[0]

    user_info = {
        "name": user_name,
        "role": user_role,
        "email": current_user.email,
    }

    try:
        result = chat_with_llm(
            messages=messages,
            provider=payload.provider,
            temperature=payload.temperature,
            role=user_role,
            user_info=user_info,
        )
        return ChatResponse(**result)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"AI service temporarily unavailable: {exc}",
        )


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
    description="Directly tests and validates the configured API key with xAI Grok or Google Gemini.",
)
def verify_provider_key(
    provider: str = "grok",
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
