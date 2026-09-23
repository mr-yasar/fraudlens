"""
Customer Behaviour & Device/Session Intelligence Endpoints.
Part B & C: Fraud Intelligence Fabric.
"""

from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.models.user import User
from backend.app.api.deps import get_current_user
from backend.app.services.behavior_intelligence_service import CustomerBehaviourIntelligenceService
from backend.app.services.device_session_service import DeviceSessionRiskService

router = APIRouter()


@router.get(
    "/customer/{customer_id}",
    summary="Get Continuous Customer Behaviour Intelligence",
    description="Retrieves statistical baselines, spending limits, velocity profile, and signal availability for a customer.",
)
def get_customer_behavior_intelligence(
    customer_id: str,
    amount: float = Query(100.0, gt=0.0, description="Hypothetical or reference amount to evaluate"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Retrieve customer behavioral intelligence report."""
    try:
        report = CustomerBehaviourIntelligenceService.evaluate_behavior(
            db=db,
            customer_id=customer_id,
            amount=amount,
        )
        return report.to_dict()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate customer intelligence report: {str(e)}",
        )


@router.get(
    "/device/assess",
    summary="Assess Device and Session Risk Profile",
    description="Evaluates hardware telemetry, spoofed signatures, and session velocity without storing raw credentials.",
)
def assess_device_session_risk(
    customer_id: str = Query(..., description="Customer ID"),
    device_type: str = Query("web", description="Device type"),
    device_id: Optional[str] = Query(None, description="Anonymized device ID"),
    failed_attempts: int = Query(0, ge=0, description="Preceding failed attempts"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Assess device and session risk."""
    try:
        assessment = DeviceSessionRiskService.evaluate_device_session(
            db=db,
            customer_id=customer_id,
            device_type=device_type,
            device_id=device_id,
            failed_attempts=failed_attempts,
        )
        return assessment.to_dict()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to assess device risk: {str(e)}",
        )
