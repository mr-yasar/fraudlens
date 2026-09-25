"""Merchant model definition."""

from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from backend.app.core.database import Base


class Merchant(Base):
    """Master merchant model containing profiling, location, and historical fraud pattern context."""

    __tablename__ = "merchants"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    merchant_id = Column(String(50), unique=True, index=True, nullable=False)
    merchant_name = Column(String(150), index=True, nullable=False)
    category = Column(String(100), index=True, nullable=False)
    subcategory = Column(String(100), nullable=True)
    city = Column(String(100), index=True, nullable=False)
    area = Column(String(150), nullable=True)
    state = Column(String(100), nullable=True)
    pincode = Column(String(20), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    business_age = Column(Integer, default=1, nullable=False)
    average_ticket = Column(Float, default=1000.0, nullable=False)
    operating_hours = Column(String(100), default="09:00-21:00", nullable=True)
    business_type = Column(String(100), nullable=True)
    payment_channel = Column(String(100), nullable=True)
    
    # Historical Synthetic Profile
    historical_fraud_rate = Column(Float, default=0.0, nullable=False)
    historical_fraud_count = Column(Integer, default=0, nullable=False)
    historical_fraud_pattern = Column(String(200), nullable=True)
    historical_fraud_summary = Column(Text, nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Relationships
    transactions = relationship("Transaction", back_populates="merchant_rel", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Merchant id={self.id} merchant_id='{self.merchant_id}' name='{self.merchant_name}' category='{self.category}'>"
