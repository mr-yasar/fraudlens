"""Comprehensive Master Test Suite for Phase 5 (Advanced Risk Intelligence & SHAP) and Phase 6 (Central Transaction Decision Engine)."""

import json
import uuid
from datetime import datetime, timezone, timedelta
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
from backend.app.models.approval import TransactionApproval, ApprovalStatus
from backend.app.models.payment_intent import PaymentIntent, PaymentLifecycleStatus
from backend.app.schemas.user import UserRole
from backend.app.schemas.payment import (
    PaymentInitiateRequest,
    PaymentDecision,
    RiskLevelEnum,
)
from backend.app.schemas.prediction import TransactionPredictionInput
from backend.app.services.prediction_service import FraudPredictionService
from backend.app.services.risk_scoring_service import RiskScoringEngine, RiskLevel
from backend.app.services.risk_decision_orchestrator import RiskDecisionOrchestrator
from ml.explainability.feature_metadata import (
    get_feature_display_name,
    format_customer_reason,
    format_investigator_reason,
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
        name="Alice Customer",
        email="alice@test.internal",
        password_hash=get_password_hash("CustomerPass123!"),
        role="CUSTOMER",
        is_active=True,
    )

    # Seed second customer user (ID: 2)
    other_user = User(
        id=2,
        name="Bob Other",
        email="bob@test.internal",
        password_hash=get_password_hash("BobPass123!"),
        role="CUSTOMER",
        is_active=True,
    )

    # Seed fraud investigator user (ID: 3)
    inv_user = User(
        id=3,
        name="Investigator Sarah",
        email="sarah@investigator.internal",
        password_hash=get_password_hash("InvestigatorPass123!"),
        role=UserRole.ADMIN.value,
        is_active=True,
    )

    db.add_all([cust_user, other_user, inv_user])

    # Seed Customers with wallet balances
    c1 = Customer(customer_id="alice@test.internal", simulated_balance=5000.0, account_age_days=180)
    c2 = Customer(customer_id="bob@test.internal", simulated_balance=1000.0, account_age_days=90)
    c_low = Customer(customer_id="CUST-P56-LOW", simulated_balance=10000.0, account_age_days=200)
    c_med = Customer(customer_id="CUST-P56-MED", simulated_balance=10000.0, account_age_days=120)
    c_high = Customer(customer_id="CUST-P56-HIGH", simulated_balance=10000.0, account_age_days=10)

    db.add_all([c1, c2, c_low, c_med, c_high])
    db.commit()

    # Seed baseline transactions for CUST-P56-LOW and CUST-P56-MED (historical mean: $100)
    past_date = datetime.now(timezone.utc) - timedelta(days=3)
    for cid in ["CUST-P56-LOW", "CUST-P56-MED", "alice@test.internal"]:
        tx1 = Transaction(
            transaction_id=f"TX-{cid}-H1",
            customer_id=cid,
            amount=95.0,
            transaction_hour=14,
            merchant_category="retail",
            beneficiary="Local Market",
            transaction_country="US",
            geo_location_region="CA",
            device_type="web",
            transaction_type="online_payment",
            created_at=past_date,
        )
        tx2 = Transaction(
            transaction_id=f"TX-{cid}-H2",
            customer_id=cid,
            amount=105.0,
            transaction_hour=16,
            merchant_category="retail",
            beneficiary="Local Market",
            transaction_country="US",
            geo_location_region="CA",
            device_type="web",
            transaction_type="online_payment",
            created_at=past_date + timedelta(days=1),
        )
        db.add_all([tx1, tx2])

    db.commit()
    db.close()

    yield

    Base.metadata.drop_all(bind=test_engine)
    app.dependency_overrides.clear()


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def alice_auth_headers():
    token = create_access_token(subject=1, role="CUSTOMER")
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def bob_auth_headers():
    token = create_access_token(subject=2, role="CUSTOMER")
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def investigator_auth_headers():
    token = create_access_token(subject=3, role=UserRole.ADMIN.value)
    return {"Authorization": f"Bearer {token}"}


