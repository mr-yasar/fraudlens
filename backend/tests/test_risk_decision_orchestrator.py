"""Integration tests for RiskDecisionOrchestrator and Pre-Auth Endpoints (Phases 15-26)."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.main import app
from backend.app.core.database import Base, get_db
from backend.app.models.user import User
from backend.app.models.customer import Customer
from backend.app.models.transaction import Transaction
from backend.app.models.payment_intent import PaymentIntent, PaymentLifecycleStatus
from backend.app.models.investigation import Investigation
from backend.app.core.security import get_password_hash, create_access_token
from backend.app.schemas.user import UserRole


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
    db = TestingSessionLocal()

    # User
    user = User(
        name="Test Investigator",
        email="investigator_orch@test.internal",
        password_hash=get_password_hash("InvestigatorPass123!"),
        role=UserRole.FRAUD_INVESTIGATOR.value,
        is_active=True,
    )
    db.add(user)

    # Customers
    c_low = Customer(customer_id="CUST-ORCH-LOW", account_age_days=180)
    c_med = Customer(customer_id="CUST-ORCH-MED", account_age_days=120)
    c_high = Customer(customer_id="CUST-ORCH-HIGH", account_age_days=300)
    db.add_all([c_low, c_med, c_high])
    db.commit()

    # Seed baseline transactions for each customer with historical timestamps
    from datetime import datetime, timezone, timedelta
    past_time = datetime.now(timezone.utc) - timedelta(days=2)

    for i in range(4):
        db.add(Transaction(
            transaction_id=f"TX-ORCH-LOW-{i}",
            customer_id="CUST-ORCH-LOW",
            amount=90.0 + (i * 5.0),
            transaction_hour=12,
            merchant_category="retail",
            transaction_country="US",
            geo_location_region="CA",
            device_type="web",
            transaction_type="online_payment",
            fraud_probability=0.02,
            risk_score=5.0,
            risk_level="LOW",
            created_at=past_time + timedelta(hours=i),
        ))
        db.add(Transaction(
            transaction_id=f"TX-ORCH-MED-{i}",
            customer_id="CUST-ORCH-MED",
            amount=100.0,
            transaction_hour=14,
            merchant_category="retail",
            transaction_country="US",
            geo_location_region="CA",
            device_type="web",
            transaction_type="online_payment",
            fraud_probability=0.05,
            risk_score=10.0,
            risk_level="LOW",
            created_at=past_time + timedelta(hours=i),
        ))
        db.add(Transaction(
            transaction_id=f"TX-ORCH-HIGH-{i}",
            customer_id="CUST-ORCH-HIGH",
            amount=80.0,
            transaction_hour=15,
            merchant_category="retail",
            transaction_country="US",
            geo_location_region="CA",
            device_type="web",
            transaction_type="online_payment",
            fraud_probability=0.03,
            risk_score=8.0,
            risk_level="LOW",
            created_at=past_time + timedelta(hours=i),
        ))

    db.commit()
    db.close()
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def auth_headers():
    token = create_access_token(subject="1", role="FRAUD_INVESTIGATOR")
    return {"Authorization": f"Bearer {token}"}


def test_orchestrator_scenario_a_allow_submits_provider(client, auth_headers):
    """Scenario A: Known customer with routine transaction is ALLOWed and submitted to sandbox."""
    payload = {
        "customer_id": "CUST-ORCH-LOW",
        "amount": 95.0,
        "currency": "USD",
        "merchant_name": "Target Retail",
        "merchant_category": "retail",
        "device_type": "web",
        "location": "CA",
        "transaction_country": "US",
        "transaction_type": "online_payment",
        "failed_attempts": 0,
    }

    resp = client.post("/api/v1/payment/initiate", json=payload, headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()

    assert data["decision"] == "ALLOW"
    assert data["risk_level"] == "LOW"
    assert data["ready_for_provider"] is True
    assert data["lifecycle_status"] in ("SUCCEEDED", "AUTHORIZED")
    assert data["external_payment_id"] is not None
    assert data["external_payment_id"].startswith("pi_sand_")


def test_orchestrator_scenario_b_review_creates_case_holds_provider(client, auth_headers):
    """Scenario B: Moderate anomaly is REVIEWed, automatically creates case, and holds provider submission."""
    payload = {
        "customer_id": "CUST-ORCH-MED",
        "amount": 350.0,  # 3.5x historical baseline
        "currency": "USD",
        "merchant_name": "Electronics Hub",
        "merchant_category": "electronics",
        "device_type": "mobile_android",  # Novel device
        "location": "CA",
        "transaction_country": "US",
        "transaction_type": "online_payment",
        "failed_attempts": 1,
    }

    resp = client.post("/api/v1/payment/initiate", json=payload, headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()

    assert data["decision"] == "REVIEW"
    assert data["risk_level"] == "MEDIUM"
    assert data["ready_for_provider"] is False
    assert data["lifecycle_status"] == "REVIEW_REQUIRED"
    assert data["case_id"] is not None
    assert data["case_id"].startswith("CASE-")
    assert data["external_payment_id"] is None  # NOT submitted to provider


def test_orchestrator_scenario_c_block_terminates_submission(client, auth_headers):
    """Scenario C: Hostile attack is BLOCKED and never submitted to provider."""
    payload = {
        "customer_id": "CUST-ORCH-HIGH",
        "amount": 7500.0,
        "currency": "USD",
        "merchant_name": "Offshore Crypto Exchange",
        "merchant_category": "crypto",
        "device_type": "unknown_bot",
        "location": "Lagos",
        "transaction_country": "NG",
        "transaction_type": "online_payment",
        "failed_attempts": 4,
    }

    resp = client.post("/api/v1/payment/initiate", json=payload, headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()

    assert data["decision"] == "BLOCK"
    assert data["risk_level"] == "HIGH"
    assert data["risk_score"] >= 71
    assert data["ready_for_provider"] is False
    assert data["lifecycle_status"] == "BLOCKED"
    assert data["external_payment_id"] is None


def test_orchestrator_idempotency_key_replay(client, auth_headers):
    """Verify duplicate request with same Idempotency-Key returns cached response without duplicate intent."""
    payload = {
        "customer_id": "CUST-ORCH-LOW",
        "amount": 55.0,
        "currency": "USD",
        "merchant_name": "Coffee Store",
        "merchant_category": "dining",
        "device_type": "web",
        "location": "CA",
        "transaction_country": "US",
        "transaction_type": "online_payment",
    }
    headers = dict(auth_headers)
    headers["Idempotency-Key"] = "idemp-orch-test-unique-12345"

    # First request
    resp1 = client.post("/api/v1/payment/initiate", json=payload, headers=headers)
    assert resp1.status_code == 200
    data1 = resp1.json()

    # Second request with identical payload and idempotency key
    resp2 = client.post("/api/v1/payment/initiate", json=payload, headers=headers)
    assert resp2.status_code == 200
    data2 = resp2.json()

    assert data1["transaction_id"] == data2["transaction_id"]
    assert data2["idempotent_replay"] is True


def test_orchestrator_cold_start_customer(client, auth_headers):
    """Verify first-time cold start customer with standard transaction is safely ALLOWed."""
    payload = {
        "customer_id": "CUST-COLD-FIRST-TIME",
        "amount": 42.0,
        "currency": "USD",
        "merchant_name": "Bakery",
        "merchant_category": "dining",
        "device_type": "mobile_ios",
        "location": "US",
        "transaction_country": "US",
        "transaction_type": "online_payment",
        "failed_attempts": 0,
    }

    resp = client.post("/api/v1/payment/initiate", json=payload, headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()

    assert data["is_cold_start"] is True
    assert data["decision"] == "ALLOW"
    assert data["risk_level"] == "LOW"
    assert data["ready_for_provider"] is True
