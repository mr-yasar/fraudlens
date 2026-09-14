"""Comprehensive test suite for Phase 8 Fraud Prediction Engine & API."""

from pathlib import Path
import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.main import app
from backend.app.core.database import Base, get_db
from backend.app.core.security import get_password_hash
from backend.app.models.user import User
from backend.app.schemas.user import UserRole
from backend.app.schemas.prediction import TransactionPredictionInput
from backend.app.services.prediction_service import FraudPredictionService
from ml.training.trainer import FraudModelTrainer, TrainingConfig
from ml.evaluation.model_selector import ModelSelector

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


def create_sample_training_dataset(n_rows: int = 150) -> pd.DataFrame:
    """Fixture producing synthetic imbalanced transaction dataset."""
    np.random.seed(42)
    y = np.array([0] * (n_rows - 20) + [1] * 20)
    amount = np.where(y == 1, np.random.exponential(500, n_rows) + 200, np.random.exponential(50, n_rows) + 10)

    return pd.DataFrame({
        "transaction_id": [f"TX-{i:05d}" for i in range(n_rows)],
        "customer_id": [f"CUST-{i%15:03d}" for i in range(n_rows)],
        "transaction_hour": np.random.randint(0, 24, n_rows),
        "transaction_day_of_week": np.random.randint(0, 7, n_rows),
        "account_age_days": np.random.randint(5, 1000, n_rows),
        "previous_chargebacks": np.random.choice([0, 1, 2], n_rows, p=[0.8, 0.15, 0.05]),
        "merchant_category": np.random.choice(["Retail", "Electronics", "Travel", "Grocery"], n_rows),
        "transaction_country": np.random.choice(["US", "CA", "GB"], n_rows),
        "device_type": np.random.choice(["mobile", "web", "pos"], n_rows),
        "transaction_type": np.random.choice(["online_payment", "card_present"], n_rows),
        "geo_location_region": np.random.choice(["CA", "NY", "TX"], n_rows),
        "is_international": np.random.choice([0, 1], n_rows, p=[0.9, 0.1]),
        "is_high_risk_merchant_category": np.random.choice([0, 1], n_rows, p=[0.85, 0.15]),
        "is_weekend": np.random.choice([0, 1], n_rows, p=[0.7, 0.3]),
        "customer_total_transactions_30d": np.random.randint(1, 50, n_rows),
        "customer_risk_score": np.random.uniform(5.0, 95.0, n_rows),
        "transaction_amount": amount,
        "avg_transaction_amount_30d_customer": np.random.uniform(20.0, 300.0, n_rows),
        "transaction_velocity_1h": np.random.randint(0, 5, n_rows),
        "transaction_velocity_24h": np.random.randint(1, 15, n_rows),
        "risk_label": y,
    })


@pytest.fixture(scope="module", autouse=True)
def setup_test_environment(tmp_path_factory):
    """Setup test database, train initial test model artifact, and configure prediction service."""
    app.dependency_overrides[get_db] = override_get_db
    Base.metadata.create_all(bind=test_engine)
    db = TestingSessionLocal()

    # Seed Admin & Investigator users
    admin = User(
        name="Test Admin",
        email="admin@test.internal",
        password_hash=get_password_hash("AdminPass123!"),
        role=UserRole.ADMIN.value,
        is_active=True,
    )
    investigator = User(
        name="Test Investigator",
        email="investigator@test.internal",
        password_hash=get_password_hash("InvestigatorPass123!"),
        role=UserRole.FRAUD_INVESTIGATOR.value,
        is_active=True,
    )
    db.add_all([admin, investigator])
    db.commit()
    db.close()

    # Create temporary artifacts directory
    artifact_dir = tmp_path_factory.mktemp("ml_artifacts")
    df = create_sample_training_dataset(150)

    # Train and select active model
    trainer = FraudModelTrainer(config=TrainingConfig(artifact_dir=str(artifact_dir)))
    X_train, y_train, X_val, y_val, X_test, y_test, _ = trainer.prepare_data_splits(df)
    models = trainer.train_all_models(X_train, y_train)

    # Save artifacts & select active model
    trainer.save_artifacts()
    selector = ModelSelector(artifact_dir=str(artifact_dir), model_version="v1.0.0")
    selector.compare_and_select(models, X_val, y_val, X_test, y_test)

    # Initialize PredictionService singleton with test artifact directory
    FraudPredictionService.reset_instance()
    FraudPredictionService.get_instance(artifact_dir=str(artifact_dir))

    yield

    Base.metadata.drop_all(bind=test_engine)
    app.dependency_overrides.clear()
    FraudPredictionService.reset_instance()