# =========================================================================
# PHASE 5 TESTS: RISK INTELLIGENCE & SHAP EXPLAINABILITY
# =========================================================================

def test_risk_score_independent_from_probability():
    """Verify Risk Score is an independent multi-factor score [0, 100], not simply prob * 100."""
    risk_engine = RiskScoringEngine()

    # Scenario A: Zero probability but high environmental risk signals
    res_a = risk_engine.compute_risk_score(
        fraud_probability=0.0,
        transaction_data={
            "Amount": 5000.0,
            "Average_Previous_Amount": 100.0,  # 50x spike
            "Velocity_1h": 4.0,                 # 4 rapid tx
            "New_Device": 1,
            "is_new_beneficiary": 1,
            "Failed_Attempts": 3,
            "Unusual_Location": 1,
        },
    )
    assert res_a.risk_score > 30  # Should be elevated despite 0.0 model prob
    assert res_a.risk_level in (RiskLevel.MEDIUM, RiskLevel.HIGH)

    # Scenario B: Moderate probability (0.4) but completely benign context
    res_b = risk_engine.compute_risk_score(
        fraud_probability=0.4,
        transaction_data={
            "Amount": 50.0,
            "Average_Previous_Amount": 50.0,
            "Velocity_1h": 0.0,
            "New_Device": 0,
            "is_new_beneficiary": 0,
            "Failed_Attempts": 0,
            "Unusual_Location": 0,
        },
    )
    assert res_b.risk_score <= 30
    assert res_b.risk_level == RiskLevel.LOW


def test_configurable_risk_thresholds():
    """Verify configurable risk scoring threshold bands."""
    initial = RiskScoringEngine.get_thresholds()
    assert initial["low_threshold"] == 30
    assert initial["high_threshold"] == 70

    assert RiskScoringEngine.classify_risk_level(25) == RiskLevel.LOW
    assert RiskScoringEngine.classify_risk_level(45) == RiskLevel.MEDIUM
    assert RiskScoringEngine.classify_risk_level(85) == RiskLevel.HIGH

    # Dynamically update thresholds
    RiskScoringEngine.update_thresholds(low=20, high=60)
    assert RiskScoringEngine.classify_risk_level(25) == RiskLevel.MEDIUM
    assert RiskScoringEngine.classify_risk_level(65) == RiskLevel.HIGH

    # Reset back to standard defaults
    RiskScoringEngine.update_thresholds(low=30, high=70)


def test_feature_metadata_and_human_translations():
    """Verify feature display names and customer/investigator explanations."""
    assert get_feature_display_name("Amount_to_Average_Ratio") == "Amount Baseline Multiplier"
    assert get_feature_display_name("New_Device") == "New Device Hardware"
    assert get_feature_display_name("Velocity_1h") == "1-Hour Transaction Velocity"

    cust_msg = format_customer_reason("New_Device", is_risk_increasing=True)
    assert "unrecognized new device" in cust_msg.lower()

    inv_msg = format_investigator_reason("Amount", 4500.0, 0.35)
    assert "$4500.00" in inv_msg
    assert "increased risk" in inv_msg.lower() or "increased" in inv_msg.lower()


def test_shap_local_explanation_and_direction():
    """Verify SHAP explainer produces genuine feature contributions with direction."""
    service = FraudPredictionService.get_instance()
    tx_input = TransactionPredictionInput(
        Amount=3500.0,
        Transaction_Hour=2,
        Transaction_Type="Transfer",
        Location="Mumbai",
        Usual_Location="Delhi",
        Device_Type="Android",
        New_Device=1,
        Account_Age_Days=20.0,
        Average_Previous_Amount=150.0,
        Transactions_Last_24H=6.0,
        Failed_Attempts=2,
        International_Transaction=1,
    )
    exp = service.explain_transaction(tx_input, top_k=5)
    assert exp.fraud_probability >= 0.0
    assert exp.risk_score >= 0
    assert len(exp.all_attributions) > 0

    # Top attribution must have display name and valid magnitude
    top_attr = exp.all_attributions[0]
    assert top_attr["feature_name"] is not None
    assert top_attr["shap_value"] is not None
    assert top_attr["impact"] in ("INCREASES_FRAUD_RISK", "DECREASES_FRAUD_RISK")


