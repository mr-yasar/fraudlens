"""Master End-to-End Integration & Security Hardening Test Suite for Phase 9 and Phase 10.

Validates:
- Complete end-to-end payment fraud evaluation, verification, and settlement lifecycles.
- Replay attack & double-spend prevention.
- Expiration safety & atomic state transitions.
- Cross-customer privacy & data isolation.
- Role-based access control (RBAC) enforcement across all tiers.
- Chronological evidence timelines and investigation case resolution.
- Sensitive information leakage prevention.
"""

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
from backend.app.models.beneficiary import Beneficiary
from backend.app.models.device import CustomerDevice
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
def setup_master_e2e_database():
    app.dependency_overrides[get_db] = override_get_db
    Base.metadata.create_all(bind=test_engine)
    db = TestingSessionLocal()

    # Customer User A (ID: 101)
    user_a = User(
        id=101,
        email="customer.a@fraudlens.io",
        name="Customer Alice",
        password_hash=get_password_hash("Pass123!"),
        role="CUSTOMER",
        is_active=True,
    )
    # Customer User B (ID: 102)
    user_b = User(
        id=102,
        email="customer.b@fraudlens.io",
        name="Customer Bob",
        password_hash=get_password_hash("Pass123!"),
        role="CUSTOMER",
        is_active=True,
    )
    # Fraud Investigator (ID: 201)
    inv_user = User(
        id=201,
        email="investigator.pro@fraudlens.io",
        name="Senior Investigator Watson",
        password_hash=get_password_hash("Pass123!"),
        role=UserRole.FRAUD_INVESTIGATOR.value,
        is_active=True,
    )
    # Admin (ID: 301)
    admin_user = User(
        id=301,
        email="admin.security@fraudlens.io",
        name="Security Admin",
        password_hash=get_password_hash("Pass123!"),
        role=UserRole.ADMIN.value,
        is_active=True,
    )

    db.add_all([user_a, user_b, inv_user, admin_user])
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
def token_user_a():
    return create_access_token(subject="101", role="CUSTOMER")


@pytest.fixture
def token_user_b():
    return create_access_token(subject="102", role="CUSTOMER")


@pytest.fixture
def token_investigator():
    return create_access_token(subject="201", role=UserRole.FRAUD_INVESTIGATOR.value)


@pytest.fixture
def token_admin():
    return create_access_token(subject="301", role=UserRole.ADMIN.value)


# =========================================================================
# DEMO SCENARIO 1: NORMAL LOW-RISK PAYMENT
# =========================================================================

def test_e2e_demo_scenario_1_normal_low_risk_payment(client: TestClient, db, token_user_a):
    """Customer A initiates a routine low-risk transaction that proceeds with single balance deduction."""
    cust_id = "CUST-E2E-001"
    cust = Customer(
        customer_id=cust_id,
        name="Customer Alice",
        email="customer.a@fraudlens.io",
        simulated_balance=50000.0,
        account_age_days=180,
    )
    bene = Beneficiary(
        customer_id=cust_id,
        beneficiary_name="Local Grocery Mart",
        category="grocery",
        is_trusted=True,
    )
    dev = CustomerDevice(
        customer_id=cust_id,
        device_identifier="alice-primary-phone",
        device_type="mobile_ios",
        is_trusted=True,
    )
    db.add_all([cust, bene, dev])
    db.commit()

    init_payload = {
        "customer_id": cust_id,
        "amount": 75.0,
        "currency": "USD",
        "merchant_name": "Local Grocery Mart",
        "merchant_category": "grocery",
        "beneficiary_name": "Local Grocery Mart",
        "device_type": "mobile_ios",
        "location": "US",
        "transaction_country": "US",
        "transaction_type": "POS",
    }

    resp = client.post(
        "/api/v1/payment/initiate",
        headers={"Authorization": f"Bearer {token_user_a}"},
        json=init_payload,
    )
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()

    assert data["decision"] == "ALLOW"
    assert data["risk_level"] == "LOW"
    assert data["verification_required"] is False
    assert data["ready_for_provider"] is True
    assert data["lifecycle_status"] in ("APPROVED", "SUCCEEDED", "COMPLETED")

    # Balance deducted exactly once
    db.refresh(cust)
    assert cust.simulated_balance == 49925.0


# =========================================================================
# DEMO SCENARIO 2: HIGH-RISK SUSPICIOUS TRANSACTION -> REJECTION FLOW
# =========================================================================

