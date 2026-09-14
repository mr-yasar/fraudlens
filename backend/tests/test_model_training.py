"""Comprehensive test suite for Phase 6 ML Model Training, Imbalance Handling & Evaluation."""

import json
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
import pytest

from ml.training.trainer import FraudModelTrainer, TrainingConfig


def create_imbalanced_fraud_dataset(n_rows: int = 200, fraud_ratio: float = 0.1) -> pd.DataFrame:
    """Helper generating an imbalanced dataset fixture for end-to-end training tests."""
    np.random.seed(42)
    n_fraud = int(n_rows * fraud_ratio)
    n_normal = n_rows - n_fraud

    y = np.array([0] * n_normal + [1] * n_fraud)

    # Correlate some features realistically without target leakage
    amount = np.where(y == 1, np.random.exponential(500, n_rows) + 200, np.random.exponential(50, n_rows) + 10)
    velocity_1h = np.where(y == 1, np.random.poisson(4, n_rows), np.random.poisson(1, n_rows))
    velocity_24h = np.where(y == 1, np.random.poisson(8, n_rows), np.random.poisson(2, n_rows))
    chargebacks = np.where(y == 1, np.random.choice([0, 1, 2], n_rows, p=[0.5, 0.3, 0.2]), np.random.choice([0, 1], n_rows, p=[0.95, 0.05]))

    return pd.DataFrame({
        "transaction_id": [f"TX-{i:05d}" for i in range(n_rows)],
        "customer_id": [f"CUST-{i%20:03d}" for i in range(n_rows)],
        "transaction_hour": np.random.randint(0, 24, n_rows),
        "transaction_day_of_week": np.random.randint(0, 7, n_rows),
        "account_age_days": np.random.randint(5, 1200, n_rows),
        "previous_chargebacks": chargebacks,
        "merchant_category": np.random.choice(["Retail", "Electronics", "Travel", "Grocery", "Gaming"], n_rows),
        "transaction_country": np.random.choice(["US", "CA", "GB", "AU", "DE"], n_rows),
        "device_type": np.random.choice(["mobile", "web", "pos"], n_rows),
        "transaction_type": np.random.choice(["online_payment", "card_present", "pos_swipe"], n_rows),
        "geo_location_region": np.random.choice(["CA", "NY", "TX", "FL", "IL"], n_rows),
        "is_international": np.random.choice([0, 1], n_rows, p=[0.85, 0.15]),
        "is_high_risk_merchant_category": np.random.choice([0, 1], n_rows, p=[0.8, 0.2]),
        "is_weekend": np.random.choice([0, 1], n_rows, p=[0.7, 0.3]),
        "customer_total_transactions_30d": np.random.randint(1, 80, n_rows),
        "customer_risk_score": np.random.uniform(5.0, 95.0, n_rows),  # Excluded by feature engineer
        "transaction_amount": amount,
        "avg_transaction_amount_30d_customer": np.random.uniform(20.0, 300.0, n_rows),
        "transaction_velocity_1h": velocity_1h,
        "transaction_velocity_24h": velocity_24h,
        "risk_label": y,
    })


def test_stratified_data_splits():
    """Verify stratified train/val/test splits maintain correct ratios and fraud proportions."""
    df = create_imbalanced_fraud_dataset(200, fraud_ratio=0.1)
    trainer = FraudModelTrainer()

    X_train, y_train, X_val, y_val, X_test, y_test, split_info = trainer.prepare_data_splits(df)

    # Check sample counts (approx 70% / 15% / 15%)
    assert split_info["total_samples"] == 200
    assert split_info["train_samples"] + split_info["val_samples"] + split_info["test_samples"] == 200
    assert 135 <= split_info["train_samples"] <= 145
    assert 25 <= split_info["val_samples"] <= 35
    assert 25 <= split_info["test_samples"] <= 35

    # Stratified target presence
    assert np.sum(y_train == 1) > 0
    assert np.sum(y_val == 1) > 0
    assert np.sum(y_test == 1) > 0


def test_all_models_training_and_evaluation(tmp_path):
    """Verify Logistic Regression, Random Forest, and XGBoost train and produce real evaluation metrics."""
    df = create_imbalanced_fraud_dataset(200, fraud_ratio=0.1)
    config = TrainingConfig(
        artifact_dir=str(tmp_path / "artifacts"),
        model_version="v1.0.0-test",
    )
    trainer = FraudModelTrainer(config=config)
    results = trainer.run_pipeline(df)

    test_metrics = results["evaluations"]["test_metrics"]

    # Must contain all 3 models
    assert "logistic_regression" in test_metrics
    assert "random_forest" in test_metrics
    assert "xgboost" in test_metrics

    # Check metrics validity on all models
    required_metrics = [
        "accuracy",
        "precision",
        "recall",
        "f1_score",
        "roc_auc",
        "pr_auc",
        "false_positive_rate",
        "false_negative_rate",
        "confusion_matrix",
    ]
    for model_name, metrics in test_metrics.items():
        for m in required_metrics:
            assert m in metrics, f"Metric '{m}' missing in {model_name}"
            if m != "confusion_matrix":
                assert 0.0 <= metrics[m] <= 1.0, f"Metric '{m}' value {metrics[m]} out of bounds [0, 1]"

        cm = metrics["confusion_matrix"]
        assert "true_negatives" in cm
        assert "false_positives" in cm
        assert "false_negatives" in cm
        assert "true_positives" in cm
        assert sum(cm.values()) == results["evaluations"]["data_splits"]["test_samples"]


def test_artifacts_saved_and_reloadable(tmp_path):
    """Verify saved models, preprocessor, and JSON metadata are serialized and reloadable."""
    df = create_imbalanced_fraud_dataset(150, fraud_ratio=0.12)
    artifact_dir = tmp_path / "saved_models"
    config = TrainingConfig(artifact_dir=str(artifact_dir))

    trainer = FraudModelTrainer(config=config)
    trainer.run_pipeline(df)

    # 1. Verify files exist on disk
    expected_files = [
        "logistic_regression.joblib",
        "random_forest.joblib",
        "xgboost.joblib",
        "preprocessor.joblib",
        "feature_metadata.json",
        "evaluation_results.json",
        "training_metadata.json",
    ]
    for filename in expected_files:
        filepath = artifact_dir / filename
        assert filepath.exists(), f"Artifact '{filename}' was not created"

    # 2. Reload XGBoost model and verify inference
    xgb_model = joblib.load(artifact_dir / "xgboost.joblib")
    preprocessor = joblib.load(artifact_dir / "preprocessor.joblib")

    sample_X = df.drop(columns=["risk_label"]).head(5)
    sample_mat = preprocessor.transform(sample_X)
    probs = xgb_model.predict_proba(sample_mat)

    assert probs.shape == (5, 2)
    assert np.all(probs >= 0.0) and np.all(probs <= 1.0)

    # 3. Read evaluation JSON
    with open(artifact_dir / "evaluation_results.json", "r", encoding="utf-8") as f:
        eval_json = json.load(f)
    assert "test_metrics" in eval_json
    assert "validation_metrics" in eval_json