def test_transaction_explanation_api_security(client, alice_auth_headers, bob_auth_headers, investigator_auth_headers):
    """Verify transaction explanation endpoint security: customers can view own, denied others, investigator can view all."""
    db = TestingSessionLocal()
    # Create Alice's transaction
    tx_alice = Transaction(
        transaction_id="TX-ALICE-SEC-01",
        customer_id="alice@test.internal",
        amount=120.0,
        transaction_hour=14,
        merchant_category="retail",
        transaction_country="US",
        geo_location_region="CA",
        device_type="web",
        transaction_type="online_payment",
        fraud_probability=0.15,
        prediction=0,
        risk_score=15.0,
        risk_level="LOW",
    )
    db.add(tx_alice)
    db.commit()
    db.close()

    # 1. Alice retrieves her own transaction explanation -> 200 OK
    res_alice = client.get("/api/v1/transactions/TX-ALICE-SEC-01/explanation", headers=alice_auth_headers)
    assert res_alice.status_code == 200
    assert res_alice.json()["transaction_id"] == "TX-ALICE-SEC-01"

    # 2. Bob attempts to access Alice's transaction explanation -> 403 Forbidden
    res_bob = client.get("/api/v1/transactions/TX-ALICE-SEC-01/explanation", headers=bob_auth_headers)
    assert res_bob.status_code == 403
    assert "Access denied" in res_bob.json()["detail"]

    # 3. Investigator Sarah accesses Alice's transaction explanation -> 200 OK
    res_inv = client.get("/api/v1/transactions/TX-ALICE-SEC-01/explanation", headers=investigator_auth_headers)
    assert res_inv.status_code == 200


# =========================================================================
# PHASE 6 TESTS: CENTRAL DECISION ENGINE & APPROVAL LIFECYCLE
# =========================================================================

def test_central_decision_low_risk_allow_immediate_deduction(client, alice_auth_headers):
    """Verify LOW risk transaction results in ALLOW, status SUCCEEDED, and immediate wallet balance deduction."""
    db = TestingSessionLocal()
    cust = db.query(Customer).filter(Customer.customer_id == "CUST-P56-LOW").first()
    balance_before = float(cust.simulated_balance)
    db.close()

    payload = {
        "customer_id": "CUST-P56-LOW",
        "amount": 95.0,  # Matches historical average of $100
        "currency": "USD",
        "merchant_name": "Local Market",
        "merchant_category": "retail",
        "device_type": "web",
        "location": "CA",
        "transaction_country": "US",
        "transaction_type": "online_payment",
        "failed_attempts": 0,
    }

    response = client.post("/api/v1/payment/initiate", json=payload, headers=alice_auth_headers)
    assert response.status_code == 200
    data = response.json()

    assert data["decision"] == "ALLOW"
    assert data["risk_level"] == "LOW"
    assert data["risk_score"] <= 30
    assert data["ready_for_provider"] is True
    assert data["verification_required"] is False
    assert data["approval_id"] is None
    assert data["simulated_balance_after"] == balance_before - 95.0

    # Verify in database
    db = TestingSessionLocal()
    cust_after = db.query(Customer).filter(Customer.customer_id == "CUST-P56-LOW").first()
    assert float(cust_after.simulated_balance) == balance_before - 95.0
    db.close()


