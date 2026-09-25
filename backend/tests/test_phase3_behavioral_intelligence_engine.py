"""Unit and Integration Tests for Phase 3 Behavioral Intelligence Engine and Phase 4 Production ML Runtime."""

from datetime import datetime, timezone, timedelta
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from backend.app.core.database import Base, get_db
from backend.app.main import app
from backend.app.models.customer import Customer
from backend.app.models.transaction import Transaction
from backend.app.models.beneficiary import Beneficiary
from backend.app.models.device import CustomerDevice
from backend.app.services.behavior_profile_service import BehaviorProfileService, CustomerBehaviorProfile
from backend.app.services.behavior_intelligence_service import CustomerBehaviourIntelligenceService
from backend.app.services.prediction_service import FraudPredictionService
from backend.app.schemas.prediction import TransactionPredictionInput


# In-memory SQLite for fast isolated testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """Provide a clean isolated in-memory database session."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """Provide a FastAPI test client using the test database."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    test_client = TestClient(app)
    yield test_client
    app.dependency_overrides.pop(get_db, None)


# --------------------------------------------------------------------------
# PHASE 3: BEHAVIORAL INTELLIGENCE ENGINE TESTS
# --------------------------------------------------------------------------

def test_cold_start_user_handling(db_session):
    """Cold start user with 0 history must not crash, have is_cold_start=True, and zero baselines."""
    customer = Customer(
        customer_id="CUST-NEW-001",
        account_age_days=10,
        simulated_balance=50000.0,
        currency="USD",
    )
    db_session.add(customer)
    db_session.commit()

    profile = BehaviorProfileService.get_customer_profile(db_session, "CUST-NEW-001")
    assert profile.is_cold_start is True
    assert profile.total_transactions == 0
    assert profile.historical_avg_amount == 0.0
    assert profile.confidence_status == "HISTORY_UNAVAILABLE"

    # Pre-auth derivation for cold start
    features = BehaviorProfileService.derive_pre_auth_features(
        db=db_session,
        customer_id="CUST-NEW-001",
        amount=100.0,
        merchant_category="retail",
        device_type="web",
    )
    assert features.is_cold_start is True
    assert features.amount == 100.0
    assert features.amount_ratio == 1.0
    assert features.amount_deviation == 0.0
    assert features.is_extreme_amount_surge is False
    assert features.is_new_device is False  # Safe cold-start prior


def test_normal_user_baseline_and_deviation(db_session):
    """Normal user with established transaction history ($100 avg) performing a $120 transaction."""
    now = datetime.now(timezone.utc)
    customer = Customer(customer_id="CUST-NORM-001", account_age_days=180, simulated_balance=50000.0)
    db_session.add(customer)

    # Add 5 historical transactions of $100
    for i in range(5):
        tx = Transaction(
            transaction_id=f"TX-NORM-{i}",
            customer_id="CUST-NORM-001",
            amount=100.0,
            transaction_hour=14,
            merchant_category="retail",
            transaction_country="US",
            geo_location_region="CA",
            device_type="iPhone",
            beneficiary="Amazon",
            created_at=now - timedelta(days=i + 1),
        )
        db_session.add(tx)
    db_session.commit()

    profile = BehaviorProfileService.get_customer_profile(db_session, "CUST-NORM-001")
    assert profile.is_cold_start is False
    assert profile.total_transactions == 5
    assert profile.historical_avg_amount == 100.0
    assert profile.historical_min_amount == 100.0
    assert profile.historical_max_amount == 100.0
    assert "iPhone" in profile.known_devices
    assert "Amazon" in profile.known_beneficiaries

    # Evaluate normal $120 payment
    features = BehaviorProfileService.derive_pre_auth_features(
        db=db_session,
        customer_id="CUST-NORM-001",
        amount=120.0,
        merchant_category="retail",
        device_type="iPhone",
        location="CA",
        transaction_country="US",
        beneficiary_name="Amazon",
    )
    assert features.is_cold_start is False
    assert round(features.amount_deviation, 2) == 20.0
    assert round(features.amount_ratio, 2) == 1.2
    assert features.is_extreme_amount_surge is False
    assert features.is_new_device is False
    assert features.is_new_beneficiary is False
    assert features.is_unusual_location is False
    assert features.behaviour_deviation_score < 0.3


