"""Comprehensive tests for Pre-Authorization Risk Engine and Payment Gateway (Phase 6)."""

from datetime import datetime, timezone
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.main import app
from backend.app.core.database import Base, get_db
from backend.app.core.security import get_password_hash, create_access_token
from backend.app.models.user import User
from backend.app.models.customer import Customer
from backend.app.models.transaction import Transaction
from backend.app.schemas.user import UserRole
from backend.app.schemas.payment import PaymentInitiateRequest, PaymentDecision, RiskLevelEnum
from backend.app.services.preauth_risk_engine import PreAuthRiskEngine

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

    # Seed regular user
    user = User(
        name="Test Investigator",
        email="investigator@test.internal",
        password_hash=get_password_hash("InvestigatorPass123!"),
        role=UserRole.FRAUD_INVESTIGATOR.value,
        is_active=True,
    )
    db.add(user)

    # Seed established customers with $100 normal baseline
    cust_low = Customer(customer_id="CUST-PAY-LOW", account_age_days=120)
    cust_med = Customer(customer_id="CUST-PAY-MED", account_age_days=120)
    cust_high = Customer(customer_id="CUST-PAY-HIGH", account_age_days=120)
    db.add_all([cust_low, cust_med, cust_high])
    db.commit()

    for cid in ["CUST-PAY-LOW", "CUST-PAY-MED", "CUST-PAY-HIGH"]:
        t1 = Transaction(
            transaction_id=f"TX-{cid}-01",
            customer_id=cid,
            amount=90.0,
            transaction_hour=12,
            merchant_category="retail",
            transaction_country="US",
            geo_location_region="CA",
            device_type="web",
            transaction_type="online_payment",
            created_at=datetime.now(timezone.utc),
        )
        t2 = Transaction(
            transaction_id=f"TX-{cid}-02",
            customer_id=cid,
            amount=110.0,
            transaction_hour=15,
            merchant_category="retail",
            transaction_country="US",
            geo_location_region="CA",
            device_type="web",
            transaction_type="online_payment",
            created_at=datetime.now(timezone.utc),
        )
        db.add_all([t1, t2])
    db.commit()
    db.close()

    yield

    Base.metadata.drop_all(bind=test_engine)
    app.dependency_overrides.clear()


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def auth_headers():
    token = create_access_token(subject=1, role="FRAUD_INVESTIGATOR")
    return {"Authorization": f"Bearer {token}"}


def test_preauth_low_risk_allow(client, auth_headers):
    """Verify LOW risk payment request results in ALLOW and ready_for_provider=True."""
    payload = {
        "customer_id": "CUST-PAY-LOW",
        "amount": 95.0,  # Matches historical average of $100
        "currency": "USD",
        "merchant_name": "Acme Grocery",
        "merchant_category": "retail",
        "device_type": "web",
        "location": "CA",
        "transaction_country": "US",
        "transaction_type": "online_payment",
        "failed_attempts": 0,
    }

    response = client.post("/api/v1/payment/initiate", json=payload, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()

    assert data["customer_id"] == "CUST-PAY-LOW"
    assert data["amount"] == 95.0
    assert data["risk_score"] <= 30
    assert data["risk_level"] == "LOW"
    assert data["decision"] == "ALLOW"
    assert data["ready_for_provider"] is True
    assert "pre-authorized successfully" in data["status_message"].lower()


def test_preauth_medium_risk_review(client, auth_headers):
    """Verify MEDIUM risk payment request results in REVIEW decision."""
    payload = {
        "customer_id": "CUST-PAY-MED",
        "amount": 350.0,  # 3.5x historical average
        "currency": "USD",
        "merchant_name": "Electronics Hub",
        "merchant_category": "electronics",
        "device_type": "mobile_android",  # New device
        "location": "CA",
        "transaction_country": "US",
        "transaction_type": "online_payment",
        "transaction_hour": 14,
        "failed_attempts": 1,
    }

    response = client.post("/api/v1/payment/initiate", json=payload, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()

    assert data["customer_id"] == "CUST-PAY-MED"
    assert data["decision"] == "REVIEW"
    assert data["risk_level"] == "MEDIUM"
    assert 31 <= data["risk_score"] <= 70
    assert data["ready_for_provider"] is False


def test_preauth_high_risk_block(client, auth_headers):
    """Verify HIGH risk payment request results in BLOCK decision and triggered rules."""
    payload = {
        "customer_id": "CUST-PAY-HIGH",
        "amount": 5500.0,  # 55x historical average
        "currency": "USD",
        "merchant_name": "Offshore Crypto Exchange",
        "merchant_category": "crypto",
        "device_type": "tor_browser_linux",  # Unknown device
        "location": "Nigeria",  # Foreign region
        "transaction_country": "NG",  # Foreign cross-border
        "transaction_type": "online_payment",
        "failed_attempts": 4,  # High auth failures
    }

    response = client.post("/api/v1/payment/initiate", json=payload, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()

    assert data["customer_id"] == "CUST-PAY-HIGH"
    assert data["decision"] == "BLOCK"
    assert data["risk_level"] == "HIGH"
    assert data["risk_score"] >= 71
    assert data["ready_for_provider"] is False
    assert len(data["triggered_rules"]) >= 1

    assert any(r["rule_name"] == "Preceding Authentication Failure Burst" or "Takeover" in r["rule_name"] for r in data["triggered_rules"])


def test_preauth_cold_start_neutral(client, auth_headers):
    """Verify brand new cold-start customer with standard transaction is ALLOWed."""
    payload = {
        "customer_id": "CUST-BRAND-NEW-99",
        "amount": 65.0,
        "currency": "USD",
        "merchant_name": "Coffee Roasters",
        "merchant_category": "dining",
        "device_type": "web",
        "location": "US",
        "transaction_country": "US",
        "transaction_type": "online_payment",
        "failed_attempts": 0,
    }

    response = client.post("/api/v1/payment/initiate", json=payload, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()

    assert data["is_cold_start"] is True
    assert data["decision"] == "ALLOW"
    assert data["risk_level"] == "LOW"
    assert data["ready_for_provider"] is True


def test_preauth_unauthorized_rejected(client):
    """Verify unauthenticated request is rejected with 401."""
    response = client.post("/api/v1/payment/initiate", json={"customer_id": "CUST-01", "amount": 10.0})
    assert response.status_code == 401
