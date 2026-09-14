"""Comprehensive test suite for Phase 13 Investigation & Case Management."""

import json
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
from backend.app.models.investigation import Investigation
from backend.app.models.shap_explanation import ShapExplanation
from backend.app.models.audit_log import AuditLog
from backend.app.schemas.user import UserRole

# In-memory SQLite engine for test isolation
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
def setup_investigation_test_db():
    """Setup test database tables and seed test data."""
    app.dependency_overrides[get_db] = override_get_db
    Base.metadata.create_all(bind=test_engine)
    db = TestingSessionLocal()

    # Seed Admin User
    admin = User(
        name="Admin User",
        email="admin_inv@test.internal",
        password_hash=get_password_hash("AdminPass123!"),
        role=UserRole.ADMIN.value,
        is_active=True,
    )
    # Seed Primary Investigator User
    investigator1 = User(
        name="Investigator One",
        email="inv1@test.internal",
        password_hash=get_password_hash("InvPass123!"),
        role=UserRole.FRAUD_INVESTIGATOR.value,
        is_active=True,
    )
    # Seed Secondary Investigator User
    investigator2 = User(
        name="Investigator Two",
        email="inv2@test.internal",
        password_hash=get_password_hash("InvPass123!"),
        role=UserRole.FRAUD_INVESTIGATOR.value,
        is_active=True,
    )
    db.add_all([admin, investigator1, investigator2])
    db.flush()

    # Seed Customer
    cust = Customer(customer_id="CUST-INV-01", account_age_days=180)
    db.add(cust)
    db.flush()

    # Seed Transactions
    tx1 = Transaction(
        transaction_id="TX-INV-001",
        customer_id="CUST-INV-01",
        amount=1500.0,
        transaction_hour=3,
        merchant_category="Electronics",
        transaction_country="US",
        fraud_probability=0.85,
        prediction=1,
        risk_score=88.0,
        risk_level="HIGH",
    )
    tx2 = Transaction(
        transaction_id="TX-INV-002",
        customer_id="CUST-INV-01",
        amount=250.0,
        transaction_hour=15,
        merchant_category="Retail",
        transaction_country="US",
        fraud_probability=0.25,
        prediction=0,
        risk_score=35.0,
        risk_level="MEDIUM",
    )
    db.add_all([tx1, tx2])
    db.flush()

    # Seed SHAP record for tx1
    shap1 = ShapExplanation(
        transaction_id="TX-INV-001",
        feature_name="transaction_amount",
        shap_value=0.45,
        impact="high_risk",
    )
    db.add(shap1)
    db.commit()
    db.close()

    yield

    Base.metadata.drop_all(bind=test_engine)
    app.dependency_overrides.clear()


@pytest.fixture
def admin_token():
    db = TestingSessionLocal()
    user = db.query(User).filter(User.email == "admin_inv@test.internal").first()
    token = create_access_token(subject=str(user.id), role=user.role)
    db.close()
    return token


@pytest.fixture
def investigator1_token():
    db = TestingSessionLocal()
    user = db.query(User).filter(User.email == "inv1@test.internal").first()
    token = create_access_token(subject=str(user.id), role=user.role)
    db.close()
    return token


@pytest.fixture
def investigator2_token():
    db = TestingSessionLocal()
    user = db.query(User).filter(User.email == "inv2@test.internal").first()
    token = create_access_token(subject=str(user.id), role=user.role)
    db.close()
    return token


