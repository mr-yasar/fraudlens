"""Alert Management Service (Phase 32).

Generates, retrieves, and updates in-app alerts for high-risk payments,
behavioral anomalies, webhook failures, and model drift events.
"""

import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from backend.app.models.alert import Alert
from backend.app.services.event_broadcaster import EventBroadcaster


class AlertType:
    HIGH_RISK_PAYMENT = "HIGH_RISK_PAYMENT"
    PAYMENT_BLOCKED = "PAYMENT_BLOCKED"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    VELOCITY_ANOMALY = "VELOCITY_ANOMALY"
    BEHAVIOURAL_ANOMALY = "BEHAVIOURAL_ANOMALY"
    MODEL_HEALTH = "MODEL_HEALTH"
    SYSTEM_HEALTH = "SYSTEM_HEALTH"
    WEBHOOK_FAILURE = "WEBHOOK_FAILURE"


class AlertService:
    """Service to record and query in-app security alerts."""

    @classmethod
    def create_alert(
        cls,
        db: Session,
        alert_type: str,
        severity: str,
        message: str,
        entity_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> Alert:
        """Create and persist an alert, and broadcast it over real-time events."""
        alert_id = f"ALT-{uuid.uuid4().hex[:8].upper()}"
        alert = Alert(
            alert_id=alert_id,
            alert_type=alert_type,
            severity=severity.upper(),
            entity_id=entity_id,
            message=message,
            details_json=json.dumps(details or {}),
            is_acknowledged=False,
        )
        db.add(alert)
        db.commit()
        db.refresh(alert)

        # Broadcast alert event to WebSocket/SSE stream
        EventBroadcaster.get_instance().sync_broadcast("alert.created", {
            "alert_id": alert.alert_id,
            "alert_type": alert.alert_type,
            "severity": alert.severity,
            "entity_id": alert.entity_id,
            "message": alert.message,
            "created_at": alert.created_at.isoformat() if alert.created_at else None,
        })

        return alert

    @classmethod
    def list_alerts(
        cls,
        db: Session,
        unacknowledged_only: bool = False,
        severity: Optional[str] = None,
        limit: int = 50,
    ) -> List[Alert]:
        """Fetch filtered list of alerts."""
        query = db.query(Alert)
        if unacknowledged_only:
            query = query.filter(Alert.is_acknowledged.is_(False))
        if severity:
            query = query.filter(Alert.severity == severity.upper())
        return query.order_by(Alert.created_at.desc()).limit(limit).all()

    @classmethod
    def acknowledge_alert(
        cls,
        db: Session,
        alert_id: str,
        acknowledged_by: str = "investigator",
    ) -> Optional[Alert]:
        """Mark an alert as acknowledged."""
        alert = db.query(Alert).filter(Alert.alert_id == alert_id).first()
        if alert:
            alert.is_acknowledged = True
            alert.acknowledged_at = datetime.now(timezone.utc)
            alert.acknowledged_by = acknowledged_by
            db.commit()
            db.refresh(alert)
        return alert
