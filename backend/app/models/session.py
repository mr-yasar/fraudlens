"""User session model for authentication and active session security tracking."""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from backend.app.core.database import Base


class UserSession(Base):
    """Tracks active user sessions with IP, approximate location, device identifier, and risk status."""

    __tablename__ = "user_sessions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    customer_id = Column(String(100), nullable=True, index=True)
    session_id = Column(String(100), unique=True, index=True, nullable=False)
    device_id = Column(String(150), nullable=True, index=True)
    device_name = Column(String(150), nullable=True)
    ip_address = Column(String(50), nullable=True)
    approximate_location = Column(String(150), nullable=True)
    session_status = Column(String(50), default="ACTIVE", nullable=False)  # ACTIVE, REVOKED, EXPIRED
    risk_score = Column(Integer, default=5, nullable=False)
    login_time = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    last_active = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Relationships
    user = relationship("User", backref="sessions")

    __table_args__ = (
        Index("ix_user_sessions_user_status", "user_id", "session_status"),
    )

    def __repr__(self) -> str:
        return f"<UserSession id={self.id} session_id='{self.session_id}' status='{self.session_status}'>"
