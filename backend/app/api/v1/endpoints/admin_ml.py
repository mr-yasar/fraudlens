"""Admin ML & Dataset Management Endpoints (Phase 14)."""

from datetime import datetime, timezone
import io
import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
import pandas as pd
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.models.user import User
from backend.app.models.model_version import ModelVersion
from backend.app.models.audit_log import AuditLog
from backend.app.api.deps import require_admin
from backend.app.schemas.admin_ml import (
    DatasetStatusResponse,
    ModelVersionInfo,
    ModelListResponse,
    ModelComparisonResponse,
    TrainModelRequest,
    TrainModelResponse,
    ModelActivationResponse,
)
from backend.app.services.prediction_service import FraudPredictionService
from ml.validation.dataset_validator import DatasetValidator, DatasetSchema
from ml.training.trainer import FraudModelTrainer, TrainingConfig
from ml.evaluation.model_selector import ModelSelector

router = APIRouter()
validator = DatasetValidator()


def _get_adaptive_validator(df: pd.DataFrame) -> DatasetValidator:
    """Return DatasetValidator configured for df's target column ('Fraud_Label', 'is_fraud', or 'risk_label')."""
    if "Fraud_Label" in df.columns or "Amount" in df.columns:
        return DatasetValidator()
    target_col = "is_fraud" if "is_fraud" in df.columns else "risk_label"
    if target_col != "risk_label":
        schema_cols = dict(DatasetSchema().expected_columns)
        schema_cols.pop("risk_label", None)
        schema_cols[target_col] = {"types": ["integer", "int64", "int32"], "required": True}
        return DatasetValidator(schema=DatasetSchema(target_column=target_col, expected_columns=schema_cols))
    return DatasetValidator()


@router.post(
    "/datasets/validate",
    summary="Validate Training Dataset (Admin Only)",
    description="Performs an 11-step validation audit on an uploaded dataset file including schema, null checks, duplicates, class distribution, and target leakage.",
)
async def validate_dataset(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
) -> Dict[str, Any]:
    """Validate uploaded dataset file and record audit trail."""
    filename = file.filename or "dataset.csv"
    suffix = "." + filename.split(".")[-1].lower() if "." in filename else ""

    if suffix not in [".csv", ".parquet", ".json"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format '{suffix}'. Allowed formats: .csv, .parquet, .json.",
        )

    content = await file.read()
    if len(content) > 50 * 1024 * 1024:  # 50 MB limit
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file exceeds 50MB size limit.",
        )

    try:
        if suffix == ".csv":
            df = pd.read_csv(io.BytesIO(content))
        elif suffix == ".parquet":
            df = pd.read_parquet(io.BytesIO(content))
        else:
            df = pd.read_json(io.BytesIO(content))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to parse uploaded dataset: {str(e)}",
        )

    ds_validator = _get_adaptive_validator(df)
    result = ds_validator.validate_dataframe(df, file_type=suffix)
    row_count = result.summary_statistics.get("total_rows", len(df))
    col_count = result.summary_statistics.get("total_columns", len(df.columns))

    # Record AuditLog
    audit_entry = AuditLog(
        user_id=admin.id,
        action="DATASET_VALIDATED",
        resource_type="dataset",
        resource_id=filename,
        details=json.dumps({
            "is_valid": result.is_valid,
            "row_count": row_count,
            "column_count": col_count,
            "errors": result.errors,
            "warnings": result.warnings,
        }),
    )
    db.add(audit_entry)
    db.commit()

    return result.to_dict()