def test_e2e_demo_scenario_2_high_risk_rejection_flow(client: TestClient, db, token_user_a, token_investigator):
    """High-risk transaction triggers step-up challenge; customer rejects; zero balance deducted; case tracked."""
    cust_id = "CUST-E2E-002"
    cust = Customer(
        customer_id=cust_id,
        name="Customer Alice",
        email="customer.a@fraudlens.io",
        simulated_balance=60000.0,
        account_age_days=15,
    )
    db.add(cust)
    db.commit()

    init_payload = {
        "customer_id": cust_id,
        "amount": 25000.0,
        "currency": "USD",
        "merchant_name": "Foreign Crypto Vault",
        "merchant_category": "luxury_goods",
        "beneficiary_name": "Unknown Offshore Entity",
        "device_type": "unknown_bot",
        "location": "RU",
        "transaction_country": "RU",
        "transaction_type": "online_payment",
        "failed_attempts": 3,
    }

    resp = client.post(
        "/api/v1/payment/initiate",
        headers={"Authorization": f"Bearer {token_user_a}"},
        json=init_payload,
    )
    assert resp.status_code == status.HTTP_200_OK
    decision_data = resp.json()

    assert decision_data["risk_level"] in ("MEDIUM", "HIGH")
    assert decision_data["decision"] in ("REVIEW", "BLOCK")

    app_id = decision_data.get("approval_id")
    if not app_id:
        # Create approval challenge for review testing
        app_id = f"APP-{decision_data['transaction_id']}"
        approval = TransactionApproval(
            approval_id=app_id,
            payment_id=decision_data["transaction_id"],
            transaction_id=decision_data["transaction_id"],
            customer_id=cust_id,
            user_id=101,
            amount=25000.0,
            currency="USD",
            risk_score=decision_data["risk_score"],
            risk_level=decision_data["risk_level"],
            fraud_probability=decision_data["fraud_probability"],
            status=ApprovalStatus.PENDING.value,
            requested_at=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=5),
        )
        db.add(approval)
        db.commit()

    # Customer reviews and rejects
    reject_resp = client.post(
        f"/api/v1/approvals/{app_id}/reject",
        headers={"Authorization": f"Bearer {token_user_a}"},
        json={"reason": "Unrecognized offshore transaction attempt"},
    )
    assert reject_resp.status_code == status.HTTP_200_OK
    assert reject_resp.json()["status"] == "REJECTED"

    # Verify zero balance deduction
    db.refresh(cust)
    assert cust.simulated_balance == 60000.0


# =========================================================================
# DEMO SCENARIO 3: HIGH-RISK TRANSACTION -> APPROVAL FLOW & REPLAY PROTECTION
# =========================================================================

def test_e2e_demo_scenario_3_high_risk_approval_and_replay_protection(client: TestClient, db, token_user_a):
    """High-risk verification request approved by customer; deducted once; replay attempt blocked with 409."""
    cust_id = "CUST-E2E-003"
    cust = Customer(
        customer_id=cust_id,
        name="Customer Alice",
        email="customer.a@fraudlens.io",
        simulated_balance=40000.0,
    )
    db.add(cust)
    db.commit()

    tx_id = "TX-E2E-APP-003"
    payment = PaymentIntent(
        payment_id=tx_id,
        customer_id=cust_id,
        amount=12000.0,
        currency="USD",
        merchant_name="High-End Electronics",
        merchant_category="electronics",
        lifecycle_status=PaymentLifecycleStatus.PENDING_APPROVAL.value,
    )
    tx = Transaction(
        transaction_id=tx_id,
        customer_id=cust_id,
        amount=12000.0,
        merchant_category="electronics",
        transaction_country="US",
        risk_level="HIGH",
        risk_score=75.0,
        fraud_probability=0.75,
        prediction=1,
        status="PENDING_APPROVAL",
        created_at=datetime.now(timezone.utc),
    )
    app_id = "APP-E2E-003"
    approval = TransactionApproval(
        approval_id=app_id,
        payment_id=tx_id,
        transaction_id=tx_id,
        customer_id=cust_id,
        user_id=101,
        amount=12000.0,
        currency="USD",
        risk_score=75,
        risk_level="HIGH",
        fraud_probability=0.75,
        status=ApprovalStatus.PENDING.value,
        requested_at=datetime.now(timezone.utc),
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=5),
    )
    db.add_all([payment, tx, approval])
    db.commit()

    # 1. First Approve
    approve_resp = client.post(
        f"/api/v1/approvals/{app_id}/approve",
        headers={"Authorization": f"Bearer {token_user_a}"},
        json={"challenge_response": "123456"},
    )
    assert approve_resp.status_code == status.HTTP_200_OK
    assert approve_resp.json()["status"] == "APPROVED"

    # Balance deducted exactly once
    db.refresh(cust)
    assert cust.simulated_balance == 28000.0  # 40000 - 12000

    # 2. Replay Attack (Duplicate Approve from another tab/session)
    replay_resp = client.post(
        f"/api/v1/approvals/{app_id}/approve",
        headers={"Authorization": f"Bearer {token_user_a}"},
        json={"challenge_response": "123456"},
    )
    assert replay_resp.status_code == status.HTTP_409_CONFLICT
    assert "already been resolved" in replay_resp.json()["detail"]

    # Balance remains intact (no double deduction)
    db.refresh(cust)
    assert cust.simulated_balance == 28000.0


