"""In-App Security and Operational Alert Model (Phase 32)."""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Index
from sqlalchemy.sql import func
from backend.app.core.database import Base


class Alert(Base):
    """Stores in-app security alerts, high-risk anomalies, and system health triggers."""

    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    alert_id = Column(String(100), unique=True, index=True, nullable=False)
    alert_type = Column(String(50), index=True, nullable=False)
    severity = Column(String(20), index=True, nullable=False)  # LOW, MEDIUM, HIGH, CRITICAL
    entity_id = Column(String(100), index=True, nullable=True)  # payment_id, customer_id, etc.
    message = Column(Text, nullable=False)
    details_json = Column(Text, nullable=True)
    is_acknowledged = Column(Boolean, default=False, index=True, nullable=False)
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    acknowledged_by = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        Index("ix_alerts_ack_created", "is_acknowledged", "created_at"),
        Index("ix_alerts_type_severity", "alert_type", "severity"),
    )

    def __repr__(self) -> str:
        return f"<Alert id={self.alert_id} type='{self.alert_type}' severity='{self.severity}'>"
