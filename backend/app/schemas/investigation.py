"""Pydantic schemas for Fraud Investigation & Case Management (Phase 13)."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


class InvestigationStatus(str, Enum):
    """Permitted investigation lifecycle statuses."""

    OPEN = "OPEN"
    UNDER_REVIEW = "UNDER_REVIEW"
    RESOLVED = "RESOLVED"


class InvestigationDecision(str, Enum):
    """Permitted investigation case determinations."""

    CONFIRMED_FRAUD = "CONFIRMED_FRAUD"
    GENUINE = "GENUINE"


class InvestigationCreateInput(BaseModel):
    """Input payload for opening a new fraud investigation case."""

    transaction_id: str = Field(..., min_length=1, max_length=100, description="Target transaction identifier")
    notes: Optional[str] = Field(None, max_length=5000, description="Initial case notes or investigation reasoning")
    investigator_id: Optional[int] = Field(None, description="Optional user ID of assigned investigator")


class InvestigationUpdateInput(BaseModel):
    """Input payload for updating an existing investigation case."""

    status: Optional[str] = Field(None, description="Updated status: 'OPEN', 'UNDER_REVIEW', or 'RESOLVED'")
    decision: Optional[str] = Field(None, description="Investigator determination: 'CONFIRMED_FRAUD' or 'GENUINE'")
    notes: Optional[str] = Field(None, max_length=5000, description="Updated investigator notes or rationale")
    investigator_id: Optional[int] = Field(None, description="Reassigned investigator user ID")

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v_upper = v.upper().strip()
            valid_statuses = {s.value for s in InvestigationStatus}
            if v_upper not in valid_statuses:
                raise ValueError(f"Invalid status '{v}'. Permitted values: {sorted(valid_statuses)}")
            return v_upper
        return v

    @field_validator("decision")
    @classmethod
    def validate_decision(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v_upper = v.upper().strip()
            valid_decisions = {d.value for d in InvestigationDecision}
            if v_upper not in valid_decisions:
                raise ValueError(f"Invalid decision '{v}'. Permitted values: {sorted(valid_decisions)}")
            return v_upper
        return v


class InvestigationSummaryResponse(BaseModel):
    """Summary representation of an investigation case for listings."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    case_id: str
    transaction_id: str
    investigator_id: Optional[int] = None
    investigator_name: Optional[str] = None
    investigator_email: Optional[str] = None
    status: str
    decision: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    amount: Optional[float] = None
    risk_score: Optional[float] = None
    risk_level: Optional[str] = None
    prediction: Optional[str] = None


class InvestigationDetailResponse(InvestigationSummaryResponse):
    """Detailed case view containing full customer context and AI explanations."""

    customer_id: Optional[str] = None
    fraud_probability: Optional[float] = None
    top_shap_factors: List[Dict[str, Any]] = Field(default_factory=list)
    transaction_details: Optional[Dict[str, Any]] = None


class InvestigationListResponse(BaseModel):
    """Paginated collection of investigation cases."""

    items: List[InvestigationSummaryResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
