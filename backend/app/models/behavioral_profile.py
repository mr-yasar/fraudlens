"""Behavioral Profile persistence model."""

from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from backend.app.core.database import Base


class BehavioralProfile(Base):
    """Customer behavioral profile tracking statistical baseline parameters and trust metrics."""

    __tablename__ = "behavioral_profiles"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    customer_id = Column(String(100), unique=True, index=True, nullable=False)
    normal_transaction_range = Column(String(100), default="₹1,000 - ₹50,000", nullable=False)
    normal_transaction_frequency = Column(String(100), default="2-4 transactions/day", nullable=False)
    common_transaction_times = Column(String(150), default="08:00 - 22:00 IST", nullable=False)
    common_locations = Column(Text, default="Mumbai, Bangalore, Pune", nullable=False)
    trusted_devices = Column(Text, default="MacBook Pro, iPhone 15 Pro", nullable=False)
    average_transaction_amount = Column(Float, default=25000.0, nullable=False)
    behavioral_baseline = Column(Text, nullable=True)
    security_score = Column(Integer, default=95, nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Relationships
    user = relationship("User", backref="behavioral_profile")

    def __repr__(self) -> str:
        return f"<BehavioralProfile customer='{self.customer_id}' avg_amount={self.average_transaction_amount}>"
