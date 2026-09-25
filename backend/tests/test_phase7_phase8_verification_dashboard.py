"""Comprehensive integration tests for Phase 7 (Real-Time Verification) & Phase 8 (Dashboard & Investigation Intelligence)."""

from datetime import datetime, timedelta, timezone
import json
import pytest
from fastapi import status
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
from backend.app.models.approval import TransactionApproval, ApprovalStatus
from backend.app.models.investigation import Investigation
from backend.app.models.payment_intent import PaymentIntent, PaymentLifecycleStatus
from backend.app.schemas.user import UserRole
from backend.app.services.notification_service import (
    NotificationService,
    NotificationPayload,
    NotificationChannel,
    NotificationType,
)

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
def setup_app_and_database():
    app.dependency_overrides[get_db] = override_get_db
    Base.metadata.create_all(bind=test_engine)
    db = TestingSessionLocal()

    # Seed regular customer user (ID: 1)
    cust_user = User(
        id=1,
        email="alice.verify@example.com",
        name="Alice Verification",
        password_hash=get_password_hash("Secret123!"),
        role="CUSTOMER",
        is_active=True,
    )
    # Seed investigator user (ID: 2)
    inv_user = User(
        id=2,
        email="investigator@fraudlens.io",
        name="Inspector Sherlock",
        password_hash=get_password_hash("Secret123!"),
        role=UserRole.FRAUD_INVESTIGATOR.value,
        is_active=True,
    )
    # Seed admin user (ID: 3)
    admin_user = User(
        id=3,
        email="admin@fraudlens.io",
        name="Admin Chief",
        password_hash=get_password_hash("Secret123!"),
        role=UserRole.ADMIN.value,
        is_active=True,
    )

    db.add_all([cust_user, inv_user, admin_user])
    db.commit()
    db.close()
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def db():
    database = TestingSessionLocal()
    try:
        yield database
    finally:
        database.close()


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def customer_token():
    return create_access_token(subject="1", role="CUSTOMER")


@pytest.fixture
def investigator_token():
    return create_access_token(subject="2", role=UserRole.FRAUD_INVESTIGATOR.value)



@pytest.fixture
def auth_headers(investigator_token):
    return {"Authorization": f"Bearer {investigator_token}"}


def test_phase7_step_up_approval_lifecycle_approve(client: TestClient, db, customer_token):
    """Test full Phase 7 verification lifecycle: Pending -> Approve -> Balance Deducted Once -> Replay Protected."""
    cust_id = "CUST-P7-001"
    cust = Customer(
        customer_id=cust_id,
        name="Alice Verification",
        email="alice.verify@example.com",
        simulated_balance=50000.0,
        currency="USD",
    )
    db.add(cust)
    db.commit()

    tx_id = "TX-P7-APP-001"
    payment = PaymentIntent(
        payment_id=tx_id,
        customer_id=cust_id,
        amount=15000.0,
        currency="USD",
        merchant_name="Wire Transfer Services",
        beneficiary_name="BENEF-9988",
        merchant_category="Wire Transfer",
        lifecycle_status=PaymentLifecycleStatus.PENDING_APPROVAL.value,
    )
    db.add(payment)


    tx = Transaction(
        transaction_id=tx_id,
        customer_id=cust_id,
        amount=15000.0,
        merchant_category="Wire Transfer",
        transaction_country="US",
        risk_level="HIGH",
        risk_score=78.5,
        fraud_probability=0.78,
        prediction=1,
        decision="VERIFY",
        created_at=datetime.now(timezone.utc),
    )
    db.add(tx)

    app_id = "APP-P7-001"
    approval = TransactionApproval(
        approval_id=app_id,
        payment_id=tx_id,
        transaction_id=tx_id,
        customer_id=cust_id,
        user_id=1,
        amount=15000.0,
        currency="USD",
        risk_score=78,
        risk_level="HIGH",
        fraud_probability=0.78,
        status=ApprovalStatus.PENDING.value,
        requested_at=datetime.now(timezone.utc),
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=5),
    )
    db.add(approval)
    db.commit()

    # 2. Customer Approves Challenge via REST
    resp = client.post(
        f"/api/v1/approvals/{app_id}/approve",
        headers={"Authorization": f"Bearer {customer_token}"},
        json={"challenge_response": "123456", "channel": "IN_APP_PUSH"},
    )
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()
    assert data["status"] == "APPROVED"

    # 3. Check Balance Deducted Exactly Once
    db.refresh(cust)
    assert cust.simulated_balance == 35000.0  # 50000 - 15000

    # 4. Replay Attack Protection: Second Approve Must Fail with 409 Conflict
    replay_resp = client.post(
        f"/api/v1/approvals/{app_id}/approve",
        headers={"Authorization": f"Bearer {customer_token}"},
        json={"challenge_response": "123456"},
    )
    assert replay_resp.status_code == status.HTTP_409_CONFLICT
    assert "already been resolved" in replay_resp.json()["detail"]

    # Ensure no double deduction
    db.refresh(cust)
    assert cust.simulated_balance == 35000.0


