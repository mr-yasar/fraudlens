"""Transaction model definition."""

from sqlalchemy import Column, Integer, String, Numeric, Float, Boolean, DateTime, ForeignKey, Index, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from backend.app.core.database import Base


class Transaction(Base):
    """Financial transaction model containing features, fraud probabilities, and risk scoring."""

    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    transaction_id = Column(String(100), unique=True, index=True, nullable=False)
    customer_id = Column(
        String(100),
        ForeignKey("customers.customer_id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    merchant_id = Column(
        String(50),
        ForeignKey("merchants.merchant_id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    merchant_name = Column(String(150), nullable=True)
    merchant_category = Column(String(100), nullable=True)
    
    amount = Column(Numeric(14, 2), nullable=False)
    currency = Column(String(10), default="INR", nullable=False)
    transaction_hour = Column(Integer, default=12, nullable=False)
    day_of_week = Column(Integer, default=1, nullable=True)
    transaction_type = Column(String(50), nullable=True)
    payment_channel = Column(String(50), nullable=True)
    
    transaction_country = Column(String(10), default="IN", nullable=True)
    geo_location_region = Column(String(100), nullable=True)
    current_location = Column(String(150), nullable=True)
    usual_location = Column(String(150), nullable=True)
    location_changed = Column(Boolean, default=False, nullable=True)
    location_distance = Column(Float, default=0.0, nullable=True)
    
    device_id = Column(String(100), nullable=True)
    device_type = Column(String(50), nullable=True)
    is_new_device = Column(Boolean, default=False, nullable=True)
    is_trusted_device = Column(Boolean, default=True, nullable=True)
    
    beneficiary = Column(String(150), nullable=True)
    beneficiary_id = Column(String(100), nullable=True)
    is_new_beneficiary = Column(Boolean, default=False, nullable=True)
    
    # Behavioral context
    transactions_last_1h = Column(Integer, default=0, nullable=True)
    transactions_last_24h = Column(Integer, default=0, nullable=True)
    transactions_last_7d = Column(Integer, default=0, nullable=True)
    amount_deviation = Column(Float, default=0.0, nullable=True)
    amount_ratio = Column(Float, default=1.0, nullable=True)
    failed_transaction_attempts = Column(Integer, default=0, nullable=True)
    failed_login_attempts = Column(Integer, default=0, nullable=True)
    recent_password_change = Column(Boolean, default=False, nullable=True)
    
    # AI and Risk Outputs
    fraud_probability = Column(Float, nullable=True)
    prediction = Column(Integer, nullable=True)
    risk_score = Column(Float, nullable=True)
    risk_level = Column(String(20), nullable=True)
    
    # Historical / Scenario context (for synthetic ground truth / investigations)
    is_fraud = Column(Integer, default=0, nullable=True)
    fraud_type = Column(String(100), nullable=True)
    fraud_stage = Column(String(100), nullable=True)
    fraud_scenario = Column(String(150), nullable=True)

    status = Column(String(50), default="SUCCESS", nullable=True)
    approval_id = Column(String(100), nullable=True)
    
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
    )

    # Relationships
    customer = relationship("Customer", back_populates="transactions")
    merchant_rel = relationship("Merchant", back_populates="transactions")
    investigations = relationship(
        "Investigation",
        back_populates="transaction",
        cascade="all, delete-orphan",
    )
    shap_explanations = relationship(
        "ShapExplanation",
        back_populates="transaction",
        cascade="all, delete-orphan",
    )

    # Useful composite and operational indexes
    __table_args__ = (
        Index("ix_transactions_prediction_risk", "prediction", "risk_level"),
        Index("ix_transactions_cust_created", "customer_id", "created_at"),
        Index("ix_transactions_merchant_created", "merchant_id", "created_at"),
    )

    @property
    def decision(self) -> str:
        if hasattr(self, "_decision") and self._decision is not None:
            return self._decision
        if self.status in ("SUCCESS", "COMPLETED", "APPROVED"):
            return "ALLOW"
        if self.status in ("BLOCKED", "REJECTED"):
            return "BLOCK"
        if self.status in ("PENDING_VERIFICATION", "PENDING_APPROVAL", "REVIEW_REQUIRED"):
            return "VERIFY"
        if self.prediction == 1 or self.risk_level == "HIGH":
            return "BLOCK"
        if self.risk_level == "MEDIUM":
            return "VERIFY"
        return "ALLOW"

    @decision.setter
    def decision(self, val: str) -> None:
        self._decision = val

    def __repr__(self) -> str:
        return f"<Transaction id={self.id} transaction_id='{self.transaction_id}' amount={self.amount} risk_level='{self.risk_level}'>"
