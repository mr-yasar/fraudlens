"""Comprehensive test suite for Phase 11 Transaction Management API."""

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
from backend.app.core.security import get_password_hash, create_access_token
from backend.app.models.user import User
from backend.app.models.customer import Customer
from backend.app.models.transaction import Transaction
from backend.app.models.shap_explanation import ShapExplanation
from backend.app.models.audit_log import AuditLog
from backend.app.schemas.user import UserRole
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
        "transaction_amount": amount,
        "avg_transaction_amount_30d_customer": np.random.exponential(80, n_rows) + 15,
        "transaction_velocity_1h": np.random.poisson(0.5, n_rows),
        "transaction_velocity_24h": np.random.poisson(2.0, n_rows),
        "is_fraud": y,
    })


@pytest.fixture(scope="module", autouse=True)
def setup_transaction_mgmt_env(tmp_path_factory):
    """Train artifacts and initialize test database."""
    tmp_artifacts = tmp_path_factory.mktemp("ml_tx_mgmt_artifacts")
    df = create_sample_training_dataset(150)

    trainer = FraudModelTrainer(config=TrainingConfig(artifact_dir=str(tmp_artifacts), target_column="is_fraud"))
    X_train, y_train, X_val, y_val, X_test, y_test, _ = trainer.prepare_data_splits(df)
    models = trainer.train_all_models(X_train, y_train)
    trainer.save_artifacts()

    selector = ModelSelector(artifact_dir=str(tmp_artifacts), model_version="v1.0.0")
    selector.compare_and_select(models, X_val, y_val, X_test, y_test)

    FraudPredictionService.reset_instance()
    FraudPredictionService.get_instance(artifact_dir=str(tmp_artifacts))

    app.dependency_overrides[get_db] = override_get_db
    Base.metadata.create_all(bind=test_engine)
    db = TestingSessionLocal()

    admin = User(
        name="Admin User",
        email="admin_tx@test.internal",
        password_hash=get_password_hash("AdminPass123!"),
        role=UserRole.ADMIN.value,
        is_active=True,
    )
    investigator = User(
        name="Investigator User",
        email="inv_tx@test.internal",
        password_hash=get_password_hash("InvPass123!"),
        role=UserRole.FRAUD_INVESTIGATOR.value,
        is_active=True,
    )
    db.add_all([admin, investigator])
    db.commit()
    db.close()

    yield

    Base.metadata.drop_all(bind=test_engine)
    app.dependency_overrides.clear()
    FraudPredictionService.reset_instance()


@pytest.fixture
def investigator_token():
    db = TestingSessionLocal()
    user = db.query(User).filter(User.email == "inv_tx@test.internal").first()
    token = create_access_token(subject=str(user.id), role=user.role)
    db.close()
    return token