def test_phase7_step_up_approval_lifecycle_reject(client: TestClient, db, customer_token):
    """Test verification rejection: Pending -> Reject -> Payment Blocked -> Zero Balance Deduction."""
    cust_id = "CUST-P7-002"
    cust = Customer(
        customer_id=cust_id,
        name="Bob Reject",
        email="bob.reject@example.com",
        simulated_balance=30000.0,
        currency="USD",
    )
    db.add(cust)
    db.commit()

    tx_id = "TX-P7-REJ-002"
    payment = PaymentIntent(
        payment_id=tx_id,
        customer_id=cust_id,
        amount=8000.0,
        currency="USD",
        merchant_name="Online Store",
        beneficiary_name="BENEF-UNKNOWN",
        merchant_category="Online Shopping",
        lifecycle_status=PaymentLifecycleStatus.PENDING_APPROVAL.value,
    )
    db.add(payment)


    app_id = "APP-P7-002"
    approval = TransactionApproval(
        approval_id=app_id,
        payment_id=tx_id,
        transaction_id=tx_id,
        customer_id=cust_id,
        user_id=1,
        amount=8000.0,
        currency="USD",
        risk_score=65,
        risk_level="MEDIUM",
        fraud_probability=0.65,
        status=ApprovalStatus.PENDING.value,
        requested_at=datetime.now(timezone.utc),
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=5),
    )
    db.add(approval)
    db.commit()

    # Reject Challenge
    resp = client.post(
        f"/api/v1/approvals/{app_id}/reject",
        headers={"Authorization": f"Bearer {customer_token}"},
        json={"reason": "Did not recognize merchant"},
    )
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()
    assert data["status"] == "REJECTED"

    # Balance must remain unchanged
    db.refresh(cust)
    assert cust.simulated_balance == 30000.0


def test_phase7_expired_approval_cannot_be_approved(client: TestClient, db, customer_token):
    """Test that an expired approval challenge cannot be approved and returns 410 Gone."""
    cust_id = "CUST-P7-003"
    cust = Customer(
        customer_id=cust_id,
        simulated_balance=20000.0,
    )
    db.add(cust)
    db.commit()

    tx_id = "TX-P7-EXP-003"
    payment = PaymentIntent(
        payment_id=tx_id,
        customer_id=cust_id,
        amount=5000.0,
        currency="USD",
        merchant_name="General Merchant",
        merchant_category="Purchase",
        lifecycle_status=PaymentLifecycleStatus.PENDING_APPROVAL.value,
    )
    db.add(payment)


    app_id = "APP-P7-EXP-003"
    approval = TransactionApproval(
        approval_id=app_id,
        payment_id=tx_id,
        transaction_id=tx_id,
        customer_id=cust_id,
        user_id=1,
        amount=5000.0,
        currency="USD",
        risk_score=70,
        risk_level="MEDIUM",
        fraud_probability=0.7,
        status=ApprovalStatus.PENDING.value,
        requested_at=datetime.now(timezone.utc) - timedelta(minutes=10),
        expires_at=datetime.now(timezone.utc) - timedelta(minutes=5),
    )
    db.add(approval)
    db.commit()

    resp = client.post(
        f"/api/v1/approvals/{app_id}/approve",
        headers={"Authorization": f"Bearer {customer_token}"},
        json={"challenge_response": "123456"},
    )
    assert resp.status_code == status.HTTP_410_GONE
    assert "expired" in resp.json()["detail"].lower()


