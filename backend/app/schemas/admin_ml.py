"""Pydantic schemas for Admin ML & Dataset Management (Phase 14)."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class DatasetStatusResponse(BaseModel):
    """Admin-only status and audit report for the active training dataset."""

    dataset_name: str
    file_format: str
    row_count: int
    column_count: int
    target_column: str
    target_distribution: Dict[str, Any]
    validation_status: str
    leakage_findings: List[Dict[str, Any]]
    last_validated: Optional[str] = None


class ModelVersionInfo(BaseModel):
    """Detailed metadata and test performance metrics for a trained model candidate."""

    id: Optional[int] = None
    model_name: str
    version: str
    accuracy: Optional[float] = None
    precision: Optional[float] = None
    recall: Optional[float] = None
    f1_score: Optional[float] = None
    roc_auc: Optional[float] = None
    pr_auc: Optional[float] = None
    false_positive_rate: Optional[float] = None
    false_negative_rate: Optional[float] = None
    optimal_threshold: Optional[float] = None
    is_active: bool = False
    trained_at: Optional[str] = None
    selection_score: Optional[float] = None


class ModelListResponse(BaseModel):
    """Collection of candidate model evaluations in the ML model registry."""

    models: List[ModelVersionInfo]
    active_model: Optional[str] = None
    model_version: str
    last_updated: Optional[str] = None


class ModelComparisonResponse(BaseModel):
    """Side-by-side evaluation comparison across all trained model algorithms."""

    version: str
    active_model: str
    comparison: Dict[str, Any]
    selection_criteria: Dict[str, Any]


class TrainModelRequest(BaseModel):
    """Configuration payload for initiating on-demand model retraining."""

    dataset_path: Optional[str] = Field("data/raw/fraud_dataset.csv", description="Relative path to validated training dataset")
    model_version: Optional[str] = Field("v1.0.0", description="Semantic version tag for new model artifacts")
    rf_n_estimators: Optional[int] = Field(100, ge=10, le=500, description="Random Forest trees count")
    xgb_n_estimators: Optional[int] = Field(100, ge=10, le=500, description="XGBoost boosting rounds")


class TrainModelResponse(BaseModel):
    """Result summary of complete automated training and selection pipeline."""

    status: str
    model_version: str
    selected_model: str
    active_metadata: Dict[str, Any]
    comparison: Dict[str, Any]
    trained_models: List[str]


class ModelActivationResponse(BaseModel):
    """Confirmation payload of active production model deployment."""

    status: str
    active_model: str
    model_version: str
    optimal_threshold: float
    activated_at: str
