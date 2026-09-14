"""API v1 Endpoints package."""

from backend.app.api.v1.endpoints.health import router as health_router
from backend.app.api.v1.endpoints.auth import router as auth_router
from backend.app.api.v1.endpoints.protected_examples import router as protected_router
from backend.app.api.v1.endpoints.datasets import router as datasets_router
from backend.app.api.v1.endpoints.prediction import router as prediction_router

__all__ = [
    "health_router",
    "auth_router",
    "protected_router",
    "datasets_router",
    "prediction_router",
]
