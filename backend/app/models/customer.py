"""Customer model definition."""

from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from backend.app.core.database import Base


class Customer(Base):
    """Customer profile model tracking customer identities and tenure."""

    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    customer_id = Column(String(100), unique=True, index=True, nullable=False)
    account_age_days = Column(Integer, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    # Relationships
    transactions = relationship(
        "Transaction",
        back_populates="customer",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Customer id={self.id} customer_id='{self.customer_id}'>"
