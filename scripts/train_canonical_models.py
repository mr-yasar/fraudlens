"""Master ML Pipeline: Train, Evaluate, Compare & Save Artifacts on Canonical 29-Merchant Dataset."""

import os
import json
import logging
import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier
from sklearn.metrics import (
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    average_precision_score,
    confusion_matrix,
)
import shap

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

DATA_PATH = os.path.join("data", "raw", "fraudlens_master_synthetic_transactions_29_merchants.csv")
ARTIFACTS_DIR = os.path.join("ml", "artifacts")
os.makedirs(ARTIFACTS_DIR, exist_ok=True)

NUMERIC_FEATURES = [
    "amount",
    "transaction_hour",
    "day_of_week",
    "is_weekend",
    "is_night_transaction",
    "merchant_business_age_years",
    "merchant_average_ticket",
    "customer_account_age_days",
    "customer_historical_avg_amount",
    "customer_historical_max_amount",
    "customer_total_transactions_prior",
    "beneficiary_prior_tx_count",
    "transactions_last_1h",
    "transactions_last_24h",
    "transactions_last_7d",
    "amount_to_avg_ratio",
    "amount_deviation_zscore",
    "location_distance_km",
    "failed_transaction_attempts_24h",
    "failed_login_attempts_24h",
    "merchant_historical_fraud_rate",
    "is_new_device",
    "is_trusted_device",
    "is_new_beneficiary",
    "is_location_changed",
    "recent_password_change",
]

CATEGORICAL_FEATURES = [
    "merchant_category",
    "transaction_type",
    "merchant_payment_channels",
    "device_type",
]

# TARGET & LEAKAGE (Excluded from model input)
TARGET_COLUMN = "is_fraud"
LEAKAGE_COLUMNS = [
    "is_fraud",
    "fraud_type",
    "fraud_stage",
    "fraud_scenario",
    "merchant_historical_fraud_pattern",
    "merchant_historical_fraud_count",
]