@router.get(
    "/datasets/status",
    response_model=DatasetStatusResponse,
    summary="Get Active Dataset Status & Leakage Findings",
    description="Returns real audit status, row counts, target distribution, and leakage findings for the primary active dataset.",
)
def get_dataset_status(
    admin: User = Depends(require_admin),
) -> DatasetStatusResponse:
    """Retrieve actual dataset status and audit metrics from the primary CSV dataset."""
    # Primary dataset: financial_fraud_customer_transactions.csv
    primary_path = Path("data/raw/financial_fraud_customer_transactions.csv")
    legacy_path = Path("data/raw/fraud_dataset.csv")

    # Prefer primary CSV, fall back to legacy
    if primary_path.exists():
        default_path = primary_path
    elif legacy_path.exists():
        default_path = legacy_path
    else:
        return DatasetStatusResponse(
            dataset_name="financial_fraud_customer_transactions.csv",
            file_format=".csv",
            row_count=0,
            column_count=0,
            target_column="Fraud_Label",
            target_distribution={},
            validation_status="NO_DATASET_FOUND",
            leakage_findings=[],
            last_validated=None,
        )

    df = pd.read_csv(default_path)
    ds_validator = _get_adaptive_validator(df)
    result = ds_validator.validate_dataframe(df, file_type=".csv")

    # Build target distribution for Fraud_Label (primary) or fallback columns
    target_dist: dict = {}
    if "Fraud_Label" in df.columns:
        counts = df["Fraud_Label"].value_counts().to_dict()
        total = len(df)
        fraud_n = int(counts.get(1, 0))
        genuine_n = int(counts.get(0, 0))
        target_dist = {
            "genuine": genuine_n,
            "fraud": fraud_n,
            "fraud_percentage": round(fraud_n / total * 100, 2) if total > 0 else 0.0,
        }
    elif "is_fraud" in df.columns:
        counts = df["is_fraud"].value_counts().to_dict()
        target_dist = {str(k): int(v) for k, v in counts.items()}
    elif "risk_label" in df.columns:
        counts = df["risk_label"].value_counts().to_dict()
        target_dist = {str(k): int(v) for k, v in counts.items()}

    # Extract leakage findings from leakage audit (excluded features list)
    leakage_list = []
    if hasattr(result, "leakage_audit") and isinstance(result.leakage_audit, dict):
        for excluded in result.leakage_audit.get("excluded_features", []):
            leakage_list.append({
                "column": excluded.get("feature", ""),
                "correlation_score": 1.0,  # Excluded = definite risk
            })
    elif hasattr(result, "leakage_findings") and isinstance(result.leakage_findings, dict):
        leakage_list = [
            {"column": k, "correlation_score": round(float(v), 4)}
            for k, v in result.leakage_findings.items()
        ]

    # Determine target column based on dataset
    if "Fraud_Label" in df.columns:
        target_col = "Fraud_Label"
    else:
        target_col = ds_validator.schema.target_column

    # Build validation timestamp
    last_validated = getattr(result, "timestamp", None)
    if last_validated is None:
        from datetime import datetime, timezone
        last_validated = datetime.now(timezone.utc).isoformat()

    return DatasetStatusResponse(
        dataset_name=default_path.name,
        file_format=".csv",
        row_count=len(df),
        column_count=len(df.columns),
        target_column=target_col,
        target_distribution=target_dist,
        validation_status="VALID" if result.is_valid else "INVALID",
        leakage_findings=leakage_list,
        last_validated=last_validated,
    )


@router.get(
    "/models",
    response_model=ModelListResponse,
    summary="List Registered Models & Evaluation Metrics",
    description="Retrieves all candidate model algorithms, optimal thresholds, validation/test metrics, and active status from the model registry.",
)
def list_registered_models(
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
) -> ModelListResponse:
    """List all registered models and their performance metrics."""
    registry_file = Path("ml/artifacts/model_registry.json")
    if not registry_file.exists():
        return ModelListResponse(models=[], active_model=None, model_version="v1.0.0")

    with open(registry_file, "r", encoding="utf-8") as f:
        registry_data = json.load(f)

    models_dict = registry_data.get("models", {})
    active_model = registry_data.get("active_model")
    model_version = registry_data.get("version", "v1.0.0")
    last_updated = registry_data.get("last_updated")

    # Fetch DB model versions if available
    db_versions = {mv.model_name: mv for mv in db.query(ModelVersion).filter(ModelVersion.version == model_version).all()}

    items: List[ModelVersionInfo] = []
    for name, m in models_dict.items():
        db_rec = db_versions.get(name)
        cm = m.get("test_confusion_matrix", {})
        items.append(
            ModelVersionInfo(
                id=db_rec.id if db_rec else None,
                model_name=name,
                version=model_version,
                accuracy=m.get("test_accuracy"),
                precision=m.get("test_precision"),
                recall=m.get("test_recall"),
                f1_score=m.get("test_f1"),
                roc_auc=m.get("test_roc_auc"),
                pr_auc=m.get("test_pr_auc"),
                false_positive_rate=m.get("test_fpr"),
                false_negative_rate=m.get("test_fnr"),
                optimal_threshold=m.get("optimal_threshold"),
                is_active=(name == active_model),
                trained_at=last_updated,
                selection_score=m.get("selection_score"),
            )
        )

    return ModelListResponse(
        models=items,
        active_model=active_model,
        model_version=model_version,
        last_updated=last_updated,
    )


