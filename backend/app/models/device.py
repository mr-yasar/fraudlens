"""Device model definition for customer hardware profiling and anomaly detection."""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from backend.app.core.database import Base


class CustomerDevice(Base):
    """Customer registered or observed client device for security & fingerprint analysis."""

    __tablename__ = "customer_devices"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    customer_id = Column(
        String(100),
        ForeignKey("customers.customer_id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    device_identifier = Column(String(150), nullable=False, index=True)
    device_name = Column(String(150), nullable=True)
    device_type = Column(String(50), nullable=False)
    os = Column(String(100), nullable=True)
    browser = Column(String(100), nullable=True)
    browser_or_client = Column(String(100), nullable=True)
    location_region = Column(String(100), nullable=True)
    is_trusted = Column(Boolean, default=True, nullable=False)
    is_compromised = Column(Boolean, default=False, nullable=False)
    trust_score = Column(Integer, default=100, nullable=True)
    status = Column(String(50), default="ACTIVE", nullable=True)  # ACTIVE, SUSPICIOUS, REVOKED, BLOCKED
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

    # Aliases / properties for Section 7 schema compatibility
    @property
    def device_id(self) -> str:
        return self.device_identifier

    @property
    def trusted(self) -> bool:
        return bool(self.is_trusted and not self.is_compromised)

    @property
    def first_seen(self):
        return self.first_seen_at

    @property
    def last_seen(self):
        return self.last_seen_at

    # Relationships
    customer = relationship("Customer", back_populates="devices")
    user = relationship("User", backref="devices", foreign_keys=[user_id])

    __table_args__ = (
        Index("ix_cust_device_unique", "customer_id", "device_identifier"),
    )

    def __repr__(self) -> str:
        return f"<CustomerDevice id={self.id} customer='{self.customer_id}' device='{self.device_identifier}' trust={self.trust_score}>"

