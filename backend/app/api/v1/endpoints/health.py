"""Health check API endpoint."""

from datetime import datetime, timezone
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class HealthResponse(BaseModel):
    status: str
    service: str
    timestamp: str
    version: str


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health Check",
    description="Returns the operational health status of the backend API service.",
)
def get_health() -> HealthResponse:
    return HealthResponse(
        status="healthy",
        service="fraud-detection-api",
        timestamp=datetime.now(timezone.utc).isoformat(),
        version="0.1.0",
    )
