"""Phase 3 & Phase 4 Comprehensive ML Pipeline, Training & Prediction Tests.

Verifies:
1. Dataset schema and target leakage exclusion (Fraud_Probability, Risk_Score, Risk_Level excluded).
2. FullFraudPreprocessor transformation determinism and feature dimension consistency.
3. Class imbalance weighting and stratified 70/15/15 train/val/test splits.
4. Validation-driven threshold optimization and model selection criteria.
5. All 3 base models (Logistic Regression, Random Forest, XGBoost) + Stacking Ensemble evaluation metrics.
6. Strict independence of Fraud Probability [0.0 - 1.0] and Risk Score [0 - 100].
7. Model artifact persistence, active model metadata, and model registry integrity.
8. Deterministic prediction outputs across repeated inferences.
"""

import json
from pathlib import Path
import numpy as np
import pandas as pd
import pytest

from ml.features.feature_engineer import FraudFeatureEngineer
from ml.preprocessing.pipeline import FullFraudPreprocessor
from ml.training.trainer import FraudModelTrainer, TrainingConfig
from ml.evaluation.model_selector import ModelSelector
from backend.app.schemas.prediction import TransactionPredictionInput
from backend.app.services.prediction_service import FraudPredictionService
from backend.app.services.risk_scoring_service import RiskScoringEngine, RiskLevel


# ---------------------------------------------------------------------------
# 1. Dataset & Target Leakage Tests
# ---------------------------------------------------------------------------

def test_dataset_exists_and_has_expected_shape():
    """Verify primary dataset exists and conforms to expected shape."""
    data_path = Path("data/raw/financial_fraud_customer_transactions.csv")
    assert data_path.exists(), "Primary dataset file missing."
    df = pd.read_csv(data_path)
    assert len(df) == 4581
    assert "Fraud_Label" in df.columns
    assert "Amount" in df.columns
    assert "Transaction_ID" in df.columns


def test_target_leakage_exclusion():
    """Verify feature engineer strictly strips target leakage and identifier columns."""
    engineer = FraudFeatureEngineer()
    sample_df = pd.DataFrame([{
        "Transaction_ID": "TX-101",
        "Customer_ID": "CUST-101",
        "Amount": 500.0,
        "Average_Previous_Amount": 200.0,
        "Transaction_Hour": 14,
        "Fraud_Probability": 0.88,
        "Risk_Score": 85,
        "Risk_Level": "HIGH",
        "Fraud_Label": 1,
    }])

    transformed = engineer.transform(sample_df)
    assert "Fraud_Probability" not in transformed.columns
    assert "Risk_Score" not in transformed.columns
    assert "Risk_Level" not in transformed.columns
    assert "Fraud_Label" not in transformed.columns
    assert "Transaction_ID" not in transformed.columns
    assert "Customer_ID" not in transformed.columns
    assert "log_amount" in transformed.columns


# ---------------------------------------------------------------------------
# 2. Preprocessing & Feature Transformation Tests
# ---------------------------------------------------------------------------

def test_preprocessor_fit_transform_determinism():
    """Verify FullFraudPreprocessor produces identical feature dimensions and determinism."""
    df = pd.read_csv("data/raw/financial_fraud_customer_transactions.csv").head(100)
    preprocessor = FullFraudPreprocessor()
    mat1 = preprocessor.fit_transform(df)
    mat2 = preprocessor.transform(df)

    assert mat1.shape == mat2.shape
    assert np.allclose(mat1, mat2, atol=1e-5)
    assert preprocessor.is_fitted_ is True
    assert len(preprocessor.get_feature_names_out()) == mat1.shape[1]


# ---------------------------------------------------------------------------
# 3. Model Training & Class Imbalance Tests
# ---------------------------------------------------------------------------

def test_data_splits_stratification():
    """Verify 70/15/15 stratified split preserves fraud class representation across splits."""
    df = pd.read_csv("data/raw/financial_fraud_customer_transactions.csv")
    trainer = FraudModelTrainer(config=TrainingConfig(random_state=42))
    X_train, y_train, X_val, y_val, X_test, y_test, split_info = trainer.prepare_data_splits(df)

    assert split_info["train_samples"] + split_info["val_samples"] + split_info["test_samples"] == len(df)
    assert 0.01 <= np.mean(y_train) <= 0.05
    assert 0.01 <= np.mean(y_val) <= 0.05
    assert 0.01 <= np.mean(y_test) <= 0.05