def train_and_evaluate():
    logger.info("Loading canonical 29-merchant dataset from: %s", DATA_PATH)
    df = pd.read_csv(DATA_PATH)
    logger.info("Loaded %d records with %d columns.", len(df), len(df.columns))

    # Sort by timestamp for time-aware split
    df["transaction_datetime"] = pd.to_datetime(df["transaction_datetime"])
    df = df.sort_values("transaction_datetime").reset_index(drop=True)

    # Validate target
    y = df[TARGET_COLUMN].values
    logger.info("Class distribution: Normal=%d, Fraud=%d (Fraud rate=%.2f%%)", 
                (y == 0).sum(), (y == 1).sum(), (y.mean() * 100))

    # Clean boolean / integer columns in feature matrix
    X = df[NUMERIC_FEATURES + CATEGORICAL_FEATURES].copy()
    for col in NUMERIC_FEATURES:
        X[col] = pd.to_numeric(X[col], errors="coerce").fillna(0.0)
    for col in CATEGORICAL_FEATURES:
        X[col] = X[col].astype(str).fillna("UNKNOWN")

    # Time-aware split: 80% train, 20% test
    split_idx = int(len(df) * 0.8)
    X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
    y_train, y_test = y[:split_idx], y[split_idx:]

    logger.info("Train set: %d rows, Test set: %d rows (Fraud rate train: %.2f%%, test: %.2f%%)",
                len(X_train), len(X_test), y_train.mean() * 100, y_test.mean() * 100)

    # Preprocessor
    preprocessor = ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), NUMERIC_FEATURES),
            ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), CATEGORICAL_FEATURES),
        ]
    )

    X_train_proc = preprocessor.fit_transform(X_train)
    X_test_proc = preprocessor.transform(X_test)

    # Get feature names after one-hot encoding
    cat_feature_names = preprocessor.named_transformers_["cat"].get_feature_names_out(CATEGORICAL_FEATURES).tolist()
    all_feature_names = NUMERIC_FEATURES + cat_feature_names

    models = {
        "LogisticRegression": LogisticRegression(max_iter=1000, class_weight="balanced", random_state=42),
        "RandomForest": RandomForestClassifier(n_estimators=150, max_depth=10, class_weight="balanced", random_state=42, n_jobs=-1),
        "XGBoost": XGBClassifier(n_estimators=150, max_depth=6, learning_rate=0.08, scale_pos_weight=(len(y_train) - sum(y_train)) / max(1, sum(y_train)), random_state=42, eval_metric="logloss", n_jobs=-1),
    }

    comparison_results = {}
    fitted_models = {}

    for name, model in models.items():
        logger.info("Training %s...", name)
        model.fit(X_train_proc, y_train)
        fitted_models[name] = model

        y_pred = model.predict(X_test_proc)
        y_prob = model.predict_proba(X_test_proc)[:, 1]

        precision = float(precision_score(y_test, y_pred, zero_division=0))
        recall = float(recall_score(y_test, y_pred, zero_division=0))
        f1 = float(f1_score(y_test, y_pred, zero_division=0))
        roc_auc = float(roc_auc_score(y_test, y_prob))
        pr_auc = float(average_precision_score(y_test, y_prob))
        cm = confusion_matrix(y_test, y_pred).tolist()

        logger.info("[%s] Precision: %.4f, Recall: %.4f, F1: %.4f, ROC-AUC: %.4f, PR-AUC: %.4f",
                    name, precision, recall, f1, roc_auc, pr_auc)

        comparison_results[name] = {
            "name": name,
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1_score": round(f1, 4),
            "roc_auc": round(roc_auc, 4),
            "pr_auc": round(pr_auc, 4),
            "confusion_matrix": cm,
            "is_champion": False,
        }

    # Select Champion based on PR-AUC & F1
    champion_name = max(comparison_results.keys(), key=lambda k: (comparison_results[k]["pr_auc"], comparison_results[k]["f1_score"]))
    comparison_results[champion_name]["is_champion"] = True
    logger.info("Selected Champion Model: %s", champion_name)

    champion_model = fitted_models[champion_name]

    # Save Preprocessor and Models
    preprocessor_path = os.path.join(ARTIFACTS_DIR, "preprocessor.joblib")
    model_path = os.path.join(ARTIFACTS_DIR, "champion_model.joblib")
    xgb_path = os.path.join(ARTIFACTS_DIR, "xgboost_model.joblib")
    rf_path = os.path.join(ARTIFACTS_DIR, "random_forest_model.joblib")
    lr_path = os.path.join(ARTIFACTS_DIR, "logistic_regression_model.joblib")

    joblib.dump(preprocessor, preprocessor_path)
    joblib.dump(champion_model, model_path)
    joblib.dump(fitted_models["XGBoost"], xgb_path)
    joblib.dump(fitted_models["RandomForest"], rf_path)
    joblib.dump(fitted_models["LogisticRegression"], lr_path)

    # SHAP Explainer
    logger.info("Fitting SHAP explainer on Champion Model...")
    background_summary = X_train_proc[:200]
    if champion_name == "XGBoost":
        explainer = shap.TreeExplainer(champion_model)
    elif champion_name == "RandomForest":
        explainer = shap.TreeExplainer(champion_model)
    else:
        explainer = shap.LinearExplainer(champion_model, background_summary)

    shap_path = os.path.join(ARTIFACTS_DIR, "shap_explainer.joblib")
    joblib.dump(explainer, shap_path)

    metadata = {
        "dataset_name": "fraudlens_master_synthetic_transactions_29_merchants.csv",
        "total_rows": len(df),
        "merchant_count": len(df["merchant_id"].unique()),
        "fraud_rate": round(float(df["is_fraud"].mean()), 4),
        "numeric_features": NUMERIC_FEATURES,
        "categorical_features": CATEGORICAL_FEATURES,
        "encoded_feature_names": all_feature_names,
        "champion_model_name": champion_name,
        "comparison": comparison_results,
    }

    metadata_path = os.path.join(ARTIFACTS_DIR, "model_comparison.json")
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    logger.info("Saved all artifacts and metadata successfully to: %s", ARTIFACTS_DIR)
    return metadata


if __name__ == "__main__":
    train_and_evaluate()
