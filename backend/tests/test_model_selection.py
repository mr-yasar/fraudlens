"""Comprehensive test suite for Phase 7 Model Evaluation, Threshold Optimization & Selection."""

import json
from pathlib import Path
import numpy as np
import pandas as pd
import pytest
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier

from ml.evaluation.model_selector import ModelSelector
from ml.training.trainer import FraudModelTrainer, TrainingConfig


def create_sample_training_dataset(n_rows: int = 250, fraud_ratio: float = 0.12) -> pd.DataFrame:
    """Fixture producing synthetic imbalanced transaction dataset."""
    np.random.seed(42)
    n_fraud = int(n_rows * fraud_ratio)
    n_normal = n_rows - n_fraud

    y = np.array([0] * n_normal + [1] * n_fraud)

    amount = np.where(y == 1, np.random.exponential(600, n_rows) + 150, np.random.exponential(60, n_rows) + 10)
    velocity_1h = np.where(y == 1, np.random.poisson(5, n_rows), np.random.poisson(1, n_rows))
    velocity_24h = np.where(y == 1, np.random.poisson(9, n_rows), np.random.poisson(2, n_rows))
    chargebacks = np.where(y == 1, np.random.choice([0, 1, 2], n_rows, p=[0.4, 0.4, 0.2]), np.random.choice([0, 1], n_rows, p=[0.95, 0.05]))

    return pd.DataFrame({
        "transaction_id": [f"TX-{i:05d}" for i in range(n_rows)],
        "customer_id": [f"CUST-{i%25:03d}" for i in range(n_rows)],
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
        "customer_risk_score": np.random.uniform(5.0, 95.0, n_rows),
        "transaction_amount": amount,
        "avg_transaction_amount_30d_customer": np.random.uniform(20.0, 300.0, n_rows),
        "transaction_velocity_1h": velocity_1h,
        "transaction_velocity_24h": velocity_24h,
        "risk_label": y,
    })


def test_validation_threshold_optimization():
    """Verify threshold optimization finds a threshold maximizing F1 on validation split."""
    df = create_sample_training_dataset(250)
    trainer = FraudModelTrainer()
    X_train, y_train, X_val, y_val, X_test, y_test, _ = trainer.prepare_data_splits(df)

    rf = RandomForestClassifier(n_estimators=50, class_weight="balanced", random_state=42)
    rf.fit(X_train, y_train)

    selector = ModelSelector()
    opt_thresh, val_metrics = selector.optimize_threshold_on_validation(rf, X_val, y_val)

    assert 0.05 <= opt_thresh <= 0.95
    assert "f1_score" in val_metrics
    assert "pr_auc" in val_metrics
    assert "roc_auc" in val_metrics
    assert 0.0 <= val_metrics["f1_score"] <= 1.0


def test_threshold_reproducibility():
    """Verify threshold optimization is completely deterministic and reproducible."""
    df = create_sample_training_dataset(200)
    trainer = FraudModelTrainer()
    X_train, y_train, X_val, y_val, _, _, _ = trainer.prepare_data_splits(df)

    lr = LogisticRegression(class_weight="balanced", random_state=42, max_iter=500)
    lr.fit(X_train, y_train)

    selector = ModelSelector()
    opt_thresh_1, _ = selector.optimize_threshold_on_validation(lr, X_val, y_val)
    opt_thresh_2, _ = selector.optimize_threshold_on_validation(lr, X_val, y_val)

    assert opt_thresh_1 == opt_thresh_2


def test_multi_model_comparison_and_selection(tmp_path):
    """Verify all 3 models are compared and the winning model is selected and saved."""
    df = create_sample_training_dataset(250)
    trainer = FraudModelTrainer(config=TrainingConfig(artifact_dir=str(tmp_path)))
    X_train, y_train, X_val, y_val, X_test, y_test, _ = trainer.prepare_data_splits(df)

    models = trainer.train_all_models(X_train, y_train)
    assert len(models) >= 3

    selector = ModelSelector(artifact_dir=str(tmp_path), model_version="v1.0.0")
    results = selector.compare_and_select(models, X_val, y_val, X_test, y_test)

    selected_model = results["selected_model"]
    assert selected_model in ["logistic_regression", "random_forest", "xgboost", "ensemble_stacking"]

    # Verify comparison dictionary contains all 3 models
    comparison = results["comparison"]
    assert "logistic_regression" in comparison
    assert "random_forest" in comparison
    assert "xgboost" in comparison

    # Active flag must be true only for selected model
    for name, report in comparison.items():
        if name == selected_model:
            assert report["is_active"] is True
        else:
            assert report["is_active"] is False

    # Check that metadata files exist on disk
    active_meta_file = tmp_path / "active_model_metadata.json"
    registry_file = tmp_path / "model_registry.json"

    assert active_meta_file.exists()
    assert registry_file.exists()

    with open(active_meta_file, "r", encoding="utf-8") as f:
        meta = json.load(f)
    assert meta["model_name"] == selected_model
    assert "selected_threshold" in meta
    assert "evaluation_metrics" in meta
    assert "pr_auc" in meta["evaluation_metrics"]
    assert "f1_score" in meta["evaluation_metrics"]
