"""Device model definition for customer hardware profiling and anomaly detection."""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from backend.app.core.database import Base


class CustomerDevice(Base):
    """Customer registered or observed client device for security & fingerprint analysis."""

    __tablename__ = "customer_devices"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    customer_id = Column(
        String(100),
        ForeignKey("customers.customer_id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    device_identifier = Column(String(150), nullable=False, index=True)
    device_type = Column(String(50), nullable=False)
    browser_or_client = Column(String(100), nullable=True)
    location_region = Column(String(100), nullable=True)
    is_trusted = Column(Boolean, default=True, nullable=False)
    is_compromised = Column(Boolean, default=False, nullable=False)
    first_seen_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    last_seen_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Relationships
    customer = relationship("Customer", back_populates="devices")

    __table_args__ = (
        Index("ix_cust_device_unique", "customer_id", "device_identifier"),
    )

    def __repr__(self) -> str:
        return f"<CustomerDevice id={self.id} customer='{self.customer_id}' device='{self.device_identifier}'>"
