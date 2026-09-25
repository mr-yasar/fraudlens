"""Tests for AI Voice Help and What is Fraud explainer endpoints."""

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.api.deps import get_current_active_user
from backend.app.models.user import User
from backend.app.schemas.user import UserRole


@pytest.fixture
def client():
    app.dependency_overrides[get_current_active_user] = lambda: User(
        id=1,
        email="test@fraudlens.com",
        name="Test Operator",
        role=UserRole.ADMIN.value,
        is_active=True,
    )
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_ai_voice_help_what_is_fraud(client):
    # Call AI voice help
    res = client.post(
        "/api/v1/investigations/ai-voice-help/explain?topic=what_is_fraud&provider=gemini",
    )
    assert res.status_code == 200
    data = res.json()
    assert "What is Financial Fraud" in data["title"]
    assert "voice_narration_script" in data
    assert len(data["voice_narration_script"]) > 20
    assert "Google Gemini" in data["provider"]
    assert len(data["key_points"]) >= 3


def test_ai_voice_help_custom_query_grok(client):
    res = client.post(
        "/api/v1/investigations/ai-voice-help/explain?topic=custom_query&query=What+is+an+anomaly+score&provider=grok",
    )
    assert res.status_code == 200
    data = res.json()
    assert "anomaly score" in data["title"].lower()
    assert "xAI Grok-2" in data["provider"]
    assert "voice_narration_script" in data
