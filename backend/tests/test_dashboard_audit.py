"""Comprehensive test suite for Phase 15 Dashboard, Reports, and Audit Logs."""

import json
import pytest
from datetime import datetime, timezone
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
from backend.app.models.audit_log import AuditLog
from backend.app.schemas.user import UserRole

# In-memory SQLite engine for isolated testing
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
def setup_dashboard_test_db():
    """Setup test database tables and seed test data."""
    app.dependency_overrides[get_db] = override_get_db
    Base.metadata.create_all(bind=test_engine)
    db = TestingSessionLocal()

    # Seed Admin User
    admin = User(
        name="Security Admin",
        email="dash_admin@test.internal",
        password_hash=get_password_hash("AdminPass123!"),
        role=UserRole.ADMIN.value,
        is_active=True,
    )
    # Seed Fraud Investigator
    investigator = User(
        name="Lead Investigator",
        email="dash_inv@test.internal",
        password_hash=get_password_hash("InvPass123!"),
        role=UserRole.FRAUD_INVESTIGATOR.value,
        is_active=True,
    )
    db.add(admin)
    db.add(investigator)
    db.commit()
    db.refresh(admin)
    db.refresh(investigator)

    # Seed Customers
    c1 = Customer(
        customer_id="CUST-DASH-01",
        account_age_days=180,
    )
    c2 = Customer(
        customer_id="CUST-DASH-02",
        account_age_days=30,
    )
    db.add(c1)
    db.add(c2)
    db.commit()


    # Seed Transactions: 1 genuine low risk, 1 medium risk, 1 high risk fraud
    t1 = Transaction(
        transaction_id="TX-DASH-001",
        customer_id="CUST-DASH-01",
        amount=45.0,
        transaction_hour=14,
        merchant_category="grocery",
        transaction_country="US",
        device_type="mobile_ios",
        transaction_type="POS",
        fraud_probability=0.08,
        prediction=0,
        risk_score=15.0,
        risk_level="LOW",
    )
    t2 = Transaction(
        transaction_id="TX-DASH-002",
        customer_id="CUST-DASH-01",
        amount=550.0,
        transaction_hour=16,
        merchant_category="electronics",
        transaction_country="US",
        device_type="desktop_windows",
        transaction_type="ONLINE",
        fraud_probability=0.45,
        prediction=0,
        risk_score=52.0,
        risk_level="MEDIUM",
    )
    t3 = Transaction(
        transaction_id="TX-DASH-003",
        customer_id="CUST-DASH-02",
        amount=1950.0,
        transaction_hour=3,
        merchant_category="luxury_goods",
        transaction_country="RU",
        device_type="unknown",
        transaction_type="ONLINE",
        fraud_probability=0.92,
        prediction=1,
        risk_score=88.0,
        risk_level="HIGH",
    )
    db.add(t1)
    db.add(t2)
    db.add(t3)
    db.commit()


    # Seed Investigation for t3
    inv = Investigation(
        case_id="INV-CASE-DASH-01",
        transaction_id="TX-DASH-003",
        status="open",
        investigator_id=investigator.id,
        decision=None,
        notes="Automated case created from high-risk transaction",
    )
    db.add(inv)


    # Seed Audit Logs
    audit1 = AuditLog(
        user_id=admin.id,
        action="CREATE",
        resource_type="TRANSACTION",
        resource_id="TX-DASH-003",
        details=json.dumps({"risk_score": 88.0, "amount": 1950.0}),
    )
    audit2 = AuditLog(
        user_id=investigator.id,
        action="UPDATE",
        resource_type="INVESTIGATION",
        resource_id="INV-CASE-DASH-01",
        details=json.dumps({"status": "open", "investigator_id": investigator.id}),
    )
    db.add(audit1)
    db.add(audit2)
    db.commit()


    db.close()
    yield
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def admin_headers():
    db = TestingSessionLocal()
    user = db.query(User).filter(User.email == "dash_admin@test.internal").first()
    token = create_access_token(subject=str(user.id), role=user.role)
    db.close()
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def investigator_headers():
    db = TestingSessionLocal()
    user = db.query(User).filter(User.email == "dash_inv@test.internal").first()
    token = create_access_token(subject=str(user.id), role=user.role)
    db.close()
    return {"Authorization": f"Bearer {token}"}



def test_dashboard_stats_unauthorized(client):
    """GET /api/v1/dashboard/stats requires authentication."""
    response = client.get("/api/v1/dashboard/stats")
    assert response.status_code == 401


def test_dashboard_stats_investigator(client, investigator_headers):
    """Investigator can fetch real DB-calculated statistics."""
    response = client.get("/api/v1/dashboard/stats", headers=investigator_headers)
    assert response.status_code == 200
    data = response.json()

    assert data["total_transactions"] == 3
    assert data["total_customers"] == 2
    assert data["fraud_transactions"] == 1
    assert data["genuine_transactions"] == 2
    assert data["high_risk_transactions"] == 1
    assert data["medium_risk_transactions"] == 1
    assert data["low_risk_transactions"] == 1
    assert data["total_investigations"] == 1
    assert data["open_investigations"] == 1
    assert data["resolved_investigations"] == 0
    assert data["active_model_info"] is not None
    assert len(data["recent_high_risk_activity"]) >= 1
    assert "LOW" in data["risk_distribution"]




def test_dashboard_reports_admin(client, admin_headers):
    """Admin can fetch real analytics reports."""
    response = client.get("/api/v1/dashboard/reports", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()

    assert "summary" in data
    assert "risk_breakdown" in data
    assert "merchant_category_analysis" in data
    assert "investigation_outcomes" in data
    assert "model_performance_summary" in data
    assert data["summary"]["total_transactions"] == 3
    assert data["summary"]["fraud_transactions"] == 1
    assert len(data["risk_breakdown"]) == 3



def test_audit_logs_listing_and_filtering(client, admin_headers, investigator_headers):
    """Test audit log queries, pagination, and action filtering."""
    # Admin access
    resp = client.get("/api/v1/audit-logs", headers=admin_headers)
    assert resp.status_code == 200
    logs_data = resp.json()
    assert logs_data["total"] >= 2
    assert len(logs_data["items"]) >= 2

    # Filter by action
    resp_action = client.get("/api/v1/audit-logs?action=CREATE", headers=admin_headers)
    assert resp_action.status_code == 200
    filtered = resp_action.json()
    assert all(item["action"] == "CREATE" for item in filtered["items"])

    # Investigator read access
    resp_inv = client.get("/api/v1/audit-logs", headers=investigator_headers)
    assert resp_inv.status_code == 200

    # Ensure no passwords or hashes in details
    for log in logs_data["items"]:
        if log["details"]:
            details_str = json.dumps(log["details"]).lower()
            assert "password" not in details_str
            assert "secret" not in details_str