def test_phase7_unauthorized_user_cannot_approve_other_user_challenge(client: TestClient, db, customer_token):
    """Test that Customer B cannot approve Customer A's challenge."""
    cust_id = "CUST-P7-004"
    cust = Customer(
        customer_id=cust_id,
        simulated_balance=10000.0,
    )
    db.add(cust)
    db.commit()

    app_id = "APP-P7-OTHER-004"
    approval = TransactionApproval(
        approval_id=app_id,
        payment_id="TX-OTHER-004",
        transaction_id="TX-OTHER-004",
        customer_id=cust_id,
        user_id=999,  # Belongs to user 999, not user 1
        amount=1000.0,
        currency="USD",
        risk_score=60,
        risk_level="MEDIUM",
        fraud_probability=0.6,
        status=ApprovalStatus.PENDING.value,
        requested_at=datetime.now(timezone.utc),
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=5),
    )
    db.add(approval)
    db.commit()

    resp = client.post(
        f"/api/v1/approvals/{app_id}/approve",
        headers={"Authorization": f"Bearer {customer_token}"},
        json={"challenge_response": "123456"},
    )
    assert resp.status_code == status.HTTP_403_FORBIDDEN


def test_phase7_notification_service_channels():
    """Test notification dispatcher modularity and resilient execution."""
    dispatcher = NotificationService.get_instance()
    payload = NotificationPayload(
        user_id=1,
        customer_id="CUST-P7-001",
        transaction_id="TX-NOTIF-001",
        approval_id="APP-NOTIF-001",
        notification_type=NotificationType.STEP_UP_CHALLENGE,
        title="Verification Required",
        message="Please verify transaction of $12,000 to John Doe",
        amount=12000.0,
        risk_level="HIGH",
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=5),
    )

    results = dispatcher.dispatch_all(payload, channels=[NotificationChannel.IN_APP_PUSH, NotificationChannel.EMAIL])
    assert len(results) == 2
    assert any(r.channel == NotificationChannel.IN_APP_PUSH for r in results)


def test_phase8_customer_dashboard_overview(client: TestClient, db, customer_token, auth_headers):
    """Test Customer Personal Dashboard endpoint returns real data and enforces privacy."""
    cust_id = "CUST-P8-001"
    cust = Customer(
        customer_id=cust_id,
        name="Alice Verification",
        email="alice.verify@example.com",  # matches user 1
        simulated_balance=45000.0,
        account_age_days=240,
    )
    db.add(cust)

    # Add transactions
    tx1 = Transaction(
        transaction_id="TX-P8-001",
        customer_id=cust_id,
        amount=2500.0,
        merchant_category="Food & Dining",
        transaction_country="US",
        risk_level="LOW",
        risk_score=12.0,
        fraud_probability=0.05,
        prediction=0,
        decision="PROCEED",
        created_at=datetime.now(timezone.utc),
    )
    tx2 = Transaction(
        transaction_id="TX-P8-002",
        customer_id=cust_id,
        amount=18000.0,
        merchant_category="Jewelry",
        transaction_country="US",
        risk_level="HIGH",
        risk_score=85.0,
        fraud_probability=0.85,
        prediction=1,
        decision="BLOCK",
        created_at=datetime.now(timezone.utc),
    )
    db.add_all([tx1, tx2])

    # Add a pending approval
    app = TransactionApproval(
        approval_id="APP-P8-001",
        payment_id="TX-P8-002",
        transaction_id="TX-P8-002",
        customer_id=cust_id,
        user_id=1,
        amount=18000.0,
        currency="USD",
        risk_score=85,
        risk_level="HIGH",
        fraud_probability=0.85,
        status=ApprovalStatus.PENDING.value,
        requested_at=datetime.now(timezone.utc),
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=3),
    )
    db.add(app)
    db.commit()

    # 1. Customer accesses their own dashboard
    resp = client.get(
        f"/api/v1/dashboard/customer/{cust_id}",
        headers={"Authorization": f"Bearer {customer_token}"},
    )
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()
    assert data["customer_id"] == cust_id
    assert data["account_balance"] == 45000.0
    assert data["total_transactions_count"] == 2
    assert data["total_spent_amount"] == 20500.0
    assert data["pending_approvals_count"] == 1
    assert len(data["pending_approvals"]) == 1
    assert data["pending_approvals"][0]["approval_id"] == "APP-P8-001"
    assert data["pending_approvals"][0]["seconds_remaining"] > 0
    assert data["security_summary"]["blocked_transactions_count"] >= 1

    # 2. Privacy Check: Customer cannot access unauthorized customer dashboard
    unauthorized_resp = client.get(
        "/api/v1/dashboard/customer/CUST-UNAUTHORIZED-999",
        headers={"Authorization": f"Bearer {customer_token}"},
    )
    assert unauthorized_resp.status_code == status.HTTP_403_FORBIDDEN

    # 3. Investigator/Admin can inspect any customer's dashboard
    admin_resp = client.get(
        f"/api/v1/dashboard/customer/{cust_id}",
        headers=auth_headers,
    )
    assert admin_resp.status_code == status.HTTP_200_OK


