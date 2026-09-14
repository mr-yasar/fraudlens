"""Investigation model definition."""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from backend.app.core.database import Base


class Investigation(Base):
    """Fraud investigation case record linking flagged transactions to analyst determinations."""

    __tablename__ = "investigations"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    case_id = Column(String(100), unique=True, index=True, nullable=False)
    transaction_id = Column(
        String(100),
        ForeignKey("transactions.transaction_id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    investigator_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    status = Column(String(50), default="open", index=True, nullable=False)
    decision = Column(String(50), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Relationships
    transaction = relationship("Transaction", back_populates="investigations")
    investigator = relationship("User", back_populates="investigations")

    __table_args__ = (
        Index("ix_investigations_status_created", "status", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<Investigation id={self.id} case_id='{self.case_id}' status='{self.status}' decision='{self.decision}'>"
