"""End-to-end integration tests for Phase 1 & Phase 2: Transaction & Payment Simulation Lifecycle."""

import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.main import app
from backend.app.core.database import Base, get_db
from backend.app.models.user import User
from backend.app.models.customer import Customer
from backend.app.models.transaction import Transaction
from backend.app.models.beneficiary import Beneficiary
from backend.app.models.device import CustomerDevice
from backend.app.models.approval import TransactionApproval, ApprovalStatus
from backend.app.models.payment_intent import PaymentIntent, PaymentLifecycleStatus
from backend.app.models.audit_log import AuditLog
from backend.app.core.security import get_password_hash, create_access_token
from backend.app.schemas.user import UserRole
from backend.app.services.state_transition_validator import StateTransitionValidator, StateTransitionError

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
def setup_test_db():
    app.dependency_overrides[get_db] = override_get_db
    Base.metadata.create_all(bind=test_engine)
    db = TestingSessionLocal()

    # Create test user
    user = User(
        name="Fintech User",
        email="user_sim@test.internal",
        password_hash=get_password_hash("SimPass123!"),
        role=UserRole.FRAUD_INVESTIGATOR.value,
        is_active=True,
    )
    db.add(user)
    db.flush()

    # Create test customer with $50,000 balance
    cust = Customer(
        customer_id="CUST-SIM-001",
        account_age_days=180,
        simulated_balance=50000.0,
        currency="USD",
    )
    db.add(cust)

    # Seed known beneficiary
    bene = Beneficiary(
        customer_id="CUST-SIM-001",
        beneficiary_name="Whole Foods Market",
        category="grocery",
        is_trusted=True,
        total_transfers=5,
    )
    db.add(bene)

    # Seed known device
    dev = CustomerDevice(
        customer_id="CUST-SIM-001",
        device_identifier="dev-web-chrome",
        device_type="web",
        is_trusted=True,
    )
    db.add(dev)

    # Seed 5 baseline transactions
    for i in range(5):
        t = Transaction(
            transaction_id=f"TX-BASE-{i}",
            customer_id="CUST-SIM-001",
            amount=50.0 + (i * 10),
            transaction_hour=14,
            merchant_category="grocery",
            transaction_country="US",
            geo_location_region="CA",
            device_type="web",
            transaction_type="online_payment",
            beneficiary="Whole Foods Market",
            status="SUCCESS",
            fraud_probability=0.03,
            prediction=0,
            risk_score=10.0,
            risk_level="LOW",
            created_at=datetime.now(timezone.utc) - timedelta(days=5 - i),
        )
        db.add(t)

    db.commit()
    db.close()
    yield
    Base.metadata.drop_all(bind=test_engine)
    app.dependency_overrides.pop(get_db, None)


@pytest.fixture
def auth_client():
    token = create_access_token(subject="1", role=UserRole.FRAUD_INVESTIGATOR.value)
    client = TestClient(app)
    client.headers = {"Authorization": f"Bearer {token}"}
    return client


def test_scenario_1_normal_transaction_proceeds_and_deducts_balance(auth_client):
    """Scenario 1: Low-risk routine payment proceeds immediately and reduces simulated balance."""
    payload = {
        "customer_id": "CUST-SIM-001",
        "amount": 45.0,
        "currency": "USD",
        "merchant_name": "Whole Foods Market",
        "merchant_category": "grocery",
        "beneficiary_name": "Whole Foods Market",
        "payment_method": "credit_card",
        "device_type": "web",
        "location": "CA",
        "transaction_country": "US",
        "transaction_type": "online_payment",
        "failed_attempts": 0,
    }
    res = auth_client.post("/api/v1/payment/initiate", json=payload)
    assert res.status_code == 200
    data = res.json()

    assert data["decision"] == "ALLOW"
    assert data["risk_level"] == "LOW"
    assert data["risk_score"] <= 30
    assert data["lifecycle_status"] in ("SUCCEEDED", "SUCCESS")
    assert data["ready_for_provider"] is True
    assert data["verification_required"] is False
    assert data["simulated_balance_after"] == data["simulated_balance_before"] - 45.0

    # Verify balance in database
    db = TestingSessionLocal()
    c = db.query(Customer).filter(Customer.customer_id == "CUST-SIM-001").first()
    assert c.simulated_balance == 50000.0 - 45.0
    db.close()


def test_scenario_2_suspicious_transaction_enters_verification_and_approves(auth_client):
    """Scenario 2: Suspicious transfer flags for verification, holds balance, and deducts on user approval."""
    payload = {
        "customer_id": "CUST-SIM-001",
        "amount": 2500.0,
        "currency": "USD",
        "merchant_name": "New International Broker",
        "merchant_category": "crypto",
        "beneficiary_name": "New International Broker",
        "payment_method": "credit_card",
        "device_type": "mobile_android",
        "location": "Dubai",
        "transaction_country": "AE",
        "transaction_type": "online_payment",
        "failed_attempts": 1,
    }
    res = auth_client.post("/api/v1/payment/initiate", json=payload)
    assert res.status_code == 200
    data = res.json()

    assert data["decision"] == "REVIEW"
    assert data["risk_level"] in ("MEDIUM", "HIGH")
    assert data["risk_score"] >= 31
    assert data["lifecycle_status"] in ("PENDING_APPROVAL", "REVIEW_REQUIRED")
    assert data["verification_required"] is True
    assert data["approval_id"] is not None

    approval_id = data["approval_id"]

    # Verify balance is HELD (not yet deducted)
    db = TestingSessionLocal()
    c = db.query(Customer).filter(Customer.customer_id == "CUST-SIM-001").first()
    bal_held = c.simulated_balance
    db.close()

    # User Step-Up Approval
    app_res = auth_client.post(f"/api/v1/payment/approvals/{approval_id}/approve")
    assert app_res.status_code == 200
    app_data = app_res.json()

    assert app_data["status"] == "APPROVED"
    assert app_data["lifecycle_status"] == "SUCCEEDED"
    assert app_data["simulated_balance"] == bal_held - 2500.0

    # Verify balance was now deducted
    db = TestingSessionLocal()
    c = db.query(Customer).filter(Customer.customer_id == "CUST-SIM-001").first()
    assert c.simulated_balance == bal_held - 2500.0

    # Verify new beneficiary was learned
    bene = db.query(Beneficiary).filter(
        Beneficiary.customer_id == "CUST-SIM-001",
        Beneficiary.beneficiary_name == "New International Broker",
    ).first()
    assert bene is not None
    db.close()


