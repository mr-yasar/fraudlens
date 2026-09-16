"""Unit and integration tests for Idempotency System (Phase 11)."""

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.app.core.database import Base
from backend.app.models.idempotency import IdempotencyRecord
from backend.app.services.idempotency_service import IdempotencyService


@pytest.fixture
def db_session():
    """Create in-memory SQLite database session for idempotency testing."""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_idempotency_compute_fingerprint():
    """Verify deterministic JSON fingerprinting."""
    p1 = {"amount": 100.0, "customer_id": "CUST-01", "currency": "USD"}
    p2 = {"currency": "USD", "amount": 100.0, "customer_id": "CUST-01"}  # Different key order
    p3 = {"amount": 105.0, "customer_id": "CUST-01", "currency": "USD"}

    fp1 = IdempotencyService.compute_fingerprint(p1)
    fp2 = IdempotencyService.compute_fingerprint(p2)
    fp3 = IdempotencyService.compute_fingerprint(p3)

    assert fp1 == fp2  # Keys sorted deterministically
    assert fp1 != fp3


def test_idempotency_lifecycle(db_session):
    """Verify storing, checking, and replaying idempotency records."""
    key = "idem-test-key-999"
    payload = {"customer_id": "CUST-IDEM-01", "amount": 75.0, "currency": "USD"}
    resp_body = {"transaction_id": "PAY-IDEM-001", "decision": "ALLOW", "risk_score": 10}

    # Initial check (should be cache miss)
    record, is_cached = IdempotencyService.check_idempotency(db_session, key, payload)
    assert record is None
    assert is_cached is False

    # Store response
    stored = IdempotencyService.store_idempotency(
        db=db_session,
        idempotency_key=key,
        request_payload=payload,
        resource_id="PAY-IDEM-001",
        status_code=200,
        response_data=resp_body,
    )
    assert stored.idempotency_key == key

    # Secondary check with identical payload (should be cache hit)
    record2, is_cached2 = IdempotencyService.check_idempotency(db_session, key, payload)
    assert record2 is not None
    assert is_cached2 is True
    assert record2.status_code == 200

    # Third check with altered payload (should raise 409 conflict)
    altered_payload = {"customer_id": "CUST-IDEM-01", "amount": 999.0, "currency": "USD"}
    with pytest.raises(HTTPException) as exc_info:
        IdempotencyService.check_idempotency(db_session, key, altered_payload)
    assert exc_info.value.status_code == 409
