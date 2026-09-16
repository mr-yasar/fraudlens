"""
Three-Scenario Acceptance Test Suite (Phases 52, 59, 67).
Validates the authoritative pre-auth decisioning and payment submission gate.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from datetime import datetime, timezone, timedelta

from backend.app.main import app
from backend.app.core.database import Base, get_db
from backend.app.models.user import User
from backend.app.models.customer import Customer
from backend.app.models.transaction import Transaction
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
def setup_test_environment():
    app.dependency_overrides[get_db] = override_get_db
    Base.metadata.create_all(bind=test_engine)
    db = TestingSessionLocal()

    # User
    user = User(
        name="Acceptance Investigator",
        email="acceptance_inv@test.internal",
        password_hash=get_password_hash("InvestigatorPass123!"),
        role=UserRole.FRAUD_INVESTIGATOR.value,
        is_active=True,
    )
    db.add(user)

    # Customers
    c_low = Customer(customer_id="CUST-SCEN-LOW", account_age_days=365)
    c_med = Customer(customer_id="CUST-SCEN-MED", account_age_days=180)
    c_high = Customer(customer_id="CUST-SCEN-HIGH", account_age_days=30)
    db.add_all([c_low, c_med, c_high])
    db.commit()

    # Seed historical baseline
    past_time = datetime.now(timezone.utc) - timedelta(days=2)
    for i in range(5):
        db.add(Transaction(
            transaction_id=f"TX-SCEN-LOW-{i}",
            customer_id="CUST-SCEN-LOW",
            amount=50.0,
            transaction_hour=14,
            merchant_category="retail",
            transaction_country="US",
            geo_location_region="CA",
            device_type="web",
            transaction_type="online_payment",
            fraud_probability=0.01,
            risk_score=5.0,
            risk_level="LOW",
            created_at=past_time + timedelta(hours=i),
        ))
        db.add(Transaction(
            transaction_id=f"TX-SCEN-MED-{i}",
            customer_id="CUST-SCEN-MED",
            amount=100.0,
            transaction_hour=14,
            merchant_category="retail",
            transaction_country="US",
            geo_location_region="CA",
            device_type="web",
            transaction_type="online_payment",
            fraud_probability=0.04,
            risk_score=8.0,
            risk_level="LOW",
            created_at=past_time + timedelta(hours=i),
        ))
        db.add(Transaction(
            transaction_id=f"TX-SCEN-HIGH-{i}",
            customer_id="CUST-SCEN-HIGH",
            amount=80.0,
            transaction_hour=15,
            merchant_category="retail",
            transaction_country="US",
            geo_location_region="CA",
            device_type="web",
            transaction_type="online_payment",
            fraud_probability=0.03,
            risk_score=7.0,
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


def test_scenario_1_low_risk_allows_and_calls_provider(client, auth_headers):
    """
    Scenario 1: Normal customer, routine amount, trusted device/location.
    Expected: ALLOW -> Provider execution permitted.
    """
    payload = {
        "customer_id": "CUST-SCEN-LOW",
        "amount": 55.0,
        "currency": "USD",
        "merchant_name": "Target Store",
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
    assert data["lifecycle_status"] in ("SUCCEEDED", "AUTHORIZED", "PROCESSING")
    assert data["external_payment_id"] is not None


def test_scenario_2_medium_risk_requires_review_blocks_provider(client, auth_headers):
    """
    Scenario 2: Moderate amount deviation (3.5x baseline), new device.
    Expected: REVIEW -> Case created, Provider NOT submitted.
    """
    payload = {
        "customer_id": "CUST-SCEN-MED",
        "amount": 350.0,
        "currency": "USD",
        "merchant_name": "Electronics Superstore",
        "merchant_category": "electronics",
        "device_type": "mobile_android",
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
    assert data["external_payment_id"] is None  # Provider never invoked


def test_scenario_3_high_risk_blocks_immediately(client, auth_headers):
    """
    Scenario 3: Extreme amount (100x baseline), high-risk category, foreign location anomaly.
    Expected: BLOCK -> Provider NOT submitted.
    """
    payload = {
        "customer_id": "CUST-SCEN-HIGH",
        "amount": 8000.0,
        "currency": "USD",
        "merchant_name": "Offshore Crypto Exchange",
        "merchant_category": "crypto_exchange",
        "device_type": "tor_exit_node",
        "location": "Lagos",
        "transaction_country": "NG",
        "transaction_type": "wire_transfer",
        "failed_attempts": 3,
    }

    resp = client.post("/api/v1/payment/initiate", json=payload, headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()

    assert data["decision"] == "BLOCK"
    assert data["risk_level"] == "HIGH"
    assert data["ready_for_provider"] is False
    assert data["lifecycle_status"] == "BLOCKED"
    assert data["external_payment_id"] is None  # Provider never invoked
