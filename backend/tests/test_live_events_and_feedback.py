"""Unit and integration tests for Live Event Broadcasting and Feedback Loop (Part 2)."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.main import app
from backend.app.core.database import Base, get_db
from backend.app.models.customer import Customer
from backend.app.models.transaction import Transaction
from backend.app.models.investigation import Investigation
from backend.app.models.payment_intent import PaymentIntent
from backend.app.services.event_broadcaster import EventBroadcaster
from backend.app.services.feedback_loop_service import FeedbackLoopService


test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="module", autouse=True)
def setup_test_app():
    app.dependency_overrides[get_db] = override_get_db
    Base.metadata.create_all(bind=test_engine)
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_event_broadcaster_buffering_and_recent():
    """Verify EventBroadcaster stores and returns recent events."""
    broadcaster = EventBroadcaster.get_instance()
    broadcaster.sync_broadcast("test.alert_event", {"score": 85, "payment_id": "PAY-EVT-01"})
    
    recent = broadcaster.get_recent_events(limit=10)
    assert len(recent) >= 1
    assert any(e["event_type"] == "test.alert_event" for e in recent)


def test_feedback_loop_record_ground_truth_and_metrics():
    """Verify FeedbackLoopService records ground truth and computes model accuracy metrics."""
    db = TestingSessionLocal()
    
    # Create customer and transaction
    c = Customer(customer_id="CUST-FEED-01", account_age_days=100)
    db.add(c)
    tx = Transaction(
        transaction_id="TX-FEED-001",
        customer_id="CUST-FEED-01",
        amount=500.0,
        transaction_hour=14,
        fraud_probability=0.88,
        prediction=1,
        risk_score=85.0,
        risk_level="HIGH",
    )
    db.add(tx)
    inv = Investigation(
        case_id="CASE-FEED-001",
        transaction_id="TX-FEED-001",
        status="OPEN",
    )
    db.add(inv)
    db.commit()

    # Record confirmed fraud
    res = FeedbackLoopService.record_ground_truth(
        db=db,
        transaction_id="TX-FEED-001",
        is_fraud=True,
        source="investigator_resolution",
        notes="Confirmed identity theft",
    )
    assert res["recorded_outcome"] == "CONFIRMED_FRAUD"
    assert res["current_metrics"]["true_positives"] >= 1
    assert res["current_metrics"]["precision"] >= 0.0

    db.close()


def test_events_recent_endpoint(client):
    """Verify GET /api/v1/events/recent returns buffered events."""
    resp = client.get("/api/v1/events/recent?limit=5")
    assert resp.status_code == 200
    data = resp.json()
    assert "events" in data
    assert isinstance(data["events"], list)
