"""Comprehensive test suite for Phase 11 Customer Management API."""

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
def setup_customer_test_db():
    """Setup test database tables and seed test users/customers/transactions."""
    app.dependency_overrides[get_db] = override_get_db
    Base.metadata.create_all(bind=test_engine)
    db = TestingSessionLocal()

    # Seed Admin User
    admin = User(
        name="Admin User",
        email="admin_cust@test.internal",
        password_hash=get_password_hash("AdminPass123!"),
        role=UserRole.ADMIN.value,
        is_active=True,
    )
    # Seed Investigator User
    investigator = User(
        name="Investigator User",
        email="inv_cust@test.internal",
        password_hash=get_password_hash("InvPass123!"),
        role=UserRole.FRAUD_INVESTIGATOR.value,
        is_active=True,
    )
    db.add_all([admin, investigator])
    db.flush()

    # Seed Customers
    cust1 = Customer(customer_id="CUST-001", account_age_days=120)
    cust2 = Customer(customer_id="CUST-002", account_age_days=450)
    cust3 = Customer(customer_id="CUST-003", account_age_days=30)
    db.add_all([cust1, cust2, cust3])
    db.flush()

    # Seed Transactions for CUST-001
    tx1 = Transaction(
        transaction_id="TX-CUST1-01",
        customer_id="CUST-001",
        amount=100.0,
        transaction_hour=14,
        merchant_category="Retail",
        transaction_country="US",
        fraud_probability=0.15,
        prediction=0,
        risk_score=20.0,
        risk_level="LOW",
    )
    tx2 = Transaction(
        transaction_id="TX-CUST1-02",
        customer_id="CUST-001",
        amount=500.0,
        transaction_hour=2,
        merchant_category="Electronics",
        transaction_country="US",
        fraud_probability=0.88,
        prediction=1,
        risk_score=85.0,
        risk_level="HIGH",
    )
    # Seed Transaction for CUST-002
    tx3 = Transaction(
        transaction_id="TX-CUST2-01",
        customer_id="CUST-002",
        amount=50.0,
        transaction_hour=10,
        merchant_category="Grocery",
        transaction_country="US",
        fraud_probability=0.05,
        prediction=0,
        risk_score=10.0,
        risk_level="LOW",
    )
    db.add_all([tx1, tx2, tx3])
    db.commit()
    db.close()

    yield

    Base.metadata.drop_all(bind=test_engine)
    app.dependency_overrides.clear()


@pytest.fixture
def investigator_token():
    db = TestingSessionLocal()
    user = db.query(User).filter(User.email == "inv_cust@test.internal").first()
    token = create_access_token(subject=str(user.id), role=user.role)
    db.close()
    return token


@pytest.fixture
def admin_token():
    db = TestingSessionLocal()
    user = db.query(User).filter(User.email == "admin_cust@test.internal").first()
    token = create_access_token(subject=str(user.id), role=user.role)
    db.close()
    return token


def test_list_customers_authenticated(investigator_token):
    client = TestClient(app)
    response = client.get(
        "/api/v1/customers",
        headers={"Authorization": f"Bearer {investigator_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    assert len(data["items"]) == 3
    assert data["page"] == 1

    # Check that transaction_count is properly aggregated
    cust1_data = next((c for c in data["items"] if c["customer_id"] == "CUST-001"), None)
    assert cust1_data is not None
    assert cust1_data["transaction_count"] == 2

    cust3_data = next((c for c in data["items"] if c["customer_id"] == "CUST-003"), None)
    assert cust3_data is not None
    assert cust3_data["transaction_count"] == 0


def test_list_customers_search(investigator_token):
    client = TestClient(app)
    response = client.get(
        "/api/v1/customers?search=002",
        headers={"Authorization": f"Bearer {investigator_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["customer_id"] == "CUST-002"


def test_list_customers_pagination(investigator_token):
    client = TestClient(app)
    response = client.get(
        "/api/v1/customers?page=1&page_size=2",
        headers={"Authorization": f"Bearer {investigator_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    assert len(data["items"]) == 2
    assert data["total_pages"] == 2


def test_get_customer_detail_and_behavioral_stats(investigator_token):
    client = TestClient(app)
    response = client.get(
        "/api/v1/customers/CUST-001",
        headers={"Authorization": f"Bearer {investigator_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["customer_id"] == "CUST-001"
    assert data["account_age_days"] == 120
    assert data["transaction_count"] == 2

    # Verify behavioral statistics calculated from database transactions
    stats = data["behavioral_stats"]
    assert stats["transaction_count"] == 2
    assert stats["average_transaction_amount"] == 300.0  # (100 + 500) / 2
    assert stats["min_transaction_amount"] == 100.0
    assert stats["max_transaction_amount"] == 500.0
    assert stats["high_risk_transaction_count"] == 1
    assert stats["fraud_transaction_count"] == 1

    # Verify recent transactions
    assert len(data["recent_transactions"]) == 2


def test_get_customer_detail_nonexistent_returns_404(investigator_token):
    client = TestClient(app)
    response = client.get(
        "/api/v1/customers/CUST-NONEXISTENT",
        headers={"Authorization": f"Bearer {investigator_token}"},
    )
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_get_customer_transactions_with_filters(investigator_token):
    client = TestClient(app)
    # Filter by risk_level=HIGH
    response = client.get(
        "/api/v1/customers/CUST-001/transactions?risk_level=HIGH",
        headers={"Authorization": f"Bearer {investigator_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["transaction_id"] == "TX-CUST1-02"
    assert data["items"][0]["risk_level"] == "HIGH"

    # Filter by min_amount
    response_amt = client.get(
        "/api/v1/customers/CUST-001/transactions?min_amount=200",
        headers={"Authorization": f"Bearer {investigator_token}"},
    )
    assert response_amt.status_code == 200
    data_amt = response_amt.json()
    assert data_amt["total"] == 1
    assert data_amt["items"][0]["amount"] == 500.0


def test_customer_endpoints_unauthenticated_denied():
    client = TestClient(app)
    res1 = client.get("/api/v1/customers")
    assert res1.status_code == 401

    res2 = client.get("/api/v1/customers/CUST-001")
    assert res2.status_code == 401

    res3 = client.get("/api/v1/customers/CUST-001/transactions")
    assert res3.status_code == 401