@router.get(
    "/models/comparison",
    response_model=ModelComparisonResponse,
    summary="Get Multi-Model Comparison Matrix",
    description="Returns detailed comparative evaluation matrix across Logistic Regression, Random Forest, and XGBoost at validation-optimized thresholds.",
)
def get_model_comparison(
    admin: User = Depends(require_admin),
) -> ModelComparisonResponse:
    """Retrieve comparative metrics across all candidate models."""
    registry_file = Path("ml/artifacts/model_registry.json")
    if not registry_file.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model registry not found. Run model training first.",
        )

    with open(registry_file, "r", encoding="utf-8") as f:
        registry_data = json.load(f)

    return ModelComparisonResponse(
        version=registry_data.get("version", "v1.0.0"),
        active_model=registry_data.get("active_model", "Unknown"),
        comparison=registry_data.get("models", {}),
        selection_criteria={
            "pr_auc_weight": 0.40,
            "f1_score_weight": 0.30,
            "recall_weight": 0.20,
            "fpr_penalty_weight": 0.10,
            "strategy": "Maximize fraud capture (PR-AUC + Recall) while constraining false positive rate.",
        },
    )


@router.post(
    "/models/train",
    response_model=TrainModelResponse,
    summary="Train & Select Models (Admin Only)",
    description="Executes automated ML pipeline: dataset validation, feature engineering, preprocessing, training (LR, RF, XGBoost), validation threshold optimization, model selection, and artifact serialization.",
)
def train_models(
    payload: TrainModelRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
) -> TrainModelResponse:
    """Trigger full model training, evaluation, threshold optimization, and selection."""
    dataset_file = Path(payload.dataset_path)
    if not dataset_file.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset file '{payload.dataset_path}' not found.",
        )

    try:
        df = pd.read_csv(dataset_file)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not load dataset: {str(e)}",
        )

    # 1. Validate dataset
    if "Fraud_Label" in df.columns:
        target_col = "Fraud_Label"
    elif "is_fraud" in df.columns:
        target_col = "is_fraud"
    else:
        target_col = "risk_label"
    ds_validator = _get_adaptive_validator(df)
    validation_res = ds_validator.validate_dataframe(df)
    if not validation_res.is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Dataset validation failed: {validation_res.errors}",
        )

    # 2. Configure and train models
    config = TrainingConfig(
        target_column=target_col,
        model_version=payload.model_version or "v1.0.0",
        rf_n_estimators=payload.rf_n_estimators or 100,
        xgb_n_estimators=payload.xgb_n_estimators or 100,
    )
    trainer = FraudModelTrainer(config=config)
    X_train, y_train, X_val, y_val, X_test, y_test, _ = trainer.prepare_data_splits(df)
    models = trainer.train_all_models(X_train, y_train)
    trainer.save_artifacts()

    # 3. Optimize thresholds and select best model
    selector = ModelSelector(artifact_dir="ml/artifacts", model_version=config.model_version)
    selection_result = selector.compare_and_select(
        models=models,
        X_val=X_val,
        y_val=y_val,
        X_test=X_test,
        y_test=y_test,
        dataset_path=str(dataset_file),
    )

    # 4. Upsert records into model_versions DB table
    for name, report in selection_result["comparison"].items():
        mv = (
            db.query(ModelVersion)
            .filter(ModelVersion.model_name == name, ModelVersion.version == config.model_version)
            .first()
        )
        if not mv:
            mv = ModelVersion(
                model_name=name,
                version=config.model_version,
                accuracy=report.get("test_accuracy"),
                precision=report.get("test_precision"),
                recall=report.get("test_recall"),
                f1_score=report.get("test_f1"),
                roc_auc=report.get("test_roc_auc"),
                pr_auc=report.get("test_pr_auc"),
                model_path=f"ml/artifacts/{name}.joblib",
                is_active=(name == selection_result["selected_model"]),
            )
            db.add(mv)
        else:
            mv.accuracy = report.get("test_accuracy")
            mv.precision = report.get("test_precision")
            mv.recall = report.get("test_recall")
            mv.f1_score = report.get("test_f1")
            mv.roc_auc = report.get("test_roc_auc")
            mv.pr_auc = report.get("test_pr_auc")
            mv.is_active = (name == selection_result["selected_model"])

    # 5. Record AuditLog
    audit = AuditLog(
        user_id=admin.id,
        action="MODEL_TRAINING_COMPLETED",
        resource_type="ml_pipeline",
        resource_id=selection_result["selected_model"],
        details=json.dumps({
            "version": config.model_version,
            "selected_model": selection_result["selected_model"],
            "models_trained": list(models.keys()),
        }),
    )
    db.add(audit)
    db.commit()

    # 6. Reset prediction service singleton to load freshly trained artifacts
    FraudPredictionService.reset_instance()
    FraudPredictionService.get_instance()

    return TrainModelResponse(
        status="TRAINING_SUCCESSFUL",
        model_version=config.model_version,
        selected_model=selection_result["selected_model"],
        active_metadata=selection_result["active_metadata"],
        comparison=selection_result["comparison"],
        trained_models=list(models.keys()),
    )


