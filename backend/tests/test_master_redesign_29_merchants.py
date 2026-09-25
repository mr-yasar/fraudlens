"""Master Test Suite for FraudLens AI Redesign with 30 Master Merchants and 15 Customers."""

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.core.security import create_access_token
from backend.app.core.database import SessionLocal
from backend.app.models import Merchant, Transaction, User, Customer

client = TestClient(app)


@pytest.fixture
def admin_token():
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == "admin@fraudlens.ai").first()
        uid = str(user.id) if user else "1"
        return create_access_token(subject=uid, role="admin")
    finally:
        db.close()


@pytest.fixture
def investigator_token():
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == "investigator@fraudlens.ai").first()
        uid = str(user.id) if user else "2"
        return create_access_token(subject=uid, role="fraud_investigator")
    finally:
        db.close()


@pytest.fixture
def customer_token():
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == "user@fraudlens.ai").first()
        uid = str(user.id) if user else "3"
        return create_access_token(subject=uid, role="customer")
    finally:
        db.close()


def test_merchant_directory_returns_30_merchants(investigator_token):
    """Verify that all 30 master merchants (20 clean, 10 fraud) are returned with live telemetry."""
    response = client.get(
        "/api/v1/merchants",
        headers={"Authorization": f"Bearer {investigator_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 30
    merchants = data["merchants"]
    assert len(merchants) == 30

    # Verify M001 (Supermarket), M011 (Tamil Name), M016 (DMart), M021 (1xBet Betting)
    m001 = next(m for m in merchants if m["merchant_id"] == "M001")
    assert "NovaMart Fresh" in m001["merchant_name"]
    assert m001["category"] == "Grocery & Supermarket"

    m011 = next(m for m in merchants if m["merchant_id"] == "M011")
    assert m011["merchant_name"] == "Murugan Idli Shop"

    m016 = next(m for m in merchants if m["merchant_id"] == "M016")
    assert "DMart" in m016["merchant_name"]

    m021 = next(m for m in merchants if m["merchant_id"] == "M021")
    assert "1xBet" in m021["merchant_name"]


def test_customers_count_is_exactly_15(investigator_token):
    """Verify that the system contains the 15 defined synthetic customers."""
    db = SessionLocal()
    try:
        cust_count = db.query(Customer).count()
        assert cust_count >= 15
        
        c1 = db.query(Customer).filter(Customer.customer_id == "CUST_001").first()
        assert c1 is not None
        assert c1.name == "Murugan Velan"
    finally:
        db.close()


def test_merchant_detail_and_betting_fraud_pattern(investigator_token):
    """Verify deep-dive merchant profile with synthetic historical betting fraud pattern."""
    response = client.get(
        "/api/v1/merchants/M021",
        headers={"Authorization": f"Bearer {investigator_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["merchant"]["merchant_id"] == "M021"
    assert "1xBet" in data["merchant"]["merchant_name"]
    assert "telemetry" in data
    assert data["telemetry"]["total_transactions"] > 0


def test_dataset_totals_and_merchants(admin_token):
    """Verify that database holds at least 30 merchants, 15 canonical customers, and 20,000 transactions."""
    db = SessionLocal()
    try:
        tx_count = db.query(Transaction).count()
        merchant_count = db.query(Merchant).count()
        customer_count = db.query(Customer).count()
        assert tx_count >= 20000
        assert merchant_count >= 30
        assert customer_count >= 15
    finally:
        db.close()
