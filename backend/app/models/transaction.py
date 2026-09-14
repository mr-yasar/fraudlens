"""Transaction model definition."""

from sqlalchemy import Column, Integer, String, Numeric, Float, DateTime, ForeignKey, Index
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
    amount = Column(Numeric(14, 2), nullable=False)
    transaction_hour = Column(Integer, nullable=False)
    merchant_category = Column(String(100), nullable=True)
    transaction_country = Column(String(10), nullable=True)
    geo_location_region = Column(String(100), nullable=True)
    device_type = Column(String(50), nullable=True)
    transaction_type = Column(String(50), nullable=True)
    fraud_probability = Column(Float, nullable=True)
    prediction = Column(Integer, nullable=True)
    risk_score = Column(Float, nullable=True)
    risk_level = Column(String(20), nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
    )

    # Relationships
    customer = relationship("Customer", back_populates="transactions")
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
    )

    def __repr__(self) -> str:
        return f"<Transaction id={self.id} transaction_id='{self.transaction_id}' amount={self.amount} risk_level='{self.risk_level}'>"
