"""Governance, Drift, Fairness, and Champion/Challenger API Endpoints."""

from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.models.user import User
from backend.app.api.deps import get_current_active_user, require_admin, require_investigator
from backend.app.services.governance_service import GovernanceService
from backend.app.services.model_health_service import ModelHealthService
from backend.app.services.drift_monitoring_service import DriftMonitoringService
from backend.app.services.champion_challenger_service import ChampionChallengerService

router = APIRouter()


@router.get(
    "/summary",
    summary="Get Unified System Governance Snapshot",
    description="Returns comprehensive telemetry across Dataset Health, Model Health, Calibration, Anomaly Status, Drift, Champion/Challenger, and Fairness.",
)
def get_governance_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_investigator),
) -> Dict[str, Any]:
    """Retrieve full unified governance console snapshot."""
    snapshot = GovernanceService.get_unified_governance_snapshot(db)
    return snapshot.to_dict()


@router.get(
    "/health",
    summary="Get Operational Model Health Metrics",
    description="Returns real runtime operational health metrics: throughput, block/review rates, average risk score, latency.",
)
def get_model_health(
    window_hours: int = Query(None, description="Optional filter window in hours"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_investigator),
) -> Dict[str, Any]:
    """Retrieve runtime operational model health."""
    health = ModelHealthService.evaluate_model_health(db, window_hours=window_hours)
    return health.to_dict()


@router.get(
    "/drift",
    summary="Get Statistical Data & Prediction Drift Diagnostics",
    description="Evaluates Population Stability Index (PSI) and prediction/risk distribution divergence.",
)
def get_drift_report(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_investigator),
) -> Dict[str, Any]:
    """Retrieve feature and prediction distribution drift report."""
    drift = DriftMonitoringService.evaluate_live_drift(db)
    return drift.to_dict()


@router.get(
    "/fairness",
    summary="Get Operational Sub-Group Fairness Audit",
    description="Audits decision parity across available operational attributes without inferring sensitive demographic characteristics.",
)
def get_fairness_audit(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_investigator),
) -> Dict[str, Any]:
    """Retrieve sub-group fairness and parity report."""
    fairness = GovernanceService.audit_fairness_on_available_features(db)
    return fairness.to_dict()


@router.post(
    "/promote",
    summary="Promote Challenger Model to Champion (Admin Only)",
    description="Evaluates candidate promotion gates and safely transitions active model with audit preservation and rollback capability.",
)
def promote_candidate_model(
    candidate_model_name: str = Query(..., description="Name of the challenger model to promote (e.g., random_forest)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> Dict[str, Any]:
    """Execute candidate model promotion."""
    result = ChampionChallengerService.promote_challenger(
        db=db,
        candidate_model_name=candidate_model_name,
        user_id=current_user.id,
    )
    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.error_message or "Candidate promotion gates failed.",
        )
    return result.to_dict()