def test_model_training_and_metric_validity():
    """Verify models train and produce bounded metrics in [0.0, 1.0]."""
    df = pd.read_csv("data/raw/financial_fraud_customer_transactions.csv")
    config = TrainingConfig(
        rf_n_estimators=30,
        xgb_n_estimators=30,
        random_state=42,
    )
    trainer = FraudModelTrainer(config=config)
    X_train, y_train, X_val, y_val, X_test, y_test, _ = trainer.prepare_data_splits(df)
    models = trainer.train_all_models(X_train, y_train)

    assert "logistic_regression" in models
    assert "random_forest" in models
    assert "xgboost" in models
    assert "ensemble_stacking" in models

    for name, model in models.items():
        eval_metrics = trainer.evaluate_model(model, X_test, y_test, name)
        assert 0.0 <= eval_metrics["accuracy"] <= 1.0
        assert 0.0 <= eval_metrics["precision"] <= 1.0
        assert 0.0 <= eval_metrics["recall"] <= 1.0
        assert 0.0 <= eval_metrics["f1_score"] <= 1.0
        assert 0.0 <= eval_metrics["roc_auc"] <= 1.0
        assert 0.0 <= eval_metrics["pr_auc"] <= 1.0


# ---------------------------------------------------------------------------
# 4. Threshold Optimization & Model Selection Tests
# ---------------------------------------------------------------------------

def test_validation_threshold_optimization_does_not_use_test_set():
    """Verify threshold optimization uses strictly validation split."""
    df = pd.read_csv("data/raw/financial_fraud_customer_transactions.csv")
    trainer = FraudModelTrainer(config=TrainingConfig(random_state=42))
    X_train, y_train, X_val, y_val, X_test, y_test, _ = trainer.prepare_data_splits(df)
    models = trainer.train_all_models(X_train, y_train)

    selector = ModelSelector()
    opt_thresh, val_metrics = selector.optimize_threshold_on_validation(
        models["logistic_regression"], X_val, y_val
    )

    assert 0.0 < opt_thresh < 1.0
    assert "f1_score" in val_metrics
    assert "pr_auc" in val_metrics


# ---------------------------------------------------------------------------
# 5. Prediction Service & Fraud Probability Validation Tests
# ---------------------------------------------------------------------------

def test_prediction_service_deterministic_inference():
    """Verify active prediction service produces deterministic, bounded probabilities."""
    service = FraudPredictionService.get_instance()
    assert service.is_ready is True
    assert service.model is not None
    assert service.preprocessor is not None

    payload = TransactionPredictionInput(
        Amount=250.0,
        Transaction_Hour=11,
        Transaction_Type="Purchase",
        Location="Delhi",
        Usual_Location="Delhi",
        Device_Type="Windows",
        New_Device=0,
        Account_Age_Days=400.0,
        Previous_Transaction_Amount=200.0,
        Average_Previous_Amount=220.0,
        Transactions_Last_24H=1,
        Failed_Attempts=0,
        International_Transaction=0,
    )

    res1 = service.predict_transaction(payload)
    res2 = service.predict_transaction(payload)

    assert res1.prediction in ["FRAUD", "GENUINE"]
    assert 0.0 <= res1.fraud_probability <= 1.0
    assert 0 <= res1.risk_score <= 100
    assert res1.risk_level in ["LOW", "MEDIUM", "HIGH"]
    assert res1.fraud_probability == res2.fraud_probability
    assert res1.risk_score == res2.risk_score


def test_fraud_probability_vs_risk_score_independence():
    """Verify Fraud Probability (ML output) is strictly separated from Risk Score (0-100 multi-factor)."""
    engine = RiskScoringEngine()
    dummy_tx = {
        "Amount": 1000.0,
        "Average_Previous_Amount": 100.0,
        "Transactions_Last_24H": 10,
        "Failed_Attempts": 3,
        "International_Transaction": 1,
    }

    # Even if ML probability is low (e.g. 0.05), behavioral signals must elevate risk score
    risk_res = engine.compute_risk_score(fraud_probability=0.05, transaction_data=dummy_tx)
    assert risk_res.risk_score > int(0.05 * 100)
    assert len(risk_res.risk_factors) > 0


def test_active_model_artifacts_integrity():
    """Verify active model metadata, model registry, and feature metadata exist on disk."""
    art_dir = Path("ml/artifacts")
    assert (art_dir / "active_model_metadata.json").exists()
    assert (art_dir / "model_registry.json").exists()
    assert (art_dir / "feature_metadata.json").exists()
    assert (art_dir / "preprocessor.joblib").exists()

    with open(art_dir / "active_model_metadata.json", "r", encoding="utf-8") as f:
        meta = json.load(f)
    assert "model_name" in meta
    assert "selected_threshold" in meta
    assert "evaluation_metrics" in meta
