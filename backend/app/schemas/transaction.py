"""Pydantic schemas for Transaction Management & Real-Time Risk Evaluation."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field
from backend.app.schemas.prediction import TransactionPredictionInput


class TransactionCreateInput(TransactionPredictionInput):
    """Input payload for creating and scoring a new financial transaction."""
    pass


class TransactionSummaryResponse(BaseModel):
    """Summary representation of a persisted transaction."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    transaction_id: str
    customer_id: str
    amount: float
    transaction_hour: int
    merchant_category: Optional[str] = None
    transaction_country: Optional[str] = None
    geo_location_region: Optional[str] = None
    device_type: Optional[str] = None
    transaction_type: Optional[str] = None
    fraud_probability: Optional[float] = None
    prediction: Optional[str] = None
    risk_score: Optional[float] = None
    risk_level: Optional[str] = None
    created_at: datetime


class TransactionDetailResponse(TransactionSummaryResponse):
    """Comprehensive transaction representation including model metadata and explanation factors."""

    model_name: Optional[str] = None
    model_version: Optional[str] = None
    threshold_used: Optional[float] = None
    risk_factors: List[Dict[str, Any]] = Field(default_factory=list)
    top_shap_factors: Optional[List[Dict[str, Any]]] = None
    shap_explanations: List[Dict[str, Any]] = Field(default_factory=list)


class TransactionListResponse(BaseModel):
    """Paginated transaction collection response."""

    items: List[TransactionSummaryResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class RealtimeEvaluationResponse(BaseModel):
    """Standardized response schema for Real-Time Transaction Risk Evaluation (Phase 12)."""

    transaction_id: str
    prediction: str = Field(..., description="Classification result: 'FRAUD' or 'GENUINE'")
    fraud_probability: float = Field(..., ge=0.0, le=1.0, description="ML fraud probability [0.0 - 1.0]")
    risk_score: int = Field(..., ge=0, le=100, description="Multi-factor risk score [0 - 100]")
    risk_level: str = Field(..., description="Risk level category: 'LOW', 'MEDIUM', 'HIGH'")
    model_name: str = Field(..., description="Active ML model utilized")
    model_version: str = Field(..., description="Active ML model version")
    threshold_used: float = Field(..., ge=0.0, le=1.0, description="Classification threshold applied")
    risk_factors: List[Dict[str, Any]] = Field(default_factory=list, description="Breakdown of multi-factor risk signals")
    top_explanations: List[Dict[str, Any]] = Field(default_factory=list, description="Top SHAP feature attribution factors")
    alert_generated: bool = Field(..., description="True if HIGH risk generated an investigator alert / audit event")
    anomaly_score: Optional[float] = Field(None, description="Unsupervised Isolation Forest anomaly score")
    anomaly_status: Optional[str] = Field(None, description="Anomaly status: 'AVAILABLE' | 'UNAVAILABLE'")
    uncertainty_score: Optional[float] = Field(None, description="Model prediction uncertainty score [0.0 - 1.0]")
    uncertainty_level: Optional[str] = Field(None, description="Uncertainty level: 'LOW' | 'MODERATE' | 'HIGH'")
    counterfactual: Optional[Dict[str, Any]] = Field(None, description="Verified counterfactual perturbation scenario")
    composed_explanation: Optional[Dict[str, Any]] = Field(None, description="Evidence-grounded investigator narrative")
