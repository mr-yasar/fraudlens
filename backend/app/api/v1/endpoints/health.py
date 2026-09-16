"""Comprehensive Health, Readiness, and Liveness Probes (Phase 45)."""

from datetime import datetime, timezone
from typing import Any, Dict
from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import text

from backend.app.core.database import get_db
from backend.app.services.prediction_service import FraudPredictionService
from backend.app.providers.factory import PaymentProviderFactory
from backend.app.services.event_broadcaster import EventBroadcaster

router = APIRouter()


class SubsystemHealth(BaseModel):
    database: str
    ml_prediction_service: str
    xai_shap_engine: str
    payment_provider_adapter: str
    event_broadcaster: str


class ReadinessResponse(BaseModel):
    status: str
    timestamp: str
    version: str
    subsystems: SubsystemHealth


class HealthResponse(BaseModel):
    status: str
    service: str
    timestamp: str
    version: str


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Basic Health Check",
    description="Returns basic operational status of the API.",
)
def get_health() -> HealthResponse:
    return HealthResponse(
        status="healthy",
        service="fraud-detection-api",
        timestamp=datetime.now(timezone.utc).isoformat(),
        version="0.1.0",
    )


@router.get(
    "/health/liveness",
    summary="Kubernetes / Process Liveness Probe",
)
def get_liveness():
    """Returns 200 if the process is responsive."""
    return {"status": "alive", "timestamp": datetime.now(timezone.utc).isoformat()}


@router.get(
    "/health/readiness",
    response_model=ReadinessResponse,
    summary="Subsystem Readiness Probe",
    description="Deep diagnostic probe verifying connectivity across database, ML model, XAI explainer, and payment adapters.",
)
def get_readiness(db: Session = Depends(get_db)):
    """Evaluate readiness of all platform subsystems."""
    # 1. Database Check
    db_status = "healthy"
    try:
        db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    # 2. ML & SHAP Check
    pred_svc = FraudPredictionService.get_instance()
    ml_status = "healthy" if pred_svc.is_ready and pred_svc.model is not None else "degraded"
    xai_status = "healthy" if pred_svc.shap_explainer is not None else "degraded"

    # 3. Payment Provider Check
    try:
        provider = PaymentProviderFactory.get_provider("sandbox_gateway")
        prov_status = "healthy" if provider is not None else "unhealthy"
    except Exception as e:
        prov_status = f"unhealthy: {str(e)}"

    # 4. Event Stream Check
    broadcaster = EventBroadcaster.get_instance()
    evt_status = "healthy" if broadcaster is not None else "unhealthy"

    overall = "ready" if (db_status == "healthy" and ml_status == "healthy") else "degraded"

    return ReadinessResponse(
        status=overall,
        timestamp=datetime.now(timezone.utc).isoformat(),
        version="0.1.0",
        subsystems=SubsystemHealth(
            database=db_status,
            ml_prediction_service=ml_status,
            xai_shap_engine=xai_status,
            payment_provider_adapter=prov_status,
            event_broadcaster=evt_status,
        ),
    )
