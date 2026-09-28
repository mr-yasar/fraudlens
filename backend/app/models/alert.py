from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Index, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from backend.app.core.database import Base


class Alert(Base):
    """Stores in-app security alerts, high-risk anomalies, and system health triggers."""

    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    alert_id = Column(String(100), unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    customer_id = Column(String(100), nullable=True, index=True)
    alert_type = Column(String(50), index=True, nullable=False)
    severity = Column(String(20), index=True, nullable=False)  # INFO, LOW, MEDIUM, HIGH, CRITICAL
    title = Column(String(200), nullable=True)
    message = Column(Text, nullable=False)
    details_json = Column(Text, nullable=True)
    entity_id = Column(String(200), nullable=True, index=True)  # Reference ID (e.g. transaction_id) that triggered this alert
    status = Column(String(50), default="OPEN", index=True, nullable=True)  # OPEN, ACKNOWLEDGED, RESOLVED
    is_acknowledged = Column(Boolean, default=False, index=True, nullable=False)
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    acknowledged_by = Column(String(100), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    user = relationship("User", backref="alerts")

    __table_args__ = (
        Index("ix_alerts_ack_created", "is_acknowledged", "created_at"),
        Index("ix_alerts_type_severity", "alert_type", "severity"),
        Index("ix_alerts_user_status", "user_id", "status"),
    )

    def __repr__(self) -> str:
        return f"<Alert id={self.alert_id} type='{self.alert_type}' severity='{self.severity}'>"

