"""
Train all three ML models on the real financial_fraud_customer_transactions.csv dataset.
This script replaces the pytest-generated artifacts with real ones.
Run from repo root: python scripts/train_real_dataset.py
"""

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

# Ensure repo root is on sys.path
repo_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(repo_root))

from ml.training.trainer import FraudModelTrainer, TrainingConfig
from ml.evaluation.model_selector import ModelSelector

DATASET_PATH = repo_root / "data" / "raw" / "financial_fraud_customer_transactions.csv"
ARTIFACT_DIR = repo_root / "ml" / "artifacts"


def main() -> None:
    print("=" * 70)
    print("REAL DATASET TRAINING PIPELINE")
    print(f"Dataset : {DATASET_PATH}")
    print(f"Artifacts: {ARTIFACT_DIR}")
    print("=" * 70)

    # 1. Load dataset
    if not DATASET_PATH.exists():
        sys.exit(f"ERROR: Dataset not found at {DATASET_PATH}")

    df = pd.read_csv(DATASET_PATH)
    print(f"\nLoaded dataset: {df.shape[0]} rows, {df.shape[1]} columns")

    # Verify expected columns
    expected_target = "Fraud_Label"
    if expected_target not in df.columns:
        sys.exit(f"ERROR: Target column '{expected_target}' not found.")

    fraud_count = int(df[expected_target].sum())
    genuine_count = int(len(df) - fraud_count)
    fraud_rate = round(fraud_count / len(df) * 100, 2)
    print(f"Target distribution: Genuine={genuine_count}, Fraud={fraud_count}, Fraud rate={fraud_rate}%")

    # Verify no training leakage columns are present as features
    leakage_cols = {"Fraud_Probability", "Risk_Score", "Risk_Level"}
    present_leakage = leakage_cols.intersection(set(df.columns))
    if present_leakage:
        print(f"\nWARNING: Dataset contains reference/output columns: {present_leakage}")
        print("These will be dropped during feature engineering (not used as model inputs).")

    # 2. Configure training
    MODEL_VERSION = "v2.0.0"
    config = TrainingConfig(
        target_column=expected_target,
        model_version=MODEL_VERSION,
        test_size=0.15,
        val_size=0.15,
        random_state=42,
        artifact_dir=str(ARTIFACT_DIR),
        lr_max_iter=2000,
        rf_n_estimators=200,
        rf_max_depth=15,
        xgb_n_estimators=200,
        xgb_max_depth=6,
        xgb_learning_rate=0.05,
    )

    print(f"\nTraining config: version={MODEL_VERSION}, target='{expected_target}'")
    print("Splitting: 70% train / 15% validation / 15% test (stratified)")

    # 3. Run training pipeline
    trainer = FraudModelTrainer(config=config)
    print("\n[1/3] Preparing stratified data splits and fitting preprocessor...")
    X_train, y_train, X_val, y_val, X_test, y_test, split_info = trainer.prepare_data_splits(df)
    print(f"  Train: {split_info['train_samples']} samples (fraud rate: {split_info['train_fraud_rate']}%)")
    print(f"  Val:   {split_info['val_samples']} samples (fraud rate: {split_info['val_fraud_rate']}%)")
    print(f"  Test:  {split_info['test_samples']} samples (fraud rate: {split_info['test_fraud_rate']}%)")
    print(f"  Feature dimensions: {split_info['feature_dimension']}")

    print("\n[2/3] Training Logistic Regression, Random Forest, and XGBoost...")
    models = trainer.train_all_models(X_train, y_train)
    print(f"  Trained models: {list(models.keys())}")

    # Save preprocessor and model artifacts
    trainer.save_artifacts()
    print("  Saved preprocessor and model artifacts to disk.")

    # 4. Model selection with threshold optimization on validation set
    print("\n[3/3] Selecting best model using validation metrics + test evaluation...")
    selector = ModelSelector(artifact_dir=str(ARTIFACT_DIR), model_version=MODEL_VERSION)
    selection_result = selector.compare_and_select(
        models=models,
        X_val=X_val,
        y_val=y_val,
        X_test=X_test,
        y_test=y_test,
        dataset_path=str(DATASET_PATH),
    )

    # 5. Print comparison table
    print("\n" + "=" * 70)
    print("MODEL COMPARISON — TEST SET METRICS")
    print("=" * 70)
    header = f"{'Model':<25} {'Acc':>6} {'Prec':>6} {'Rec':>6} {'F1':>6} {'ROC':>7} {'PR':>7} {'FPR':>6} {'FNR':>6} {'Thresh':>8} {'Score':>7}"
    print(header)
    print("-" * 100)
    for model_name, report in selection_result["comparison"].items():
        row = (
            f"{model_name:<25}"
            f" {report.get('test_accuracy', 0):>6.4f}"
            f" {report.get('test_precision', 0):>6.4f}"
            f" {report.get('test_recall', 0):>6.4f}"
            f" {report.get('test_f1', 0):>6.4f}"
            f" {report.get('test_roc_auc', 0):>7.4f}"
            f" {report.get('test_pr_auc', 0):>7.4f}"
            f" {report.get('test_fpr', 0):>6.4f}"
            f" {report.get('test_fnr', 0):>6.4f}"
            f" {report.get('optimal_threshold', 0.5):>8.4f}"
            f" {report.get('selection_score', 0):>7.4f}"
        )
        print(row)
    print("-" * 100)

    champion = selection_result["selected_model"]
    active_meta = selection_result["active_metadata"]
    print(f"\nCHAMPION MODEL: {champion.upper()}")
    print(f"  Version:    {active_meta['model_version']}")
    print(f"  Threshold:  {active_meta['selected_threshold']}")
    print(f"  PR-AUC:     {active_meta['evaluation_metrics'].get('pr_auc', 'N/A')}")
    print(f"  Recall:     {active_meta['evaluation_metrics'].get('recall', 'N/A')}")
    print(f"  F1-Score:   {active_meta['evaluation_metrics'].get('f1_score', 'N/A')}")

    # 6. Generate global SHAP explanation using the training background sample
    print("\nGenerating global SHAP explanation (background sample from training set)...")
    try:
        from backend.app.services.prediction_service import FraudPredictionService
        FraudPredictionService.reset_instance()
        service = FraudPredictionService.get_instance(artifact_dir=str(ARTIFACT_DIR))
        if service.is_ready and service.shap_explainer is not None:
            # Use a sample from the test set for global explanation
            sample_size = min(200, X_test.shape[0])
            sample_matrix = X_test[:sample_size]
            service.shap_explainer.compute_and_cache_global_explanation(sample_matrix, sample_size=sample_size)
            print(f"  Global SHAP explanation generated from {sample_size} test samples.")
        else:
            print("  WARNING: Prediction service not ready for SHAP global explanation.")
    except Exception as e:
        print(f"  WARNING: Could not generate global SHAP: {e}")

    print("\n" + "=" * 70)
    print("TRAINING COMPLETE — Real dataset artifacts saved.")
    print(f"Active model: {champion} | Threshold: {active_meta['selected_threshold']}")
    print("=" * 70)


if __name__ == "__main__":
    main()
