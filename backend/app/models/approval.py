"""Transaction Approval and Verification Request model."""

from enum import Enum
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from backend.app.core.database import Base


class ApprovalStatus(str, Enum):
    """Explicit verification approval state machine states."""
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"


class TransactionApproval(Base):
    """Step-up verification / user approval request record for suspicious transactions."""

    __tablename__ = "transaction_approvals"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    approval_id = Column(String(100), unique=True, index=True, nullable=False)
    payment_id = Column(String(100), ForeignKey("payment_intents.payment_id", ondelete="CASCADE"), index=True, nullable=True)
    transaction_id = Column(String(100), ForeignKey("transactions.transaction_id", ondelete="CASCADE"), index=True, nullable=True)
    customer_id = Column(String(100), ForeignKey("customers.customer_id"), index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    status = Column(String(50), default=ApprovalStatus.PENDING.value, index=True, nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String(10), default="USD", nullable=False)
    risk_score = Column(Integer, nullable=False)
    risk_level = Column(String(20), nullable=False)
    fraud_probability = Column(Float, nullable=False)
    challenge_type = Column(String(50), default="USER_CONFIRMATION", nullable=False)
    verification_token = Column(String(100), nullable=True)
    notes = Column(Text, nullable=True)

    requested_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    responded_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)

    # Relationships
    customer = relationship("Customer", back_populates="approvals")
    user = relationship("User", back_populates="approvals")
    payment_intent = relationship("PaymentIntent", back_populates="approval_record")

    __table_args__ = (
        Index("ix_approvals_status_expires", "status", "expires_at"),
    )

    def __repr__(self) -> str:
        return f"<TransactionApproval id='{self.approval_id}' status='{self.status}' amount={self.amount}>"


# Convenient Alias
Approval = TransactionApproval

