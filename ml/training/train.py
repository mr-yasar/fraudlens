"""Command Line Interface for Training Fraud Detection ML Models."""

import argparse
from pathlib import Path
import pandas as pd
from ml.training.trainer import FraudModelTrainer, TrainingConfig
from ml.validation.dataset_validator import DatasetValidator


def main():
    parser = argparse.ArgumentParser(description="Train Fraud Detection Machine Learning Models")
    parser.add_argument(
        "--data-path",
        type=str,
        default="data/raw/financial_fraud_customer_transactions.csv",
        help="Path to validated dataset (.csv, .parquet)",
    )
    parser.add_argument(
        "--artifact-dir",
        type=str,
        default="ml/artifacts",
        help="Directory to save trained models and preprocessor",
    )
    parser.add_argument(
        "--model-version",
        type=str,
        default="v1.2.0",
        help="Model version string",
    )
    args = parser.parse_args()

    data_file = Path(args.data_path)
    if not data_file.exists():
        print(f"[ERROR] Dataset file not found at: {data_file}")
        print("Please place your validated dataset in data/raw/ before running training.")
        return

    print(f"[INFO] Validating dataset at: {data_file}")
    validator = DatasetValidator()
    val_result = validator.validate_file(data_file)
    if not val_result.is_valid:
        print("[ERROR] Dataset validation failed:")
        for err in val_result.errors:
            print(f"  - {err}")
        return

    print("[INFO] Dataset validation passed. Loading data...")
    if data_file.suffix == ".csv":
        df = pd.read_csv(data_file)
    elif data_file.suffix == ".parquet":
        df = pd.read_parquet(data_file)
    else:
        df = pd.read_json(data_file)

    config = TrainingConfig(
        artifact_dir=args.artifact_dir,
        model_version=args.model_version,
    )
    trainer = FraudModelTrainer(config=config)

    print("[INFO] Preparing data splits (Stratified 70/15/15)...")
    X_train, y_train, X_val, y_val, X_test, y_test, split_info = trainer.prepare_data_splits(df)

    print(f"[INFO] Data split complete: Train={len(y_train)}, Val={len(y_val)}, Test={len(y_test)}")
    print(f"[INFO] Features dimension after preprocessing: {X_train.shape[1]}")

    print("[INFO] Starting ML Training Pipeline (Logistic Regression, Random Forest, XGBoost, Stacking Ensemble)...")
    trainer.train_all_models(X_train, y_train)

    print("[INFO] Serializing base models and preprocessor...")
    trainer.save_artifacts()

    print("[INFO] Running ModelSelector: Cost-Sensitive Threshold Optimization & Champion Selection...")
    from ml.evaluation.model_selector import ModelSelector
    selector = ModelSelector(artifact_dir=args.artifact_dir, model_version=args.model_version)
    selection_results = selector.compare_and_select(
        models=trainer.models,
        X_val=X_val,
        y_val=y_val,
        X_test=X_test,
        y_test=y_test,
        dataset_path=args.data_path,
        feature_version=args.model_version,
    )

    best_model_name = selection_results["selected_model"]
    active_meta = selection_results["active_metadata"]

    print("\n" + "=" * 70)
    print("        MULTI-MODEL COMPARISON & OPTIMIZED EVALUATION RESULTS          ")
    print("=" * 70)
    for model_name, rep in selection_results["comparison"].items():
        is_best = " [SELECTED CHAMPION]" if model_name == best_model_name else ""
        print(f"\nModel: {model_name.upper()}{is_best}")
        print(f"  Optimal Threshold:    {rep['optimal_threshold']:.4f}")
        print(f"  Test Accuracy:        {rep['test_accuracy']:.4f}")
        print(f"  Test Precision:       {rep['test_precision']:.4f}")
        print(f"  Test Recall:          {rep['test_recall']:.4f}")
        print(f"  Test F1-Score:        {rep['test_f1']:.4f}")
        print(f"  Test F2-Score:        {rep.get('test_f2', rep['test_f1']):.4f}")
        print(f"  Test ROC-AUC:         {rep['test_roc_auc']:.4f}")
        print(f"  Test PR-AUC:          {rep['test_pr_auc']:.4f}")
        print(f"  False Positive Rate:  {rep['test_fpr']:.4f}")
        print(f"  False Negative Rate:  {rep['test_fnr']:.4f}")
        print(f"  Selection Score:      {rep['selection_score']:.4f}")

    print("\n" + "=" * 70)
    print(f"[SUCCESS] Selected Champion Model: {best_model_name.upper()}")
    print(f"[SUCCESS] Decision Threshold:     {active_meta['selected_threshold']:.4f}")
    print("=" * 70)

    print("\n[INFO] Fitting SHAP Explainer and caching global feature importance...")
    from ml.explainability.shap_explainer import FraudShapExplainer
    best_model = trainer.models[best_model_name]
    feature_names = trainer.preprocessor.get_feature_names_out()
    shap_engine = FraudShapExplainer(
        model=best_model,
        feature_names=feature_names,
        background_data=X_train,
        model_name=best_model_name,
        model_version=args.model_version,
        artifact_dir=args.artifact_dir,
    )
    shap_engine.compute_and_cache_global_explanation(X_test, sample_size=min(100, len(X_test)))
    print("[INFO] Global SHAP feature importances successfully generated and cached.")

    print("\n[INFO] All artifacts successfully serialized to:", Path(args.artifact_dir).resolve())


if __name__ == "__main__":
    main()