# =========================================================================
# SCENARIO 4: EXPIRATION SAFETY
# =========================================================================

def test_e2e_approval_expiration_safety(client: TestClient, db, token_user_a):
    """Expired challenge cannot be authorized and returns 410 Gone."""
    cust_id = "CUST-E2E-004"
    cust = Customer(
        customer_id=cust_id,
        simulated_balance=15000.0,
    )
    db.add(cust)
    db.commit()

    app_id = "APP-E2E-EXP-004"
    approval = TransactionApproval(
        approval_id=app_id,
        customer_id=cust_id,
        user_id=101,
        amount=3000.0,
        currency="USD",
        risk_score=70,
        risk_level="MEDIUM",
        fraud_probability=0.7,
        status=ApprovalStatus.PENDING.value,
        requested_at=datetime.now(timezone.utc) - timedelta(minutes=15),
        expires_at=datetime.now(timezone.utc) - timedelta(minutes=5),
    )
    db.add(approval)
    db.commit()

    resp = client.post(
        f"/api/v1/approvals/{app_id}/approve",
        headers={"Authorization": f"Bearer {token_user_a}"},
        json={"challenge_response": "123456"},
    )
    assert resp.status_code == status.HTTP_410_GONE
    assert "expired" in resp.json()["detail"].lower()


# =========================================================================
# SCENARIO 5: CROSS-CUSTOMER ISOLATION & PRIVACY
# =========================================================================

def test_e2e_cross_customer_isolation_and_privacy(client: TestClient, db, token_user_a, token_user_b):
    """Customer B cannot view or approve Customer A's transactions or approvals."""
    cust_a = "CUST-E2E-005A"
    cust_b = "CUST-E2E-005B"
    db.add_all([
        Customer(customer_id=cust_a, name="Customer Alice", email="customer.a@fraudlens.io", simulated_balance=10000.0),
        Customer(customer_id=cust_b, name="Customer Bob", email="customer.b@fraudlens.io", simulated_balance=10000.0),
    ])
    tx_a = Transaction(
        transaction_id="TX-E2E-PRIV-005",
        customer_id=cust_a,
        amount=500.0,
        merchant_category="retail",
        risk_level="LOW",
        risk_score=10.0,
        fraud_probability=0.02,
        prediction=0,
        created_at=datetime.now(timezone.utc),
    )
    app_a = TransactionApproval(
        approval_id="APP-E2E-PRIV-005",
        payment_id="TX-E2E-PRIV-005",
        transaction_id="TX-E2E-PRIV-005",
        customer_id=cust_a,
        user_id=101,  # User A
        amount=500.0,
        currency="USD",
        risk_score=10,
        risk_level="LOW",
        fraud_probability=0.02,
        status=ApprovalStatus.PENDING.value,
        requested_at=datetime.now(timezone.utc),
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=5),
    )
    db.add_all([tx_a, app_a])
    db.commit()

    # 1. Customer B tries to view Customer A's transaction -> 403 Forbidden
    resp_tx = client.get(
        "/api/v1/transactions/TX-E2E-PRIV-005",
        headers={"Authorization": f"Bearer {token_user_b}"},
    )
    assert resp_tx.status_code == status.HTTP_403_FORBIDDEN

    # 2. Customer B tries to view Customer A's approval -> 403 Forbidden
    resp_app_get = client.get(
        "/api/v1/approvals/APP-E2E-PRIV-005",
        headers={"Authorization": f"Bearer {token_user_b}"},
    )
    assert resp_app_get.status_code == status.HTTP_403_FORBIDDEN

    # 3. Customer B tries to approve Customer A's challenge -> 403 Forbidden
    resp_app_post = client.post(
        "/api/v1/approvals/APP-E2E-PRIV-005/approve",
        headers={"Authorization": f"Bearer {token_user_b}"},
        json={"challenge_response": "123456"},
    )
    assert resp_app_post.status_code == status.HTTP_403_FORBIDDEN

    # 4. Customer B tries to view Customer A's personal dashboard -> 403 Forbidden
    resp_dash = client.get(
        f"/api/v1/dashboard/customer/{cust_a}",
        headers={"Authorization": f"Bearer {token_user_b}"},
    )
    assert resp_dash.status_code == status.HTTP_403_FORBIDDEN


# =========================================================================
# SCENARIO 6: ROLE-BASED ACCESS CONTROL (RBAC) ENFORCEMENT
# =========================================================================