def test_create_and_persist_transaction(investigator_token):
    client = TestClient(app)
    payload = {
        "transaction_id": "TX-TEST-001",
        "customer_id": "CUST-NEW-01",
        "transaction_hour": 3,
        "transaction_day_of_week": 6,
        "account_age_days": 15.0,
        "previous_chargebacks": 1,
        "merchant_category": "Electronics",
        "transaction_country": "US",
        "device_type": "mobile",
        "transaction_type": "online_payment",
        "geo_location_region": "CA",
        "is_international": 0,
        "is_high_risk_merchant_category": 1,
        "is_weekend": 1,
        "customer_total_transactions_30d": 5.0,
        "transaction_amount": 1250.0,
        "avg_transaction_amount_30d_customer": 80.0,
        "transaction_velocity_1h": 3.0,
        "transaction_velocity_24h": 6.0,
    }

    response = client.post(
        "/api/v1/transactions",
        json=payload,
        headers={"Authorization": f"Bearer {investigator_token}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["transaction_id"] == "TX-TEST-001"
    assert data["customer_id"] == "CUST-NEW-01"
    assert data["amount"] == 1250.0
    assert data["prediction"] in ["FRAUD", "GENUINE"]
    assert 0.0 <= data["fraud_probability"] <= 1.0
    assert 0 <= data["risk_score"] <= 100
    assert data["risk_level"] in ["LOW", "MEDIUM", "HIGH"]
    assert data["model_name"] is not None

    # Verify database persistence
    db = TestingSessionLocal()
    saved_tx = db.query(Transaction).filter(Transaction.transaction_id == "TX-TEST-001").first()
    assert saved_tx is not None
    assert float(saved_tx.amount) == 1250.0
    assert saved_tx.risk_level == data["risk_level"]

    # Verify customer auto-creation
    cust = db.query(Customer).filter(Customer.customer_id == "CUST-NEW-01").first()
    assert cust is not None
    assert cust.account_age_days == 15

    # Verify SHAP explanations persisted
    shap_recs = db.query(ShapExplanation).filter(ShapExplanation.transaction_id == "TX-TEST-001").all()
    assert len(shap_recs) > 0

    db.close()


def test_create_duplicate_transaction_id_rejected(investigator_token):
    client = TestClient(app)
    payload = {
        "transaction_id": "TX-TEST-001",
        "customer_id": "CUST-NEW-01",
        "transaction_hour": 14,
        "transaction_day_of_week": 2,
        "account_age_days": 100.0,
        "previous_chargebacks": 0,
        "merchant_category": "Retail",
        "transaction_country": "US",
        "device_type": "web",
        "transaction_type": "online_payment",
        "geo_location_region": "NY",
        "is_international": 0,
        "is_high_risk_merchant_category": 0,
        "is_weekend": 0,
        "customer_total_transactions_30d": 12.0,
        "transaction_amount": 50.0,
        "avg_transaction_amount_30d_customer": 45.0,
        "transaction_velocity_1h": 0.0,
        "transaction_velocity_24h": 1.0,
    }
    response = client.post(
        "/api/v1/transactions",
        json=payload,
        headers={"Authorization": f"Bearer {investigator_token}"},
    )
    assert response.status_code == 409
    assert "already exists" in response.json()["detail"].lower()


def test_list_transactions_with_filters(investigator_token):
    client = TestClient(app)
    # Add another low-risk transaction
    payload2 = {
        "transaction_id": "TX-TEST-002",
        "customer_id": "CUST-NEW-02",
        "transaction_hour": 12,
        "transaction_day_of_week": 3,
        "account_age_days": 300.0,
        "previous_chargebacks": 0,
        "merchant_category": "Grocery",
        "transaction_country": "US",
        "device_type": "pos",
        "transaction_type": "card_present",
        "geo_location_region": "TX",
        "is_international": 0,
        "is_high_risk_merchant_category": 0,
        "is_weekend": 0,
        "customer_total_transactions_30d": 20.0,
        "transaction_amount": 25.0,
        "avg_transaction_amount_30d_customer": 30.0,
        "transaction_velocity_1h": 0.0,
        "transaction_velocity_24h": 1.0,
    }
    client.post(
        "/api/v1/transactions",
        json=payload2,
        headers={"Authorization": f"Bearer {investigator_token}"},
    )

    # List all
    res = client.get(
        "/api/v1/transactions",
        headers={"Authorization": f"Bearer {investigator_token}"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["total"] >= 2

    # Filter by search
    res_search = client.get(
        "/api/v1/transactions?search=TEST-002",
        headers={"Authorization": f"Bearer {investigator_token}"},
    )
    assert res_search.status_code == 200
    assert res_search.json()["total"] == 1
    assert res_search.json()["items"][0]["transaction_id"] == "TX-TEST-002"

    # Filter by amount range
    res_amt = client.get(
        "/api/v1/transactions?min_amount=1000",
        headers={"Authorization": f"Bearer {investigator_token}"},
    )
    assert res_amt.status_code == 200
    assert res_amt.json()["total"] == 1
    assert res_amt.json()["items"][0]["transaction_id"] == "TX-TEST-001"


def test_get_transaction_detail_and_explanation(investigator_token):
    client = TestClient(app)
    # Detail
    res = client.get(
        "/api/v1/transactions/TX-TEST-001",
        headers={"Authorization": f"Bearer {investigator_token}"},
    )
    assert res.status_code == 200
    detail = res.json()
    assert detail["transaction_id"] == "TX-TEST-001"
    assert detail["model_name"] is not None

    # SHAP Explanation endpoint
    res_exp = client.get(
        "/api/v1/transactions/TX-TEST-001/explanation",
        headers={"Authorization": f"Bearer {investigator_token}"},
    )
    assert res_exp.status_code == 200
    exp_data = res_exp.json()
    assert exp_data["transaction_id"] == "TX-TEST-001"
    assert "top_risk_increasing_factors" in exp_data
    assert "top_risk_decreasing_factors" in exp_data
    assert len(exp_data["all_attributions"]) > 0


def test_nonexistent_transaction_returns_404(investigator_token):
    client = TestClient(app)
    res = client.get(
        "/api/v1/transactions/TX-NONEXISTENT",
        headers={"Authorization": f"Bearer {investigator_token}"},
    )
    assert res.status_code == 404

    res_exp = client.get(
        "/api/v1/transactions/TX-NONEXISTENT/explanation",
        headers={"Authorization": f"Bearer {investigator_token}"},
    )
    assert res_exp.status_code == 404