def test_scenario_2b_suspicious_transaction_rejected_prevents_deduction(auth_client):
    """Scenario 2b: Rejected verification blocks transaction and protects simulated balance."""
    db = TestingSessionLocal()
    c = db.query(Customer).filter(Customer.customer_id == "CUST-SIM-001").first()
    bal_before = c.simulated_balance
    db.close()

    payload = {
        "customer_id": "CUST-SIM-001",
        "amount": 1800.0,
        "currency": "USD",
        "merchant_name": "Suspicious Merchant LLC",
        "merchant_category": "luxury_goods",
        "beneficiary_name": "Suspicious Merchant LLC",
        "payment_method": "credit_card",
        "device_type": "mobile_android",
        "location": "Singapore",
        "transaction_country": "SG",
        "transaction_type": "online_payment",
        "failed_attempts": 1,
    }
    res = auth_client.post("/api/v1/payment/initiate", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["decision"] == "REVIEW"
    approval_id = data["approval_id"]

    # User Rejects
    rej_res = auth_client.post(f"/api/v1/payment/approvals/{approval_id}/reject")
    assert rej_res.status_code == 200
    rej_data = rej_res.json()
    assert rej_data["status"] == "REJECTED"
    assert rej_data["lifecycle_status"] == "BLOCKED"

    # Verify balance NOT deducted
    db = TestingSessionLocal()
    c = db.query(Customer).filter(Customer.customer_id == "CUST-SIM-001").first()
    assert c.simulated_balance == bal_before
    db.close()


def test_scenario_3_critical_takeover_immediately_blocked(auth_client):
    """Scenario 3: Severe risk transaction is immediately blocked with zero balance deduction."""
    db = TestingSessionLocal()
    c = db.query(Customer).filter(Customer.customer_id == "CUST-SIM-001").first()
    bal_before = c.simulated_balance
    db.close()

    payload = {
        "customer_id": "CUST-SIM-001",
        "amount": 6800.0,
        "currency": "USD",
        "merchant_name": "Apex Luxury Bullion",
        "merchant_category": "luxury_goods",
        "payment_method": "credit_card",
        "device_type": "unknown_bot",
        "location": "Lagos",
        "transaction_country": "NG",
        "transaction_type": "online_payment",
        "failed_attempts": 4,
    }
    res = auth_client.post("/api/v1/payment/initiate", json=payload)
    assert res.status_code == 200
    data = res.json()

    assert data["decision"] == "BLOCK"
    assert data["risk_level"] == "HIGH"
    assert data["risk_score"] >= 80
    assert data["lifecycle_status"] == "BLOCKED"
    assert data["ready_for_provider"] is False

    # Balance protected
    db = TestingSessionLocal()
    c = db.query(Customer).filter(Customer.customer_id == "CUST-SIM-001").first()
    assert c.simulated_balance == bal_before
    db.close()


def test_insufficient_wallet_balance_rejection(auth_client):
    """Attempting a transaction higher than simulated wallet balance raises 400 Bad Request."""
    payload = {
        "customer_id": "CUST-SIM-001",
        "amount": 999999.0,
        "currency": "USD",
        "merchant_name": "Mega Store",
    }
    res = auth_client.post("/api/v1/payment/initiate", json=payload)
    assert res.status_code == 400
    assert "Insufficient funds in simulated wallet" in res.json()["detail"]


def test_duplicate_approval_replay_protection(auth_client):
    """Attempting to re-approve an already resolved challenge is rejected with 409 Conflict."""
    payload = {
        "customer_id": "CUST-SIM-001",
        "amount": 600.0,
        "currency": "USD",
        "merchant_name": "Novel Tech Inc",
        "device_type": "mobile_android",
        "location": "Tokyo",
        "transaction_country": "JP",
    }
    res = auth_client.post("/api/v1/payment/initiate", json=payload)
    data = res.json()
    approval_id = data["approval_id"]

    # First approval succeeds
    r1 = auth_client.post(f"/api/v1/payment/approvals/{approval_id}/approve")
    assert r1.status_code == 200

    # Second approval attempt fails safely
    r2 = auth_client.post(f"/api/v1/payment/approvals/{approval_id}/approve")
    assert r2.status_code == 409
    assert "already been resolved" in r2.json()["detail"]


def test_state_transition_validator_prohibits_illegal_jumps():
    """Validates that illegal transitions (e.g. BLOCKED -> SUCCEEDED) raise StateTransitionError."""
    with pytest.raises(StateTransitionError):
        StateTransitionValidator.enforce_transition("BLOCKED", "SUCCEEDED")

    with pytest.raises(StateTransitionError):
        StateTransitionValidator.enforce_transition("EXPIRED", "AUTHORIZED")

    # Valid transitions succeed
    valid, _ = StateTransitionValidator.validate_transition("PENDING_APPROVAL", "APPROVED")
    assert valid is True

    valid, _ = StateTransitionValidator.validate_transition("APPROVED", "SUCCEEDED")
    assert valid is True