def test_central_decision_medium_risk_review_payment_hold(client, alice_auth_headers):
    """Verify MEDIUM risk transaction creates an Approval, holds wallet balance, and requires step-up verification."""
    db = TestingSessionLocal()
    cust = db.query(Customer).filter(Customer.customer_id == "CUST-P56-MED").first()
    balance_before = float(cust.simulated_balance)
    db.close()

    payload = {
        "customer_id": "CUST-P56-MED",
        "amount": 350.0,  # 3.5x average
        "currency": "USD",
        "merchant_name": "New High End Store",
        "merchant_category": "electronics",
        "device_type": "mobile_android",  # New device
        "location": "CA",
        "transaction_country": "US",
        "transaction_type": "online_payment",
        "failed_attempts": 1,
    }

    response = client.post("/api/v1/payment/initiate", json=payload, headers=alice_auth_headers)
    assert response.status_code == 200
    data = response.json()

    assert data["decision"] == "REVIEW"
    assert data["risk_level"] in ("MEDIUM", "HIGH")
    assert data["verification_required"] is True
    assert data["ready_for_provider"] is False
    assert data["approval_id"] is not None
    assert data["approval_id"].startswith("APP-")
    # Payment hold: balance must remain unchanged until approved
    assert data["simulated_balance_after"] == balance_before

    db = TestingSessionLocal()
    cust_check = db.query(Customer).filter(Customer.customer_id == "CUST-P56-MED").first()
    assert float(cust_check.simulated_balance) == balance_before
    db.close()


def test_approval_lifecycle_approve_deducts_balance(client, alice_auth_headers):
    """Verify approving a step-up verification atomically transitions status to SUCCEEDED and deducts balance."""
    db = TestingSessionLocal()
    approval_id = "APP-TEST-APPROVE-01"
    tx_id = "TX-TEST-APPROVE-01"
    customer_id = "alice@test.internal"

    cust = db.query(Customer).filter(Customer.customer_id == customer_id).first()
    initial_balance = float(cust.simulated_balance)

    pi = PaymentIntent(
        payment_id=tx_id,
        customer_id=customer_id,
        amount=250.0,
        currency="USD",
        merchant_name="Verified Tech Store",
        merchant_category="retail",
        lifecycle_status=PaymentLifecycleStatus.PENDING_APPROVAL.value,
        fraud_probability=0.45,
        risk_score=55,
        risk_level="MEDIUM",
        fraud_decision="REVIEW",
    )
    tx = Transaction(
        transaction_id=tx_id,
        customer_id=customer_id,
        amount=250.0,
        status="PENDING_VERIFICATION",
        risk_score=55.0,
        risk_level="MEDIUM",
    )
    appr = TransactionApproval(
        approval_id=approval_id,
        payment_id=tx_id,
        transaction_id=tx_id,
        customer_id=customer_id,
        user_id=1,
        status=ApprovalStatus.PENDING.value,
        amount=250.0,
        currency="USD",
        risk_score=55,
        risk_level="MEDIUM",
        fraud_probability=0.45,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=15),
    )
    db.add_all([pi, tx, appr])
    db.commit()
    db.close()

    # Step: User Approves
    res = client.post(
        f"/api/v1/payment/approvals/{approval_id}/action",
        json={"action": "APPROVE", "notes": "Verified by user via app confirmation"},
        headers=alice_auth_headers,
    )
    assert res.status_code == 200
    res_data = res.json()
    assert res_data["status"] == "APPROVED"
    assert res_data["lifecycle_status"] == "SUCCEEDED"
    assert res_data["simulated_balance"] == initial_balance - 250.0

    # Verify database state
    db = TestingSessionLocal()
    appr_db = db.query(TransactionApproval).filter(TransactionApproval.approval_id == approval_id).first()
    pi_db = db.query(PaymentIntent).filter(PaymentIntent.payment_id == tx_id).first()
    cust_db = db.query(Customer).filter(Customer.customer_id == customer_id).first()

    assert appr_db.status == "APPROVED"
    assert pi_db.lifecycle_status == "SUCCEEDED"
    assert float(cust_db.simulated_balance) == initial_balance - 250.0
    db.close()


