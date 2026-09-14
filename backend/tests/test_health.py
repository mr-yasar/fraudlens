"""Test health check endpoints."""

from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_root_endpoint():
    """Verify root endpoint provides API metadata."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert data["health"] == "/api/health"


def test_api_health_endpoint():
    """Verify top-level /api/health endpoint."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "fraud-detection-api"
    assert "timestamp" in data
    assert "version" in data


def test_api_v1_health_endpoint():
    """Verify versioned /api/v1/health endpoint."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "fraud-detection-api"
