"""Unit tests for Customer Behavior Profile Service (Phase 5)."""

from datetime import datetime, timezone
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.core.database import Base
from backend.app.models.customer import Customer
from backend.app.models.transaction import Transaction
from backend.app.services.behavior_profile_service import BehaviorProfileService


@pytest.fixture
def db_session():
    """Create in-memory SQLite database session for behavior profiling tests."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = Session()

    # Seed an established customer with 3 history transactions
    cust_established = Customer(customer_id="CUST-ESTABLISHED-01", account_age_days=180)
    session.add(cust_established)
    session.commit()

    t1 = Transaction(
        transaction_id="TX-HIST-01",
        customer_id="CUST-ESTABLISHED-01",
        amount=50.0,
        transaction_hour=14,
        merchant_category="grocery",
        transaction_country="US",
        geo_location_region="CA",
        device_type="web",
        transaction_type="online_payment",
        created_at=datetime.now(timezone.utc),
    )
    t2 = Transaction(
        transaction_id="TX-HIST-02",
        customer_id="CUST-ESTABLISHED-01",
        amount=150.0,
        transaction_hour=15,
        merchant_category="dining",
        transaction_country="US",
        geo_location_region="CA",
        device_type="mobile",
        transaction_type="POS",
        created_at=datetime.now(timezone.utc),
    )
    t3 = Transaction(
        transaction_id="TX-HIST-03",
        customer_id="CUST-ESTABLISHED-01",
        amount=100.0,
        transaction_hour=16,
        merchant_category="retail",
        transaction_country="US",
        geo_location_region="CA",
        device_type="web",
        transaction_type="online_payment",
        created_at=datetime.now(timezone.utc),
    )
    session.add_all([t1, t2, t3])
    session.commit()

    yield session

    session.close()
    Base.metadata.drop_all(bind=engine)


def test_behavior_profile_established_customer(db_session):
    """Verify profile calculation for a customer with existing transaction history."""
    profile = BehaviorProfileService.get_customer_profile(
        db=db_session,
        customer_id="CUST-ESTABLISHED-01",
    )

    assert profile.customer_id == "CUST-ESTABLISHED-01"
    assert profile.is_cold_start is False
    assert profile.total_transactions == 3
    assert profile.historical_avg_amount == 100.0  # (50 + 150 + 100) / 3
    assert profile.historical_median_amount == 100.0
    assert profile.historical_max_amount == 150.0
    assert "web" in profile.known_devices
    assert "mobile" in profile.known_devices
    assert "CA" in profile.usual_locations
    assert profile.home_country == "US"


def test_behavior_profile_cold_start_new_customer(db_session):
    """Verify cold start behavior for a new customer with zero past transactions."""
    new_cust = Customer(customer_id="CUST-NEW-01", account_age_days=5)
    db_session.add(new_cust)
    db_session.commit()

    profile = BehaviorProfileService.get_customer_profile(
        db=db_session,
        customer_id="CUST-NEW-01",
    )

    assert profile.customer_id == "CUST-NEW-01"
    assert profile.is_cold_start is True
    assert profile.total_transactions == 0
    assert profile.historical_avg_amount == 0.0
    assert profile.known_devices == []


def test_derive_pre_auth_features_normal_transaction(db_session):
    """Verify pre-auth feature engineering for a normal within-profile payment."""
    features = BehaviorProfileService.derive_pre_auth_features(
        db=db_session,
        customer_id="CUST-ESTABLISHED-01",
        amount=110.0,
        merchant_category="grocery",
        device_type="web",
        location="CA",
        transaction_country="US",
        transaction_hour=14,
        failed_attempts=0,
    )

    assert features.amount == 110.0
    assert features.historical_avg_amount == 100.0
    assert features.amount_deviation == 10.0
    assert round(features.amount_ratio, 2) == 1.10
    assert features.is_extreme_amount_surge is False
    assert features.is_new_device is False
    assert features.is_unusual_location is False
    assert features.is_international is False
    assert features.is_night_transaction is False
    assert features.behaviour_deviation_score < 0.20


def test_derive_pre_auth_features_anomalous_transaction(db_session):
    """Verify pre-auth feature engineering when payment deviates heavily from baseline."""
    features = BehaviorProfileService.derive_pre_auth_features(
        db=db_session,
        customer_id="CUST-ESTABLISHED-01",
        amount=3500.0,  # 35x historical average
        merchant_category="luxury_goods",
        device_type="unknown_linux_bot",  # Novel device
        location="Moscow",  # Novel location
        transaction_country="RU",  # Cross-border
        transaction_hour=3,  # Night window
        failed_attempts=3,
    )

    assert features.amount == 3500.0
    assert features.amount_ratio >= 30.0
    assert features.is_extreme_amount_surge is True
    assert features.is_new_device is True
    assert features.is_unusual_location is True
    assert features.is_international is True
    assert features.is_night_transaction is True
    assert features.failed_attempts == 3
    assert features.behaviour_deviation_score >= 0.70


def test_derive_pre_auth_features_cold_start_safe(db_session):
    """Verify cold start customer is treated neutrally without false positive fraud."""
    features = BehaviorProfileService.derive_pre_auth_features(
        db=db_session,
        customer_id="CUST-BRAND-NEW",
        amount=85.0,
        merchant_category="retail",
        device_type="mobile",
        location="CA",
        transaction_country="US",
        transaction_hour=12,
        failed_attempts=0,
    )

    assert features.is_cold_start is True
    assert features.amount == 85.0
    assert features.amount_ratio == 1.0
    assert features.amount_deviation == 0.0
    assert features.is_extreme_amount_surge is False
    assert features.is_new_device is False
    assert features.is_unusual_location is False
    assert features.behaviour_deviation_score == 0.0
