"""Comprehensive test suite for Phase 4 Dataset Integration, Validation & Feature Leakage Audit."""

import io
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
from ml.validation.dataset_validator import DatasetValidator, DatasetSchema

# Test Database setup for API testing
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
def setup_test_app():
    app.dependency_overrides[get_db] = override_get_db
    Base.metadata.create_all(bind=test_engine)
    db = TestingSessionLocal()

    admin = User(
        name="Test Admin",
        email="admin@test.internal",
        password_hash=get_password_hash("AdminPass123!"),
        role=UserRole.ADMIN.value,
        is_active=True,
    )
    db.add(admin)
    db.commit()
    db.close()

    yield

    Base.metadata.drop_all(bind=test_engine)
    app.dependency_overrides.clear()


@pytest.fixture
def client():
    return TestClient(app)


def create_sample_valid_dataframe(n_rows: int = 50) -> pd.DataFrame:
    """Helper creating a synthetically structured DataFrame adhering to valid schema."""
    return pd.DataFrame({
        "transaction_id": [f"TX-{i:05d}" for i in range(n_rows)],
        "customer_id": [f"CUST-{i%10:03d}" for i in range(n_rows)],
        "transaction_hour": [14] * n_rows,
        "transaction_day_of_week": [3] * n_rows,
        "account_age_days": [180] * n_rows,
        "previous_chargebacks": [0] * n_rows,
        "merchant_category": ["Retail"] * n_rows,
        "transaction_country": ["US"] * n_rows,
        "device_type": ["mobile"] * n_rows,
        "transaction_type": ["online_payment"] * n_rows,
        "geo_location_region": ["CA"] * n_rows,
        "is_international": [0] * n_rows,
        "is_high_risk_merchant_category": [0] * n_rows,
        "is_weekend": [0] * n_rows,
        "customer_total_transactions_30d": [12] * n_rows,
        "customer_risk_score": [15.2] * n_rows,
        "transaction_amount": [120.50] * n_rows,
        "avg_transaction_amount_30d_customer": [95.00] * n_rows,
        "transaction_velocity_1h": [1] * n_rows,
        "transaction_velocity_24h": [3] * n_rows,
        "risk_label": [0] * (n_rows - 5) + [1] * 5,
    })


def test_valid_schema_passes_validation():
    """Verify clean dataset passes all checks."""
    df = create_sample_valid_dataframe(50)
    validator = DatasetValidator()
    result = validator.validate_dataframe(df)

    assert result.is_valid is True
    assert len(result.errors) == 0
    assert result.schema_check["passed"] is True
    assert result.target_analysis["has_target"] is True
    assert result.target_analysis["is_binary"] is True
    assert result.target_analysis["fraud_count"] == 5
    assert result.target_analysis["normal_count"] == 45


def test_missing_required_column_detection():
    """Verify error is raised when required columns (e.g. transaction_amount) are missing."""
    df = create_sample_valid_dataframe(20)
    df_missing = df.drop(columns=["transaction_amount", "merchant_category"])

    validator = DatasetValidator()
    result = validator.validate_dataframe(df_missing)

    assert result.is_valid is False
    assert result.schema_check["passed"] is False
    assert "transaction_amount" in result.schema_check["missing_required_columns"]
    assert "merchant_category" in result.schema_check["missing_required_columns"]
    assert any("Missing required columns" in err for err in result.errors)


def test_invalid_target_values_detection():
    """Verify error is raised when target column contains invalid values outside {0, 1}."""
    df = create_sample_valid_dataframe(20)
    df.loc[0, "risk_label"] = 99  # Invalid class

    validator = DatasetValidator()
    result = validator.validate_dataframe(df)

    assert result.is_valid is False
    assert result.target_analysis["is_binary"] is False
    assert any("contains invalid values" in err for err in result.errors)


def test_duplicate_transaction_id_detection():
    """Verify duplicate primary key transaction_id is flagged as error."""
    df = create_sample_valid_dataframe(20)
    df.loc[1, "transaction_id"] = df.loc[0, "transaction_id"]  # Duplicate PK

    validator = DatasetValidator()
    result = validator.validate_dataframe(df)

    assert result.is_valid is False
    assert result.duplicates["duplicate_transaction_ids"] > 0
    assert any("duplicate transaction_id" in err for err in result.errors)


def test_missing_value_detection_and_reporting():
    """Verify missing values are quantified and reported per column."""
    df = create_sample_valid_dataframe(30)
    df.loc[0:5, "device_type"] = None
    df.loc[0:2, "account_age_days"] = None

    validator = DatasetValidator()
    result = validator.validate_dataframe(df)

    assert result.missing_values["has_missing_values"] is True
    assert result.missing_values["missing_counts"]["device_type"] == 6
    assert result.missing_values["missing_counts"]["account_age_days"] == 3


def test_suspicious_values_detection():
    """Verify out-of-bounds hour and negative amount values are flagged."""
    df = create_sample_valid_dataframe(20)
    df.loc[0, "transaction_hour"] = 28  # Invalid hour > 23
    df.loc[1, "transaction_amount"] = -50.0  # Invalid negative amount

    validator = DatasetValidator()
    result = validator.validate_dataframe(df)

    assert result.suspicious_values["has_suspicious_values"] is True
    assert "transaction_hour_above_max_23" in result.suspicious_values["suspicious_counts"]
    assert "transaction_amount_below_min_0.01" in result.suspicious_values["suspicious_counts"]


def test_leakage_audit_logic():
    """Verify leakage audit properly excludes risk scores, identifiers, and high correlation proxies."""
    df = create_sample_valid_dataframe(50)
    # Add a synthetic perfect leak feature (|r| = 1.0)
    df["perfect_leak_flag"] = df["risk_label"] * 100.0

    validator = DatasetValidator()
    leakage = validator.audit_leakage(df)

    excluded_names = [item["feature"] for item in leakage["excluded_features"]]
    # 1. customer_risk_score must be excluded
    assert "customer_risk_score" in excluded_names
    # 2. transaction_id must be excluded
    assert "transaction_id" in excluded_names
    # 3. perfect_leak_flag must be excluded due to extreme correlation
    assert "perfect_leak_flag" in excluded_names

    # 4. Safe features list must include baseline operational features
    safe_names = [item["feature"] for item in leakage["safe_features"]]
    assert "transaction_amount" in safe_names
    assert "transaction_hour" in safe_names
    assert "account_age_days" in safe_names


def test_get_dataset_schema_endpoint(client):
    """Verify GET /api/v1/datasets/schema endpoint returns schema metadata."""
    response = client.get("/api/v1/datasets/schema")
    assert response.status_code == 200
    data = response.json()
    assert data["target_column"] == "risk_label"
    assert "expected_columns" in data
    assert "transaction_amount" in data["expected_columns"]


def test_dataset_validate_upload_endpoint(client):
    """Verify POST /api/v1/datasets/validate endpoint performs audit via file upload."""
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@test.internal", "password": "AdminPass123!"},
    )
    token = login_resp.json()["access_token"]

    df = create_sample_valid_dataframe(30)
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)
    csv_bytes = csv_buffer.getvalue().encode("utf-8")

    response = client.post(
        "/api/v1/datasets/validate",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("fraud_dataset.csv", csv_bytes, "text/csv")},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["is_valid"] is True
    assert data["file_format"]["total_rows"] == 30
    assert data["target_analysis"]["has_target"] is True
    assert "leakage_audit" in data
