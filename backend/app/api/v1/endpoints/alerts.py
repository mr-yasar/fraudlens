"""In-App Security Alerts API Endpoints (Phase 32)."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.models.user import User
from backend.app.api.deps import require_investigator
from backend.app.services.alert_service import AlertService

router = APIRouter()


@router.get(
    "",
    summary="List In-App Security Alerts",
    description="Fetches recent platform alerts with optional filtering by severity and unacknowledged status.",
)
def list_alerts(
    unacknowledged_only: bool = Query(False, description="Filter only unacknowledged alerts"),
    severity: Optional[str] = Query(None, description="Filter by severity: LOW, MEDIUM, HIGH, CRITICAL"),
    limit: int = Query(50, ge=1, le=200, description="Max alerts to retrieve"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_investigator),
):
    """List recent in-app security alerts."""
    alerts = AlertService.list_alerts(
        db=db,
        unacknowledged_only=unacknowledged_only,
        severity=severity,
        limit=limit,
    )
    return [
        {
            "alert_id": a.alert_id,
            "alert_type": a.alert_type,
            "severity": a.severity,
            "entity_id": a.entity_id,
            "message": a.message,
            "is_acknowledged": a.is_acknowledged,
            "acknowledged_at": a.acknowledged_at.isoformat() if a.acknowledged_at else None,
            "acknowledged_by": a.acknowledged_by,
            "created_at": a.created_at.isoformat() if a.created_at else None,
        }
        for a in alerts
    ]


@router.post(
    "/{alert_id}/acknowledge",
    summary="Acknowledge In-App Alert",
    description="Marks an alert as acknowledged by the current investigator.",
)
def acknowledge_alert(
    alert_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_investigator),
):
    """Mark alert as acknowledged."""
    alert = AlertService.acknowledge_alert(
        db=db,
        alert_id=alert_id,
        acknowledged_by=current_user.email or current_user.name,
    )
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alert with ID '{alert_id}' not found.",
        )
    return {
        "status": "success",
        "alert_id": alert.alert_id,
        "is_acknowledged": alert.is_acknowledged,
        "acknowledged_by": alert.acknowledged_by,
    }