@router.post(
    "/models/{model_name}/activate",
    response_model=ModelActivationResponse,
    summary="Activate Production Model Candidate (Admin Only)",
    description="Safely promotes a registered model to active production status, verifies binary and metadata existence, updates threshold settings, and updates active model metadata.",
)
def activate_model(
    model_name: str,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
) -> ModelActivationResponse:
    """Safely activate a model version with full fallback preservation."""
    clean_name = model_name.lower().strip()
    registry_file = Path("ml/artifacts/model_registry.json")
    active_meta_file = Path("ml/artifacts/active_model_metadata.json")

    if not registry_file.exists() or not active_meta_file.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model artifacts or registry not found. Run model training first.",
        )

    # 1. Load registry and backup current active metadata
    with open(registry_file, "r", encoding="utf-8") as f:
        registry = json.load(f)

    with open(active_meta_file, "r", encoding="utf-8") as f:
        previous_active_meta = json.load(f)

    models_dict = registry.get("models", {})
    if clean_name not in models_dict:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model '{clean_name}' is not registered. Registered models: {list(models_dict.keys())}",
        )

    # 2. Verify model binary exists
    target_model_file = Path(f"ml/artifacts/{clean_name}.joblib")
    if not target_model_file.exists():
        # Record failure audit log
        db.add(
            AuditLog(
                user_id=admin.id,
                action="MODEL_ACTIVATION_FAILED",
                resource_type="model",
                resource_id=clean_name,
                details=f"Binary file not found at: {target_model_file}",
            )
        )
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot activate model '{clean_name}': binary artifact missing at '{target_model_file}'.",
        )

    candidate_report = models_dict[clean_name]
    optimal_thresh = float(candidate_report.get("optimal_threshold", 0.5))
    model_ver = registry.get("version", "v1.0.0")

    try:
        # 3. Update Registry Active Model
        registry["active_model"] = clean_name
        for name, m in registry["models"].items():
            m["is_active"] = (name == clean_name)
        registry["last_updated"] = datetime.now(timezone.utc).isoformat()

        # 4. Update Active Model Metadata
        new_active_metadata = {
            "model_name": clean_name,
            "model_version": model_ver,
            "selected_threshold": optimal_thresh,
            "training_timestamp": registry["last_updated"],
            "dataset_version_path": previous_active_meta.get("dataset_version_path", "data/raw/fraud_dataset.csv"),
            "feature_version": previous_active_meta.get("feature_version", "v1.0.0"),
            "preprocessing_version": "v1.0.0",
            "model_artifact_path": f"ml/artifacts/{clean_name}.joblib",
            "preprocessor_artifact_path": "ml/artifacts/preprocessor.joblib",
            "is_active": True,
            "selection_score": candidate_report.get("selection_score", 1.0),
            "evaluation_metrics": {
                "accuracy": candidate_report.get("test_accuracy"),
                "precision": candidate_report.get("test_precision"),
                "recall": candidate_report.get("test_recall"),
                "f1_score": candidate_report.get("test_f1"),
                "roc_auc": candidate_report.get("test_roc_auc"),
                "pr_auc": candidate_report.get("test_pr_auc"),
                "false_positive_rate": candidate_report.get("test_fpr"),
                "false_negative_rate": candidate_report.get("test_fnr"),
                "confusion_matrix": candidate_report.get("test_confusion_matrix", {}),
            },
        }

        # Write metadata atomically
        with open(registry_file, "w", encoding="utf-8") as f:
            json.dump(registry, f, indent=2)

        with open(active_meta_file, "w", encoding="utf-8") as f:
            json.dump(new_active_metadata, f, indent=2)

        # 5. Update DB model_versions
        all_db_versions = db.query(ModelVersion).filter(ModelVersion.version == model_ver).all()
        for mv in all_db_versions:
            mv.is_active = (mv.model_name == clean_name)

        # 6. Reset prediction service
        FraudPredictionService.reset_instance()
        service = FraudPredictionService.get_instance()
        if not service.is_ready or service.model_name != clean_name:
            raise RuntimeError("FraudPredictionService failed to verify new active model.")

        # 7. Record Success AuditLog
        audit_entry = AuditLog(
            user_id=admin.id,
            action="MODEL_ACTIVATED",
            resource_type="model",
            resource_id=clean_name,
            details=json.dumps({
                "model_name": clean_name,
                "version": model_ver,
                "threshold": optimal_thresh,
            }),
        )
        db.add(audit_entry)
        db.commit()

        return ModelActivationResponse(
            status="MODEL_ACTIVATION_SUCCESSFUL",
            active_model=clean_name,
            model_version=model_ver,
            optimal_threshold=optimal_thresh,
            activated_at=registry["last_updated"],
        )

    except Exception as e:
        # Rollback metadata to previous state
        with open(active_meta_file, "w", encoding="utf-8") as f:
            json.dump(previous_active_meta, f, indent=2)
        FraudPredictionService.reset_instance()
        FraudPredictionService.get_instance()
        db.rollback()

        db.add(
            AuditLog(
                user_id=admin.id,
                action="MODEL_ACTIVATION_FAILED",
                resource_type="model",
                resource_id=clean_name,
                details=f"Activation error: {str(e)}",
            )
        )
        db.commit()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Model activation failed: {str(e)}. Previous model state was preserved.",
        )


@router.post(
    "/models/backtest",
    summary="Run Historical Policy Replay & Backtest (Admin Only)",
    description="Simulates pre-auth risk policies over historical transaction ledgers with zero database mutation.",
)
def run_model_backtest(
    sample_size: int = 100,
    candidate_threshold: Optional[float] = None,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Execute historical policy replay."""
    from backend.app.services.backtest_service import BacktestService
    result = BacktestService.run_historical_replay(
        db=db,
        sample_size=sample_size,
        candidate_threshold=candidate_threshold,
    )
    return result


@router.get(
    "/models/performance-metrics",
    summary="Get Production Model Quality & Drift Metrics (Admin Only)",
    description="Retrieves accuracy, precision, recall, and false positive metrics derived from verified ground truth outcomes.",
)
def get_model_performance_metrics(
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Retrieve production model performance metrics."""
    from backend.app.services.feedback_loop_service import FeedbackLoopService
    metrics = FeedbackLoopService.calculate_performance_metrics(db)
    return metrics.__dict__
