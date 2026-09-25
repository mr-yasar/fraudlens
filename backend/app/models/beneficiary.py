"""Beneficiary model definition for tracking known customer transfer recipients."""

from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from backend.app.core.database import Base


class Beneficiary(Base):
    """Customer recipient / beneficiary model representing known and trusted payment endpoints."""

    __tablename__ = "beneficiaries"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    customer_id = Column(
        String(100),
        ForeignKey("customers.customer_id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    beneficiary_name = Column(String(150), nullable=False, index=True)
    beneficiary_account = Column(String(100), nullable=True)
    category = Column(String(50), default="transfer", nullable=False)
    trust_score = Column(Float, default=1.0, nullable=False)
    is_trusted = Column(Boolean, default=True, nullable=False)
    total_transfers = Column(Integer, default=1, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    last_used_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Relationships
    customer = relationship("Customer", back_populates="beneficiaries")

    __table_args__ = (
        Index("ix_beneficiary_cust_name", "customer_id", "beneficiary_name"),
    )

    def __repr__(self) -> str:
        return f"<Beneficiary id={self.id} customer='{self.customer_id}' name='{self.beneficiary_name}'>"
