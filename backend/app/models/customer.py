"""Customer model definition."""

from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from backend.app.core.database import Base


class Customer(Base):
    """Customer profile model tracking customer identities, tenure, simulated wallet, and behavior."""

    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    customer_id = Column(String(100), unique=True, index=True, nullable=False)
    account_age_days = Column(Integer, nullable=True)
    simulated_balance = Column(Float, default=50000.0, nullable=False, server_default="50000.0")
    currency = Column(String(10), default="USD", nullable=False, server_default="USD")
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    name = Column(String(200), nullable=True)
    email = Column(String(200), nullable=True)
    risk_segment = Column(String(50), nullable=True, default="Standard")

    @property
    def account_balance(self) -> float:
        return float(self.simulated_balance or 0.0)

    @account_balance.setter
    def account_balance(self, value: float) -> None:
        self.simulated_balance = float(value)

    # Relationships
    transactions = relationship(
        "Transaction",
        back_populates="customer",
        cascade="all, delete-orphan",
    )
    payment_intents = relationship(
        "PaymentIntent",
        back_populates="customer",
        cascade="all, delete-orphan",
    )
    beneficiaries = relationship(
        "Beneficiary",
        back_populates="customer",
        cascade="all, delete-orphan",
    )
    devices = relationship(
        "CustomerDevice",
        back_populates="customer",
        cascade="all, delete-orphan",
    )
    approvals = relationship(
        "TransactionApproval",
        back_populates="customer",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Customer id={self.id} customer_id='{self.customer_id}' balance={self.simulated_balance}>"

