"""Pydantic schemas for Dashboard Statistics & Real Analytics (Phase 15)."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class DashboardStatsResponse(BaseModel):
    """Holistic system and risk statistics derived strictly from actual database records."""

    total_transactions: int = Field(0, description="Total recorded transactions")
    total_customers: int = Field(0, description="Total registered customer profiles")
    total_investigations: int = Field(0, description="Total investigation cases opened")
    fraud_transactions: int = Field(0, description="Transactions predicted or confirmed as fraud")
    genuine_transactions: int = Field(0, description="Transactions classified as genuine")
    fraud_ratio: float = Field(0.0, description="Fraud rate percentage across population")
    high_risk_transactions: int = Field(0, description="Count of HIGH risk transactions")
    medium_risk_transactions: int = Field(0, description="Count of MEDIUM risk transactions")
    low_risk_transactions: int = Field(0, description="Count of LOW risk transactions")
    average_risk_score: float = Field(0.0, description="Mean risk score across all transactions")
    average_fraud_probability: float = Field(0.0, description="Mean ML fraud probability")
    open_investigations: int = Field(0, description="Active investigations in OPEN state")
    under_review_investigations: int = Field(0, description="Investigations in UNDER_REVIEW state")
    resolved_investigations: int = Field(0, description="Completed investigations in RESOLVED state")
    confirmed_fraud_cases: int = Field(0, description="Resolved investigations confirmed as fraud")
    genuine_cases: int = Field(0, description="Resolved investigations ruled genuine")
    recent_transactions: List[Dict[str, Any]] = Field(default_factory=list)
    recent_high_risk_activity: List[Dict[str, Any]] = Field(default_factory=list)
    recent_investigations: List[Dict[str, Any]] = Field(default_factory=list)
    risk_distribution: Dict[str, Any] = Field(default_factory=dict)
    transaction_trends: List[Dict[str, Any]] = Field(default_factory=list)
    transaction_type_risk: List[Dict[str, Any]] = Field(default_factory=list)
    device_risk: List[Dict[str, Any]] = Field(default_factory=list)
    location_risk: List[Dict[str, Any]] = Field(default_factory=list)
    ai_risk_intelligence: Dict[str, Any] = Field(default_factory=dict)
    model_comparison: Dict[str, Any] = Field(default_factory=dict)
    top_risk_factors: List[Dict[str, Any]] = Field(default_factory=list)
    active_model_info: Dict[str, Any] = Field(default_factory=dict)
    system_status: Dict[str, Any] = Field(default_factory=dict)


class AnalyticsReportsResponse(BaseModel):
    """Detailed reporting data for executive and compliance audits."""

    summary: Dict[str, Any]
    risk_breakdown: List[Dict[str, Any]]
    merchant_category_analysis: List[Dict[str, Any]]
    investigation_outcomes: Dict[str, Any]
    model_performance_summary: Dict[str, Any]
    timeline_series: List[Dict[str, Any]]