def test_create_case_success_and_audit_log(investigator1_token):
    client = TestClient(app)
    payload = {
        "transaction_id": "TX-INV-001",
        "notes": "Suspicious late night high value electronics purchase.",
    }
    response = client.post(
        "/api/v1/investigations",
        json=payload,
        headers={"Authorization": f"Bearer {investigator1_token}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["case_id"].startswith("CASE-")
    assert data["transaction_id"] == "TX-INV-001"
    assert data["status"] == "OPEN"
    assert data["decision"] is None
    assert data["amount"] == 1500.0
    assert data["risk_level"] == "HIGH"
    assert len(data["top_shap_factors"]) > 0

    # Verify audit log was recorded
    db = TestingSessionLocal()
    audit = db.query(AuditLog).filter(AuditLog.resource_id == data["case_id"]).first()
    assert audit is not None
    assert audit.action == "INVESTIGATION_CASE_CREATED"
    db.close()


def test_create_duplicate_active_case_prevention(investigator1_token):
    client = TestClient(app)
    payload = {
        "transaction_id": "TX-INV-001",
        "notes": "Attempting second case for same transaction.",
    }
    response = client.post(
        "/api/v1/investigations",
        json=payload,
        headers={"Authorization": f"Bearer {investigator1_token}"},
    )
    assert response.status_code == 409
    assert "already exists" in response.json()["detail"].lower()


def test_create_case_nonexistent_transaction(investigator1_token):
    client = TestClient(app)
    payload = {
        "transaction_id": "TX-DOES-NOT-EXIST",
        "notes": "Invalid transaction reference.",
    }
    response = client.post(
        "/api/v1/investigations",
        json=payload,
        headers={"Authorization": f"Bearer {investigator1_token}"},
    )
    assert response.status_code == 404


def test_list_investigations_and_filters(investigator1_token, admin_token):
    client = TestClient(app)
    # Create a second case
    client.post(
        "/api/v1/investigations",
        json={"transaction_id": "TX-INV-002", "notes": "Medium risk review."},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    # List all
    res = client.get(
        "/api/v1/investigations",
        headers={"Authorization": f"Bearer {investigator1_token}"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 2

    # Filter by status
    res_status = client.get(
        "/api/v1/investigations?status=OPEN",
        headers={"Authorization": f"Bearer {investigator1_token}"},
    )
    assert res_status.status_code == 200
    assert res_status.json()["total"] == 2

    # Filter by search
    res_search = client.get(
        "/api/v1/investigations?search=TX-INV-002",
        headers={"Authorization": f"Bearer {investigator1_token}"},
    )
    assert res_search.status_code == 200
    assert res_search.json()["total"] == 1


def test_get_investigation_detail(investigator1_token):
    client = TestClient(app)
    # List to get case_id
    list_res = client.get("/api/v1/investigations", headers={"Authorization": f"Bearer {investigator1_token}"})
    case_id = list_res.json()["items"][0]["case_id"]

    res = client.get(
        f"/api/v1/investigations/{case_id}",
        headers={"Authorization": f"Bearer {investigator1_token}"},
    )
    assert res.status_code == 200
    detail = res.json()
    assert detail["case_id"] == case_id
    assert detail["customer_id"] == "CUST-INV-01"


def test_case_workflow_status_and_resolution_validation(investigator1_token):
    client = TestClient(app)
    list_res = client.get("/api/v1/investigations", headers={"Authorization": f"Bearer {investigator1_token}"})
    items = list_res.json()["items"]
    # Pick case assigned to or created for investigator1
    case_id = items[0]["case_id"]
    for item in items:
        if item.get("assigned_to") == 2 or item.get("investigator_id") == 2:
            case_id = item["case_id"]
            break

    # 1. Update to UNDER_REVIEW
    res_review = client.patch(
        f"/api/v1/investigations/{case_id}",
        json={"status": "UNDER_REVIEW", "notes": "Investigator verifying billing address."},
        headers={"Authorization": f"Bearer {investigator1_token}"},
    )
    assert res_review.status_code == 200
    assert res_review.json()["status"] == "UNDER_REVIEW"

    # 2. Attempt to resolve WITHOUT decision (must fail 400)
    res_no_dec = client.patch(
        f"/api/v1/investigations/{case_id}",
        json={"status": "RESOLVED"},
        headers={"Authorization": f"Bearer {investigator1_token}"},
    )
    assert res_no_dec.status_code == 400
    assert "decision" in res_no_dec.json()["detail"].lower()

    # 3. Resolve WITH valid decision and notes
    res_resolved = client.patch(
        f"/api/v1/investigations/{case_id}",
        json={
            "status": "RESOLVED",
            "decision": "CONFIRMED_FRAUD",
            "notes": "Cardholder confirmed unauthorized activity.",
        },
        headers={"Authorization": f"Bearer {investigator1_token}"},
    )
    assert res_resolved.status_code == 200
    data = res_resolved.json()
    assert data["status"] == "RESOLVED"
    assert data["decision"] == "CONFIRMED_FRAUD"


def test_invalid_status_and_decision_rejected(investigator1_token):
    client = TestClient(app)
    list_res = client.get("/api/v1/investigations", headers={"Authorization": f"Bearer {investigator1_token}"})
    case_id = list_res.json()["items"][0]["case_id"]

    # Invalid status
    res1 = client.patch(
        f"/api/v1/investigations/{case_id}",
        json={"status": "INVALID_STATUS"},
        headers={"Authorization": f"Bearer {investigator1_token}"},
    )
    assert res1.status_code == 422

    # Invalid decision
    res2 = client.patch(
        f"/api/v1/investigations/{case_id}",
        json={"decision": "MAYBE_FRAUD"},
        headers={"Authorization": f"Bearer {investigator1_token}"},
    )
    assert res2.status_code == 422


def test_investigator_authorization_boundaries(investigator1_token, investigator2_token, admin_token):
    client = TestClient(app)
    list_res = client.get("/api/v1/investigations", headers={"Authorization": f"Bearer {admin_token}"})
    case_id = list_res.json()["items"][0]["case_id"]

    # Investigator 2 attempts to modify case assigned to Investigator 1 (must fail 403)
    res = client.patch(
        f"/api/v1/investigations/{case_id}",
        json={"notes": "Investigator 2 trying to hijack notes."},
        headers={"Authorization": f"Bearer {investigator2_token}"},
    )
    assert res.status_code == 403

    # Admin CAN modify and reassign any case
    db = TestingSessionLocal()
    u2 = db.query(User).filter(User.email == "inv2@test.internal").first()
    db.close()

    res_admin = client.patch(
        f"/api/v1/investigations/{case_id}",
        json={"investigator_id": u2.id, "notes": "Reassigned by Admin."},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res_admin.status_code == 200
    assert res_admin.json()["investigator_id"] == u2.id
