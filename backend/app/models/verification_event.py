"""Verification Event model for step-up multi-factor and OTP tracking."""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Index, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from backend.app.core.database import Base


class VerificationEvent(Base):
    """Tracks step-up verification requests, attempts, OTP codes, states, and expiration."""

    __tablename__ = "verification_events"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    customer_id = Column(String(100), nullable=True, index=True)
    transaction_id = Column(String(100), nullable=True, index=True)
    verification_type = Column(String(50), default="OTP_SMS", nullable=False)  # OTP_SMS, BIOMETRIC, EMAIL_2FA
    status = Column(String(50), default="PENDING", nullable=False, index=True)  # PENDING, VERIFIED, FAILED, EXPIRED, LOCKED
    otp_code_hash = Column(String(255), nullable=True)
    attempts_count = Column(Integer, default=0, nullable=False)
    max_attempts = Column(Integer, default=3, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    last_attempted_at = Column(DateTime(timezone=True), nullable=True)
    resend_available_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
    )
    verified_at = Column(DateTime(timezone=True), nullable=True)

    @property
    def timestamp(self):
        return self.created_at

    # Relationships
    user = relationship("User", backref="verification_events")

    __table_args__ = (
        Index("ix_verif_tx_status", "transaction_id", "status"),
    )

    def __repr__(self) -> str:
        return f"<VerificationEvent id={self.id} tx='{self.transaction_id}' status='{self.status}'>"