def test_amount_anomaly_detection(db_session):
    """User with $50 historical average attempting a $2,500 transaction (50x spike)."""
    now = datetime.now(timezone.utc)
    customer = Customer(customer_id="CUST-SPIKE-001", account_age_days=90, simulated_balance=50000.0)
    db_session.add(customer)

    for i in range(4):
        tx = Transaction(
            transaction_id=f"TX-SPIKE-{i}",
            customer_id="CUST-SPIKE-001",
            amount=50.0,
            transaction_hour=12,
            merchant_category="groceries",
            transaction_country="US",
            geo_location_region="NY",
            device_type="Android",
            beneficiary="Walmart",
            created_at=now - timedelta(days=i + 1),
        )
        db_session.add(tx)
    db_session.commit()

    features = BehaviorProfileService.derive_pre_auth_features(
        db=db_session,
        customer_id="CUST-SPIKE-001",
        amount=2500.0,
        merchant_category="electronics",
        device_type="Android",
        location="NY",
        transaction_country="US",
        beneficiary_name="Walmart",
    )
    assert features.is_extreme_amount_surge is True
    assert features.amount_ratio >= 40.0
    assert features.amount_deviation == 2450.0
    assert features.behaviour_deviation_score >= 0.35


def test_device_novelty_detection(db_session):
    """Detect new unrecognized device vs existing known device."""
    customer = Customer(customer_id="CUST-DEV-001", account_age_days=60, simulated_balance=50000.0)
    db_session.add(customer)
    # Register known device
    dev = CustomerDevice(
        customer_id="CUST-DEV-001",
        device_identifier="dev-mac-001",
        device_type="MacBook",
        is_trusted=True,
    )
    db_session.add(dev)
    # Register historical transaction
    tx = Transaction(
        transaction_id="TX-DEV-01",
        customer_id="CUST-DEV-001",
        amount=75.0,
        transaction_hour=12,
        device_type="MacBook",
        created_at=datetime.now(timezone.utc) - timedelta(days=1),
    )
    db_session.add(tx)
    db_session.commit()

    # Known device
    feat_known = BehaviorProfileService.derive_pre_auth_features(
        db=db_session,
        customer_id="CUST-DEV-001",
        amount=75.0,
        device_type="MacBook",
    )
    assert feat_known.is_new_device is False

    # New device
    feat_new = BehaviorProfileService.derive_pre_auth_features(
        db=db_session,
        customer_id="CUST-DEV-001",
        amount=75.0,
        device_type="LinuxBot",
    )
    assert feat_new.is_new_device is True


def test_beneficiary_novelty_detection(db_session):
    """Detect first-time beneficiary vs existing trusted beneficiary."""
    customer = Customer(customer_id="CUST-BENE-001", account_age_days=120, simulated_balance=50000.0)
    db_session.add(customer)
    bene = Beneficiary(customer_id="CUST-BENE-001", beneficiary_name="Alice Smith", is_trusted=True)
    db_session.add(bene)
    tx = Transaction(
        transaction_id="TX-BENE-01",
        customer_id="CUST-BENE-001",
        amount=200.0,
        transaction_hour=14,
        beneficiary="Alice Smith",
        created_at=datetime.now(timezone.utc) - timedelta(days=2),
    )
    db_session.add(tx)
    db_session.commit()

    # Existing beneficiary
    feat_existing = BehaviorProfileService.derive_pre_auth_features(
        db=db_session,
        customer_id="CUST-BENE-001",
        amount=200.0,
        beneficiary_name="Alice Smith",
    )
    assert feat_existing.is_new_beneficiary is False

    # New beneficiary
    feat_new = BehaviorProfileService.derive_pre_auth_features(
        db=db_session,
        customer_id="CUST-BENE-001",
        amount=200.0,
        beneficiary_name="Unknown Off-shore Merchant",
    )
    assert feat_new.is_new_beneficiary is True


