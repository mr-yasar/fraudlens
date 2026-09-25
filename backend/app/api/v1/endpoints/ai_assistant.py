"""AI Assistant Chat Endpoint — Gemini + Grok + Smart Fallback (Phase 15).

Provides a conversational AI assistant powered by Google Gemini 2.0 Flash or
xAI Grok-2 for user-facing fraud education and forensic explanation queries.
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from backend.app.api.deps import get_current_active_user
from backend.app.models.user import User
from backend.app.services.llm_service import (
    chat_with_llm,
    get_available_providers,
    is_gemini_configured,
    is_grok_configured,
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


class ChatResponse(BaseModel):
    response: str
    provider: str
    model: str
    used_real_api: bool


class ProvidersResponse(BaseModel):
    providers: List[Dict[str, Any]]
    gemini_configured: bool
    grok_configured: bool
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

    try:
        result = chat_with_llm(
            messages=messages,
            provider=payload.provider,
            temperature=payload.temperature,
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
    current_user: User = Depends(get_current_active_user),
) -> ProvidersResponse:
    """Return configured AI providers and their status."""
    import os
    return ProvidersResponse(
        providers=get_available_providers(),
        gemini_configured=is_gemini_configured(),
        grok_configured=is_grok_configured(),
        default_provider=os.getenv("DEFAULT_LLM_PROVIDER", "gemini"),
    )
