"""Idempotency Record Model."""

from sqlalchemy import Column, Integer, String, Text, DateTime, Index
from sqlalchemy.sql import func
from backend.app.core.database import Base


class IdempotencyRecord(Base):
    """Stores client idempotency keys, request fingerprints, and cached HTTP responses."""

    __tablename__ = "idempotency_records"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    idempotency_key = Column(String(128), unique=True, index=True, nullable=False)
    request_fingerprint = Column(String(64), nullable=False)
    resource_id = Column(String(100), nullable=True)
    status_code = Column(Integer, nullable=False)
    response_json = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("ix_idempotency_fingerprint", "request_fingerprint"),
    )

    def __repr__(self) -> str:
        return f"<IdempotencyRecord key='{self.idempotency_key}' status={self.status_code}>"