def test_velocity_window_calculations(db_session):
    """Verify velocity tracking across 5m, 15m, 1h, 24h, and 7d."""
    now = datetime.now(timezone.utc)
    customer = Customer(customer_id="CUST-VEL-001", account_age_days=45, simulated_balance=50000.0)
    db_session.add(customer)

    # 1 transaction 2 mins ago (in 5m, 15m, 1h, 24h, 7d)
    db_session.add(Transaction(transaction_id="TX-V1", customer_id="CUST-VEL-001", amount=10.0, transaction_hour=now.hour, created_at=now - timedelta(minutes=2)))
    # 1 transaction 10 mins ago (in 15m, 1h, 24h, 7d)
    db_session.add(Transaction(transaction_id="TX-V2", customer_id="CUST-VEL-001", amount=20.0, transaction_hour=now.hour, created_at=now - timedelta(minutes=10)))
    # 1 transaction 30 mins ago (in 1h, 24h, 7d)
    db_session.add(Transaction(transaction_id="TX-V3", customer_id="CUST-VEL-001", amount=30.0, transaction_hour=now.hour, created_at=now - timedelta(minutes=30)))
    # 1 transaction 5 hours ago (in 24h, 7d)
    db_session.add(Transaction(transaction_id="TX-V4", customer_id="CUST-VEL-001", amount=40.0, transaction_hour=now.hour, created_at=now - timedelta(hours=5)))
    # 1 transaction 3 days ago (in 7d)
    db_session.add(Transaction(transaction_id="TX-V5", customer_id="CUST-VEL-001", amount=50.0, transaction_hour=now.hour, created_at=now - timedelta(days=3)))
    # 1 transaction 10 days ago (outside 7d)
    db_session.add(Transaction(transaction_id="TX-V6", customer_id="CUST-VEL-001", amount=60.0, transaction_hour=now.hour, created_at=now - timedelta(days=10)))

    db_session.commit()

    profile = BehaviorProfileService.get_customer_profile(db_session, "CUST-VEL-001", current_timestamp=now)
    assert profile.velocity_5m == 1
    assert profile.velocity_15m == 2
    assert profile.velocity_1h == 3
    assert profile.velocity_24h == 4
    assert profile.velocity_7d == 5
    assert profile.total_transactions == 6



# --------------------------------------------------------------------------
# PHASE 4: PRODUCTION ML RUNTIME INTEGRATION TESTS
# --------------------------------------------------------------------------

def test_prediction_service_singleton_and_artifacts():
    """Ensure FraudPredictionService loads preprocessor, active model, and metadata correctly."""
    service = FraudPredictionService.get_instance()
    assert service.is_ready is True
    assert service.preprocessor is not None
    assert service.model is not None
    assert service.model_name in ["xgboost", "random_forest", "logistic_regression", "ensemble_stacking"]
    assert service.threshold > 0.0


def test_three_model_architecture_inference():
    """Verify inference across Logistic Regression, Random Forest, and XGBoost models."""
    service = FraudPredictionService.get_instance()
    
    payload = TransactionPredictionInput(
        transaction_id="TX-TEST-ML-001",
        Amount=250.0,
        Average_Previous_Amount=100.0,
        Transactions_Last_24H=2.0,
        Account_Age_Days=180.0,
        Transaction_Hour=14,
        Device_Type="web",
        Location="NY",
        Usual_Location="NY",
        New_Device=0,
        International_Transaction=0,
    )

    # 1. Active model prediction
    active_pred = service.predict_transaction(payload)
    assert active_pred.fraud_probability >= 0.0 and active_pred.fraud_probability <= 1.0
    assert active_pred.prediction in ["FRAUD", "GENUINE"]
    assert active_pred.risk_score >= 0 and active_pred.risk_score <= 100

    # 2. Multi-model simultaneous comparison
    comparison = service.compare_all_models(payload)
    assert "active_model" in comparison
    assert "model_predictions" in comparison
    preds = comparison["model_predictions"]
    
    for model_name in ["logistic_regression", "random_forest", "xgboost"]:
        if model_name in preds and "fraud_probability" in preds[model_name]:
            p = preds[model_name]["fraud_probability"]
            assert 0.0 <= p <= 1.0


def test_shap_explanation_integration():
    """Verify local SHAP explanation returns attribution factors for model features."""
    service = FraudPredictionService.get_instance()
    
    payload = TransactionPredictionInput(
        transaction_id="TX-SHAP-001",
        Amount=5000.0,
        Average_Previous_Amount=50.0,
        Transactions_Last_24H=10.0,
        Account_Age_Days=15.0,
        Transaction_Hour=3,
        Device_Type="mobile",
        Location="Unknown",
        Usual_Location="NY",
        New_Device=1,
        International_Transaction=1,
    )

    exp = service.explain_transaction(payload, top_k=3)
    assert exp.transaction_id == "TX-SHAP-001"
    assert len(exp.all_attributions) > 0
    assert exp.fraud_probability >= 0.0


def test_model_health_endpoint(client):
    """Verify /api/v1/health/model endpoint returns ML status and metadata."""
    res = client.get("/api/v1/health/model")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] in ["healthy", "ready"]
    assert "model_runtime" in data
    assert data["model_runtime"]["is_ready"] is True
    assert "active_model" in data["model_runtime"]
