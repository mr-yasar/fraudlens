"""Payment Intent and Payment Attempt Models.

Encapsulates the full payment domain lifecycle, cleanly separated from
the ML fraud probability, risk score, and gateway decision.
"""

from enum import Enum
from sqlalchemy import Column, Integer, Float, String, Text, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from backend.app.core.database import Base


class PaymentLifecycleStatus(str, Enum):
    """Explicit Payment Lifecycle states."""
    CREATED = "CREATED"
    RISK_EVALUATING = "RISK_EVALUATING"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    APPROVED = "APPROVED"
    BLOCKED = "BLOCKED"
    SUBMITTED = "SUBMITTED"
    PROCESSING = "PROCESSING"
    AUTHORIZED = "AUTHORIZED"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"


class PaymentIntent(Base):
    """Authoritative Payment Intent record tracking state across pre-auth risk and gateway submission."""

    __tablename__ = "payment_intents"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    payment_id = Column(String(100), unique=True, index=True, nullable=False)
    customer_id = Column(String(100), ForeignKey("customers.customer_id"), index=True, nullable=False)
    
    # Financial details
    amount = Column(Float, nullable=False)
    currency = Column(String(3), default="USD", nullable=False)
    merchant_name = Column(String(150), nullable=False)
    merchant_category = Column(String(50), nullable=False)
    payment_method = Column(String(50), default="card", nullable=False)

    # Lifecycle State (Separated from fraud decision)
    lifecycle_status = Column(String(50), default=PaymentLifecycleStatus.CREATED.value, index=True, nullable=False)

    # Fraud Risk Evaluation Results (Strictly separated fields)
    fraud_probability = Column(Float, nullable=True)  # ML Output [0.0, 1.0]
    risk_score = Column(Integer, nullable=True)        # 0 - 100 Integer metric
    risk_level = Column(String(20), nullable=True)       # LOW / MEDIUM / HIGH
    fraud_decision = Column(String(20), nullable=True)   # ALLOW / REVIEW / BLOCK
    behaviour_deviation_score = Column(Float, nullable=True)
    is_cold_start = Column(Boolean, default=False)
    model_version = Column(String(50), nullable=True)
    explanation_id = Column(String(100), nullable=True)

    # Provider Execution Details
    provider_name = Column(String(50), default="sandbox_gateway", nullable=False)
    external_payment_id = Column(String(100), index=True, nullable=True)
    
    # Idempotency & Case Links
    idempotency_key = Column(String(128), index=True, nullable=True)
    request_fingerprint = Column(String(64), nullable=True)
    case_id = Column(String(100), index=True, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    customer = relationship("Customer", back_populates="payment_intents", foreign_keys=[customer_id])
    attempts = relationship("PaymentAttempt", back_populates="payment_intent", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_payment_intents_lifecycle_created", "lifecycle_status", "created_at"),
        Index("ix_payment_intents_cust_created", "customer_id", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<PaymentIntent id={self.payment_id} status={self.lifecycle_status} decision={self.fraud_decision} amount={self.amount}>"


class PaymentAttempt(Base):
    """Records individual provider submission attempts for a payment intent."""

    __tablename__ = "payment_attempts"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    payment_id = Column(String(100), ForeignKey("payment_intents.payment_id", ondelete="CASCADE"), index=True, nullable=False)
    attempt_number = Column(Integer, default=1, nullable=False)
    provider_name = Column(String(50), nullable=False)
    external_payment_id = Column(String(100), nullable=True)
    status = Column(String(50), nullable=False)
    error_message = Column(Text, nullable=True)
    error_type = Column(String(50), nullable=True)
    raw_response = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    payment_intent = relationship("PaymentIntent", back_populates="attempts")


class WebhookEventRecord(Base):
    """Audit log of all incoming payment provider webhook events."""

    __tablename__ = "webhook_event_records"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    event_id = Column(String(100), unique=True, index=True, nullable=False)
    provider_name = Column(String(50), index=True, nullable=False)
    event_type = Column(String(100), index=True, nullable=False)
    external_payment_id = Column(String(100), index=True, nullable=True)
    internal_payment_id = Column(String(100), index=True, nullable=True)
    signature_valid = Column(Boolean, default=False, nullable=False)
    processed = Column(Boolean, default=False, nullable=False)
    payload_json = Column(Text, nullable=False)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
