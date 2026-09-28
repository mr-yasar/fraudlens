"""Risk Event model definition."""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from backend.app.core.database import Base


class RiskEvent(Base):
    """Granular risk detection and anomaly evaluation events."""

    __tablename__ = "risk_events"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    customer_id = Column(String(100), nullable=True, index=True)
    transaction_id = Column(String(100), nullable=True, index=True)
    event_type = Column(String(100), nullable=False, index=True)  # ANOMALOUS_AMOUNT, UNUSUAL_HOURS, NEW_DEVICE, etc.
    severity = Column(String(20), nullable=False, index=True)      # LOW, MEDIUM, HIGH, CRITICAL
    score = Column(Integer, nullable=False)                        # 0 - 100
    explanation = Column(Text, nullable=False)
    details_json = Column(Text, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
    )

    # Relationships
    user = relationship("User", backref="risk_events")

    __table_args__ = (
        Index("ix_risk_events_user_created", "user_id", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<RiskEvent id={self.id} type='{self.event_type}' score={self.score}>"