def test_approval_lifecycle_reject_permanently_blocks(client, alice_auth_headers):
    """Verify rejecting a step-up verification permanently blocks transaction without balance deduction."""
    db = TestingSessionLocal()
    approval_id = "APP-TEST-REJECT-01"
    tx_id = "TX-TEST-REJECT-01"
    customer_id = "alice@test.internal"

    cust = db.query(Customer).filter(Customer.customer_id == customer_id).first()
    initial_balance = float(cust.simulated_balance)

    pi = PaymentIntent(
        payment_id=tx_id,
        customer_id=customer_id,
        amount=300.0,
        currency="USD",
        merchant_name="Unknown Store",
        merchant_category="retail",
        lifecycle_status=PaymentLifecycleStatus.PENDING_APPROVAL.value,
        fraud_probability=0.55,
        risk_score=65,
        risk_level="MEDIUM",
        fraud_decision="REVIEW",
    )
    tx = Transaction(
        transaction_id=tx_id,
        customer_id=customer_id,
        amount=300.0,
        status="PENDING_VERIFICATION",
        risk_score=65.0,
        risk_level="MEDIUM",
    )
    appr = TransactionApproval(
        approval_id=approval_id,
        payment_id=tx_id,
        transaction_id=tx_id,
        customer_id=customer_id,
        user_id=1,
        status=ApprovalStatus.PENDING.value,
        amount=300.0,
        currency="USD",
        risk_score=65,
        risk_level="MEDIUM",
        fraud_probability=0.55,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=15),
    )
    db.add_all([pi, tx, appr])
    db.commit()
    db.close()

    # Step: User Rejects
    res = client.post(
        f"/api/v1/payment/approvals/{approval_id}/action",
        json={"action": "REJECT", "notes": "I did not authorize this charge"},
        headers=alice_auth_headers,
    )
    assert res.status_code == 200
    res_data = res.json()
    assert res_data["status"] == "REJECTED"
    assert res_data["lifecycle_status"] == "BLOCKED"

    # Verify database state
    db = TestingSessionLocal()
    appr_db = db.query(TransactionApproval).filter(TransactionApproval.approval_id == approval_id).first()
    pi_db = db.query(PaymentIntent).filter(PaymentIntent.payment_id == tx_id).first()
    cust_db = db.query(Customer).filter(Customer.customer_id == customer_id).first()

    assert appr_db.status == "REJECTED"
    assert pi_db.lifecycle_status == "BLOCKED"
    assert float(cust_db.simulated_balance) == initial_balance  # Unchanged
    db.close()


def test_duplicate_action_replay_protection(client, alice_auth_headers):
    """Verify attempting to approve/reject an already resolved approval returns 409 Conflict."""
    db = TestingSessionLocal()
    approval_id = "APP-TEST-REPLAY-01"
    appr = TransactionApproval(
        approval_id=approval_id,
        payment_id="TX-REPLAY-01",
        customer_id="alice@test.internal",
        user_id=1,
        status=ApprovalStatus.APPROVED.value,  # Already approved
        amount=100.0,
        currency="USD",
        risk_score=40,
        risk_level="MEDIUM",
        fraud_probability=0.35,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=15),
    )
    db.add(appr)
    db.commit()
    db.close()

    # Replay approval action
    res = client.post(
        f"/api/v1/payment/approvals/{approval_id}/action",
        json={"action": "APPROVE"},
        headers=alice_auth_headers,
    )
    assert res.status_code == 409
    assert "Replay prevented" in res.json()["detail"]


def test_expired_approval_rejection(client, alice_auth_headers):
    """Verify attempting to approve an expired verification returns 410 Gone."""
    db = TestingSessionLocal()
    approval_id = "APP-TEST-EXPIRED-01"
    past_time = datetime.now(timezone.utc) - timedelta(minutes=30)
    appr = TransactionApproval(
        approval_id=approval_id,
        payment_id="TX-EXPIRED-01",
        customer_id="alice@test.internal",
        user_id=1,
        status=ApprovalStatus.PENDING.value,
        amount=100.0,
        currency="USD",
        risk_score=45,
        risk_level="MEDIUM",
        fraud_probability=0.40,
        expires_at=past_time,  # Expired 30 mins ago
    )
    db.add(appr)
    db.commit()
    db.close()

    res = client.post(
        f"/api/v1/payment/approvals/{approval_id}/action",
        json={"action": "APPROVE"},
        headers=alice_auth_headers,
    )
    assert res.status_code == 410
    assert "expired" in res.json()["detail"].lower()