def test_phase8_investigator_dashboard_and_timeline(client: TestClient, db, auth_headers):
    """Test Investigator Command Center stats, case lifecycle, and evidence timeline."""
    # 1. Get Live Command Center Stats
    stats_resp = client.get("/api/v1/dashboard/stats", headers=auth_headers)
    assert stats_resp.status_code == status.HTTP_200_OK
    stats = stats_resp.json()
    assert "total_transactions" in stats
    assert "risk_distribution" in stats
    assert "ai_risk_intelligence" in stats

    # 2. Create Investigation Case
    tx_id = "TX-P8-INV-100"
    tx = Transaction(
        transaction_id=tx_id,
        customer_id="CUST-INV-100",
        amount=45000.0,
        merchant_category="Electronics",
        transaction_country="US",
        risk_level="HIGH",
        risk_score=92.0,
        fraud_probability=0.92,
        prediction=1,
        created_at=datetime.now(timezone.utc),
    )
    db.add(tx)
    db.commit()

    case_resp = client.post(
        "/api/v1/investigations",
        headers=auth_headers,
        json={
            "transaction_id": tx_id,
            "notes": "Suspicious high-value international purchase",
        },
    )
    assert case_resp.status_code == status.HTTP_201_CREATED
    case_data = case_resp.json()
    case_id = case_data["case_id"]

    # 3. Move case to UNDER_REVIEW
    patch_resp = client.patch(
        f"/api/v1/investigations/{case_id}",
        headers=auth_headers,
        json={"status": "UNDER_REVIEW", "notes": "Investigator analyzing velocity signals"},
    )
    assert patch_resp.status_code == status.HTTP_200_OK
    assert patch_resp.json()["status"] == "UNDER_REVIEW"

    # 4. Resolve case with CONFIRMED_FRAUD decision
    resolve_resp = client.patch(
        f"/api/v1/investigations/{case_id}",
        headers=auth_headers,
        json={
            "status": "RESOLVED",
            "decision": "CONFIRMED_FRAUD",
            "notes": "Confirmed account takeover with IP mismatch.",
        },
    )
    assert resolve_resp.status_code == status.HTTP_200_OK
    assert resolve_resp.json()["status"] == "RESOLVED"
    assert resolve_resp.json()["decision"] == "CONFIRMED_FRAUD"

    # 5. Fetch Chronological Evidence Timeline
    timeline_resp = client.get(
        f"/api/v1/investigations/{case_id}/timeline",
        headers=auth_headers,
    )
    assert timeline_resp.status_code == status.HTTP_200_OK
    timeline = timeline_resp.json()
    assert isinstance(timeline, list)
    assert len(timeline) >= 3
    event_types = [e["event_type"] for e in timeline]
    assert "TRANSACTION_INITIATED" in event_types
    assert "RISK_EVALUATION_COMPLETED" in event_types
    assert "INVESTIGATION_CASE_CREATED" in event_types