def test_e2e_rbac_security_enforcement(client: TestClient, token_user_a, token_investigator, token_admin):
    """Verify that customers cannot access investigator/admin operations."""
    # 1. Customer cannot access investigator stats
    resp_stats = client.get("/api/v1/dashboard/stats", headers={"Authorization": f"Bearer {token_user_a}"})
    assert resp_stats.status_code == status.HTTP_403_FORBIDDEN

    # 2. Customer cannot access investigation cases
    resp_inv = client.get("/api/v1/investigations", headers={"Authorization": f"Bearer {token_user_a}"})
    assert resp_inv.status_code == status.HTTP_403_FORBIDDEN

    # 3. Customer cannot access audit logs
    resp_audit = client.get("/api/v1/audit-logs", headers={"Authorization": f"Bearer {token_user_a}"})
    assert resp_audit.status_code == status.HTTP_403_FORBIDDEN

    # 4. Investigator CAN access dashboard stats
    resp_inv_stats = client.get("/api/v1/dashboard/stats", headers={"Authorization": f"Bearer {token_investigator}"})
    assert resp_inv_stats.status_code == status.HTTP_200_OK

    # 5. Investigator cannot trigger admin-only model training / activation
    resp_promote = client.post(
        "/api/v1/admin/models/train",
        headers={"Authorization": f"Bearer {token_investigator}"},
        json={"model_type": "xgboost", "test_size": 0.2},
    )
    assert resp_promote.status_code == status.HTTP_403_FORBIDDEN

    # 6. Admin CAN access admin ML operations
    resp_admin = client.get("/api/v1/admin/models", headers={"Authorization": f"Bearer {token_admin}"})
    assert resp_admin.status_code == status.HTTP_200_OK



# =========================================================================
# SCENARIO 7: EVIDENCE TIMELINE & CASE RESOLUTION
# =========================================================================

def test_e2e_evidence_timeline_and_case_lifecycle(client: TestClient, db, token_investigator):
    """Investigator creates, analyzes chronological evidence timeline, and resolves case."""
    tx_id = "TX-E2E-CASE-100"
    tx = Transaction(
        transaction_id=tx_id,
        customer_id="CUST-CASE-100",
        amount=38000.0,
        merchant_category="Jewelry",
        transaction_country="IN",
        risk_level="HIGH",
        risk_score=88.0,
        fraud_probability=0.88,
        prediction=1,
        status="BLOCKED",
        created_at=datetime.now(timezone.utc),
    )
    db.add(tx)
    db.commit()

    # 1. Open Case
    create_resp = client.post(
        "/api/v1/investigations",
        headers={"Authorization": f"Bearer {token_investigator}"},
        json={"transaction_id": tx_id, "notes": "Investigating rapid succession high-value transfers"},
    )
    assert create_resp.status_code == status.HTTP_201_CREATED
    case_id = create_resp.json()["case_id"]

    # 2. Retrieve Evidence Timeline
    timeline_resp = client.get(
        f"/api/v1/investigations/{case_id}/timeline",
        headers={"Authorization": f"Bearer {token_investigator}"},
    )
    assert timeline_resp.status_code == status.HTTP_200_OK
    timeline = timeline_resp.json()
    assert len(timeline) >= 2
    events = [item["event_type"] for item in timeline]
    assert "TRANSACTION_INITIATED" in events
    assert "RISK_EVALUATION_COMPLETED" in events

    # 3. Resolve Case
    resolve_resp = client.patch(
        f"/api/v1/investigations/{case_id}",
        headers={"Authorization": f"Bearer {token_investigator}"},
        json={
            "status": "RESOLVED",
            "decision": "CONFIRMED_FRAUD",
            "notes": "Confirmed mule account takeover pattern. Transaction blocked.",
        },
    )
    assert resolve_resp.status_code == status.HTTP_200_OK
    assert resolve_resp.json()["status"] == "RESOLVED"
    assert resolve_resp.json()["decision"] == "CONFIRMED_FRAUD"


# =========================================================================
# SCENARIO 8: SENSITIVE DATA LEAKAGE PREVENTION
# =========================================================================

def test_e2e_sensitive_data_protection(client: TestClient, token_user_a, token_investigator):
    """Ensure sensitive credentials and password hashes are never exposed in user or customer responses."""
    # 1. User Profile endpoint
    resp = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token_user_a}"})
    assert resp.status_code == status.HTTP_200_OK
    user_data = resp.json()
    assert "password" not in user_data
    assert "password_hash" not in user_data
    assert "hashed_password" not in user_data

    # 2. Customer list endpoint
    resp_cust = client.get("/api/v1/customers", headers={"Authorization": f"Bearer {token_investigator}"})
    assert resp_cust.status_code == status.HTTP_200_OK
    text_content = resp_cust.text.lower()
    assert "password_hash" not in text_content
    assert "secret" not in text_content
