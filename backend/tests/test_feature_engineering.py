"""Comprehensive test suite for Phase 5 Feature Engineering & Preprocessing Pipeline."""

import numpy as np
import pandas as pd
import pytest

from ml.features.feature_engineer import FraudFeatureEngineer
from ml.preprocessing.pipeline import FullFraudPreprocessor


def create_sample_raw_dataframe(n_rows: int = 40) -> pd.DataFrame:
    """Fixture creating raw transaction batch before feature engineering."""
    np.random.seed(42)
    return pd.DataFrame({
        "transaction_id": [f"TX-{i:05d}" for i in range(n_rows)],
        "customer_id": [f"CUST-{i%8:03d}" for i in range(n_rows)],
        "transaction_hour": np.random.randint(0, 24, n_rows),
        "transaction_day_of_week": np.random.randint(0, 7, n_rows),
        "account_age_days": np.random.randint(10, 1000, n_rows),
        "previous_chargebacks": np.random.choice([0, 1, 2], n_rows, p=[0.8, 0.15, 0.05]),
        "merchant_category": np.random.choice(["Retail", "Electronics", "Travel", "Grocery"], n_rows),
        "transaction_country": np.random.choice(["US", "CA", "GB", "MX"], n_rows),
        "device_type": np.random.choice(["mobile", "web", "pos"], n_rows),
        "transaction_type": np.random.choice(["online_payment", "card_present", "pos_swipe"], n_rows),
        "geo_location_region": np.random.choice(["CA", "NY", "TX", "FL"], n_rows),
        "is_international": np.random.choice([0, 1], n_rows, p=[0.9, 0.1]),
        "is_high_risk_merchant_category": np.random.choice([0, 1], n_rows, p=[0.85, 0.15]),
        "is_weekend": np.random.choice([0, 1], n_rows, p=[0.7, 0.3]),
        "customer_total_transactions_30d": np.random.randint(1, 60, n_rows),
        "customer_risk_score": np.random.uniform(5.0, 95.0, n_rows),  # Candidate leakage
        "transaction_amount": np.random.uniform(10.0, 2500.0, n_rows),
        "avg_transaction_amount_30d_customer": np.random.uniform(20.0, 500.0, n_rows),
        "transaction_velocity_1h": np.random.randint(0, 5, n_rows),
        "transaction_velocity_24h": np.random.randint(1, 15, n_rows),
        "risk_label": np.random.choice([0, 1], n_rows, p=[0.9, 0.1]),
    })


def test_fraud_feature_engineer_generation():
    """Verify FraudFeatureEngineer derives all required behavioural and temporal features."""
    df = create_sample_raw_dataframe(25)
    engineer = FraudFeatureEngineer()
    df_eng = engineer.fit_transform(df)

    # 1. Verify engineered column presence
    expected_engineered = [
        "amount_to_avg_ratio",
        "amount_to_velocity_1h_ratio",
        "velocity_ratio_1h_24h",
        "chargeback_rate_30d",
        "is_night_transaction",
        "sin_hour",
        "cos_hour",
        "sin_day_of_week",
        "cos_day_of_week",
    ]
    for col in expected_engineered:
        assert col in df_eng.columns, f"Engineered feature '{col}' missing"

    # 2. Verify bounds of cyclical encodings [-1.0, 1.0]
    assert df_eng["sin_hour"].between(-1.0, 1.0).all()
    assert df_eng["cos_hour"].between(-1.0, 1.0).all()
    assert df_eng["sin_day_of_week"].between(-1.0, 1.0).all()
    assert df_eng["cos_day_of_week"].between(-1.0, 1.0).all()

    # 3. Verify night transaction flag is binary
    assert set(df_eng["is_night_transaction"].unique()).issubset({0, 1})


def test_leakage_and_identifier_exclusion():
    """Verify target leakage (customer_risk_score) and row identifiers are dropped from feature matrix."""
    df = create_sample_raw_dataframe(20)
    engineer = FraudFeatureEngineer()
    df_eng = engineer.fit_transform(df)

    # Leakage column must be stripped
    assert "customer_risk_score" not in df_eng.columns
    # Primary identifiers must be stripped
    assert "transaction_id" not in df_eng.columns
    assert "customer_id" not in df_eng.columns


def test_full_preprocessing_pipeline_fit_transform():
    """Verify FullFraudPreprocessor returns a clean numeric matrix without NaNs."""
    df = create_sample_raw_dataframe(40)
    X = df.drop(columns=["risk_label"])

    preprocessor = FullFraudPreprocessor()
    X_transformed = preprocessor.fit_transform(X)

    # Must be 2D numpy array
    assert isinstance(X_transformed, np.ndarray)
    assert X_transformed.shape[0] == 40
    assert X_transformed.shape[1] > 20  # Numerical + One-Hot encoded categories

    # Must have no NaNs or Infs
    assert not np.isnan(X_transformed).any()
    assert not np.isinf(X_transformed).any()


def test_preprocessing_handles_missing_values():
    """Verify preprocessor imputes missing numerical and categorical values safely."""
    df = create_sample_raw_dataframe(30)
    X = df.drop(columns=["risk_label"]).copy()

    # Inject nulls
    X.loc[0:5, "transaction_amount"] = np.nan
    X.loc[2:7, "merchant_category"] = None
    X.loc[4:9, "avg_transaction_amount_30d_customer"] = np.nan

    preprocessor = FullFraudPreprocessor()
    X_transformed = preprocessor.fit_transform(X)

    assert not np.isnan(X_transformed).any()
    assert X_transformed.shape[0] == 30


def test_preprocessor_reusability_on_unseen_data():
    """Verify fitted preprocessor can transform a new unseen batch with identical column output."""
    train_df = create_sample_raw_dataframe(50)
    test_df = create_sample_raw_dataframe(15)

    X_train = train_df.drop(columns=["risk_label"])
    X_test = test_df.drop(columns=["risk_label"])

    preprocessor = FullFraudPreprocessor()
    X_train_mat = preprocessor.fit_transform(X_train)
    X_test_mat = preprocessor.transform(X_test)

    # Feature dimensions must match exactly
    assert X_train_mat.shape[1] == X_test_mat.shape[1]
    assert X_test_mat.shape[0] == 15
    assert not np.isnan(X_test_mat).any()


def test_preprocessor_serialization(tmp_path):
    """Verify preprocessor can be saved to disk and reloaded without loss of functionality."""
    df = create_sample_raw_dataframe(30)
    X = df.drop(columns=["risk_label"])

    preprocessor = FullFraudPreprocessor()
    preprocessor.fit(X)

    save_file = tmp_path / "preprocessor.joblib"
    preprocessor.save(save_file)

    # Load from disk
    loaded_preprocessor = FullFraudPreprocessor.load(save_file)
    assert loaded_preprocessor.is_fitted_ is True

    # Transform with loaded preprocessor
    transformed = loaded_preprocessor.transform(X)
    assert transformed.shape[0] == 30
    assert not np.isnan(transformed).any()
