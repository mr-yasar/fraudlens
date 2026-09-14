"""Comprehensive test suite for Phase 14 Admin ML & Dataset Management."""

import io
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
from backend.app.models.model_version import ModelVersion
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
def setup_admin_ml_test_db():
    """Setup test database tables and seed test users."""
    app.dependency_overrides[get_db] = override_get_db
    Base.metadata.create_all(bind=test_engine)
    db = TestingSessionLocal()

    admin = User(
        name="Admin User",
        email="admin_ml@test.internal",
        password_hash=get_password_hash("AdminPass123!"),
        role=UserRole.ADMIN.value,
        is_active=True,
    )
    investigator = User(
        name="Investigator User",
        email="inv_ml@test.internal",
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


@pytest.fixture
def admin_token():
    db = TestingSessionLocal()
    user = db.query(User).filter(User.email == "admin_ml@test.internal").first()
    token = create_access_token(subject=str(user.id), role=user.role)
    db.close()
    return token


@pytest.fixture
def investigator_token():
    db = TestingSessionLocal()
    user = db.query(User).filter(User.email == "inv_ml@test.internal").first()
    token = create_access_token(subject=str(user.id), role=user.role)
    db.close()
    return token


def test_admin_dataset_validate_endpoint(admin_token, investigator_token):
    client = TestClient(app)
    df = create_sample_training_dataset(50)
    csv_bytes = df.to_csv(index=False).encode("utf-8")

    # 1. Investigator is rejected (403 Forbidden)
    res_inv = client.post(
        "/api/v1/admin/datasets/validate",
        files={"file": ("dataset.csv", io.BytesIO(csv_bytes), "text/csv")},
        headers={"Authorization": f"Bearer {investigator_token}"},
    )
    assert res_inv.status_code == 403

    # 2. Admin succeeds
    res_admin = client.post(
        "/api/v1/admin/datasets/validate",
        files={"file": ("dataset.csv", io.BytesIO(csv_bytes), "text/csv")},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res_admin.status_code == 200
    data = res_admin.json()
    assert data["is_valid"] is True
    assert data["file_format"]["total_rows"] == 50


def test_admin_dataset_status_endpoint(admin_token, investigator_token):
    client = TestClient(app)
    # Investigator rejected
    res_inv = client.get(
        "/api/v1/admin/datasets/status",
        headers={"Authorization": f"Bearer {investigator_token}"},
    )
    assert res_inv.status_code == 403

    # Admin access
    res_admin = client.get(
        "/api/v1/admin/datasets/status",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res_admin.status_code == 200
    data = res_admin.json()
    assert "dataset_name" in data
    assert "target_distribution" in data


def test_admin_models_list_and_comparison(admin_token, investigator_token):
    client = TestClient(app)
    # Investigator rejected
    res_inv = client.get(
        "/api/v1/admin/models",
        headers={"Authorization": f"Bearer {investigator_token}"},
    )
    assert res_inv.status_code == 403

    # Admin lists models
    res_admin = client.get(
        "/api/v1/admin/models",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res_admin.status_code == 200
    data = res_admin.json()
    assert "models" in data
    assert len(data["models"]) >= 1
    assert data["active_model"] is not None

    # Comparison matrix
    res_comp = client.get(
        "/api/v1/admin/models/comparison",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res_comp.status_code == 200
    comp_data = res_comp.json()
    assert "comparison" in comp_data
    assert "selection_criteria" in comp_data


def test_admin_model_training_workflow(admin_token, investigator_token, tmp_path):
    client = TestClient(app)
    # Create temporary dataset file
    ds_path = tmp_path / "train_data.csv"
    df = create_sample_training_dataset(120)
    df.to_csv(ds_path, index=False)

    # Investigator rejected
    res_inv = client.post(
        "/api/v1/admin/models/train",
        json={"dataset_path": str(ds_path), "model_version": "v1.1.0"},
        headers={"Authorization": f"Bearer {investigator_token}"},
    )
    assert res_inv.status_code == 403

    # Admin trains models
    res_admin = client.post(
        "/api/v1/admin/models/train",
        json={"dataset_path": str(ds_path), "model_version": "v1.1.0"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res_admin.status_code == 200
    train_res = res_admin.json()
    assert train_res["selected_model"] in ["logistic_regression", "random_forest", "xgboost", "ensemble_stacking"]
    assert len(train_res["trained_models"]) >= 3

    # Verify model_versions database records
    db = TestingSessionLocal()
    mv_records = db.query(ModelVersion).filter(ModelVersion.version == "v1.1.0").all()
    assert len(mv_records) >= 3
    active_mvs = [mv for mv in mv_records if mv.is_active]
    assert len(active_mvs) == 1
    db.close()


def test_admin_model_activation_and_safety_preservation(admin_token, investigator_token):
    client = TestClient(app)
    # Investigator rejected
    res_inv = client.post(
        "/api/v1/admin/models/xgboost/activate",
        headers={"Authorization": f"Bearer {investigator_token}"},
    )
    assert res_inv.status_code == 403

    # Admin activates XGBoost
    res_act = client.post(
        "/api/v1/admin/models/xgboost/activate",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res_act.status_code == 200
    act_data = res_act.json()
    assert act_data["status"] == "MODEL_ACTIVATION_SUCCESSFUL"
    assert act_data["active_model"] == "xgboost"

    # Activation of nonexistent model rejected without breaking active model
    res_invalid = client.post(
        "/api/v1/admin/models/nonexistent_model/activate",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res_invalid.status_code == 404

    # Verify prediction service still points to active model safely
    service = FraudPredictionService.get_instance()
    assert service.is_ready is True
    assert service.model_name == "xgboost"
