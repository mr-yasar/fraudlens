"""Comprehensive test suite for Phase 10 SHAP & Explainable AI Engine."""

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
from ml.explainability.shap_explainer import FraudShapExplainer

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
    app.dependency_overrides[get_db] = override_get_db
    Base.metadata.create_all(bind=test_engine)
    db = TestingSessionLocal()

    investigator = User(
        name="Lead Investigator",
        email="investigator@test.internal",
        password_hash=get_password_hash("InvestigatorPass123!"),
        role=UserRole.FRAUD_INVESTIGATOR.value,
        is_active=True,
    )
    db.add(investigator)
    db.commit()
    db.close()

    artifact_dir = tmp_path_factory.mktemp("ml_shap_artifacts")
    df = create_sample_training_dataset(150)

    trainer = FraudModelTrainer(config=TrainingConfig(artifact_dir=str(artifact_dir)))
    X_train, y_train, X_val, y_val, X_test, y_test, _ = trainer.prepare_data_splits(df)
    models = trainer.train_all_models(X_train, y_train)
    trainer.save_artifacts()

    selector = ModelSelector(artifact_dir=str(artifact_dir), model_version="v1.0.0")
    selector.compare_and_select(models, X_val, y_val, X_test, y_test)

    # Initialize PredictionService with SHAP explainer
    FraudPredictionService.reset_instance()
    service = FraudPredictionService.get_instance(artifact_dir=str(artifact_dir))

    # Precompute global explanation
    service.get_global_explanation()

    yield

    Base.metadata.drop_all(bind=test_engine)
    app.dependency_overrides.clear()
    FraudPredictionService.reset_instance()


@pytest.fixture
def client():
    return TestClient(app)


def get_token(client):
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"email": "investigator@test.internal", "password": "InvestigatorPass123!"},
    )
    return login_resp.json()["access_token"]


def sample_transaction_payload() -> dict:
    return {
        "transaction_id": "TX-SHAP-001",
        "customer_id": "CUST-992",
        "transaction_hour": 2,  # Night window
        "transaction_day_of_week": 6,
        "account_age_days": 12.0,  # Young account
        "previous_chargebacks": 2,  # Disputes
        "merchant_category": "Electronics",
        "transaction_country": "US",
        "device_type": "mobile",
        "transaction_type": "online_payment",
        "geo_location_region": "CA",
        "is_international": 1,
        "is_high_risk_merchant_category": 1,
        "is_weekend": 1,
        "customer_total_transactions_30d": 8.0,
        "transaction_amount": 1850.00,  # Surge
        "avg_transaction_amount_30d_customer": 100.00,
        "transaction_velocity_1h": 4.0,
        "transaction_velocity_24h": 5.0,
    }


def test_shap_explainer_local_attribution():
    """Verify FraudShapExplainer calculates aligned feature attributions with positive/negative impacts."""
    service = FraudPredictionService.get_instance()
    input_schema = TransactionPredictionInput(**sample_transaction_payload())

    explanation = service.explain_transaction(input_schema, top_k=5)

    assert explanation.transaction_id == "TX-SHAP-001"
    assert len(explanation.all_attributions) > 10
    assert len(explanation.top_risk_increasing_factors) > 0

    # Verify attribution structure
    for attr in explanation.all_attributions:
        assert "feature_name" in attr
        assert "shap_value" in attr
        assert "impact" in attr
        assert attr["impact"] in ["INCREASES_FRAUD_RISK", "DECREASES_FRAUD_RISK"]
        assert attr["importance_rank"] >= 1
        assert "detail" in attr


def test_api_explain_local_endpoint(client):
    """Verify POST /api/v1/explain returns full local SHAP report."""
    token = get_token(client)
    payload = sample_transaction_payload()

    response = client.post(
        "/api/v1/explain?top_k=4",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
    )
    assert response.status_code == 200
    data = response.json()

    assert data["transaction_id"] == "TX-SHAP-001"
    assert "base_value" in data
    assert "top_risk_increasing_factors" in data
    assert "top_risk_decreasing_factors" in data
    assert len(data["top_risk_increasing_factors"]) <= 4


def test_api_explain_global_endpoint(client):
    """Verify GET /api/v1/explain/global returns ranked feature importance."""
    token = get_token(client)

    response = client.get(
        "/api/v1/explain/global",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()

    assert "model_name" in data
    assert "feature_importance_ranking" in data
    assert len(data["feature_importance_ranking"]) > 10

    first_item = data["feature_importance_ranking"][0]
    assert first_item["rank"] == 1
    assert "mean_abs_shap" in first_item
    assert first_item["mean_abs_shap"] >= 0.0


def test_enhanced_predict_api_includes_risk_and_shap(client):
    """Verify POST /api/v1/predict returns risk score (0-100), risk level, and top SHAP factors."""
    token = get_token(client)
    payload = sample_transaction_payload()

    response = client.post(
        "/api/v1/predict",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
    )
    assert response.status_code == 200
    data = response.json()

    assert "risk_score" in data
    assert 0 <= data["risk_score"] <= 100
    assert data["risk_level"] in ["LOW", "MEDIUM", "HIGH"]
    assert "risk_factors" in data
    assert len(data["risk_factors"]) > 0
    assert "top_shap_factors" in data