@pytest.fixture
def client():
    return TestClient(app)


def get_investigator_token(client):
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"email": "investigator@test.internal", "password": "InvestigatorPass123!"},
    )
    return login_resp.json()["access_token"]


def sample_transaction_payload() -> dict:
    return {
        "transaction_id": "TX-99881",
        "customer_id": "CUST-0012",
        "transaction_hour": 14,
        "transaction_day_of_week": 3,
        "account_age_days": 240.0,
        "previous_chargebacks": 0,
        "merchant_category": "Electronics",
        "transaction_country": "US",
        "device_type": "mobile",
        "transaction_type": "online_payment",
        "geo_location_region": "CA",
        "is_international": 0,
        "is_high_risk_merchant_category": 0,
        "is_weekend": 0,
        "customer_total_transactions_30d": 15.0,
        "transaction_amount": 145.50,
        "avg_transaction_amount_30d_customer": 120.00,
        "transaction_velocity_1h": 1.0,
        "transaction_velocity_24h": 3.0,
    }


def test_valid_prediction_api(client):
    """Verify POST /api/v1/predict returns valid prediction schema and probability in [0, 1]."""
    token = get_investigator_token(client)
    payload = sample_transaction_payload()

    response = client.post(
        "/api/v1/predict",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
    )
    assert response.status_code == 200
    data = response.json()

    assert data["prediction"] in ["FRAUD", "GENUINE"]
    assert 0.0 <= data["fraud_probability"] <= 1.0
    assert "model_name" in data
    assert "model_version" in data
    assert "threshold_used" in data
    assert data["transaction_id"] == "TX-99881"


def test_prediction_service_threshold_behavior():
    """Verify changing decision threshold changes prediction label without altering probability."""
    service = FraudPredictionService.get_instance()
    input_schema = TransactionPredictionInput(**sample_transaction_payload())

    # Test with very low threshold (0.001 -> should be classified as FRAUD)
    res_low = service.predict_transaction(input_schema, threshold_override=0.0001)
    # Test with very high threshold (0.999 -> should be classified as GENUINE)
    res_high = service.predict_transaction(input_schema, threshold_override=0.9999)

    # Probabilities must be identical
    assert res_low.fraud_probability == res_high.fraud_probability
    assert res_low.prediction == "FRAUD"
    assert res_high.prediction == "GENUINE"


def test_prediction_missing_required_field(client):
    """Verify 422 Unprocessable Entity when a mandatory feature (e.g. transaction_amount) is missing."""
    token = get_investigator_token(client)
    payload = sample_transaction_payload()
    del payload["transaction_amount"]

    response = client.post(
        "/api/v1/predict",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
    )
    assert response.status_code == 422


def test_prediction_invalid_out_of_bounds_value(client):
    """Verify 422 Unprocessable Entity when hour > 23 or amount <= 0."""
    token = get_investigator_token(client)
    payload = sample_transaction_payload()
    payload["transaction_hour"] = 35  # Invalid hour

    response = client.post(
        "/api/v1/predict",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
    )
    assert response.status_code == 422


def test_prediction_unauthenticated_denied(client):
    """Verify 401 Unauthorized when no auth token is provided."""
    payload = sample_transaction_payload()
    response = client.post("/api/v1/predict", json=payload)
    assert response.status_code == 401
