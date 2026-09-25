"""Pydantic schemas for Customer Management."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class CustomerBase(BaseModel):
    """Base schema for customer entity."""

    customer_id: str = Field(..., min_length=1, max_length=100, description="Unique customer identifier")
    account_age_days: Optional[int] = Field(None, ge=0, description="Customer account age in days")
    name: Optional[str] = Field(None, description="Full customer name")
    email: Optional[str] = Field(None, description="Customer email address")
    risk_segment: Optional[str] = Field("Standard", description="Risk tier segment")


class CustomerResponse(CustomerBase):
    """Schema representing a customer in listings and summaries."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    transaction_count: int = Field(0, description="Total count of transactions for this customer")
    historical_avg_amount: float = Field(0.0, description="Calculated average transaction amount")
    high_risk_count: int = Field(0, description="Count of transactions flagged HIGH risk")
    fraud_transaction_count: int = Field(0, description="Count of confirmed fraud transactions")


class CustomerBehavioralStats(BaseModel):
    """Calculated behavioural statistics derived dynamically from database transactions."""

    transaction_count: int = Field(0, description="Total historical transactions count")
    average_transaction_amount: float = Field(0.0, description="Average transaction amount in base currency")
    min_transaction_amount: float = Field(0.0, description="Minimum recorded transaction amount")
    max_transaction_amount: float = Field(0.0, description="Maximum recorded transaction amount")
    recent_transaction_count: int = Field(0, description="Transactions count in the last 30 days")
    high_risk_transaction_count: int = Field(0, description="Count of transactions flagged with HIGH risk level")
    fraud_transaction_count: int = Field(0, description="Count of transactions classified as FRAUD")


class CustomerDetailResponse(CustomerResponse):
    """Detailed customer profile including behavioural statistics and recent transaction history."""

    behavioral_stats: CustomerBehavioralStats
    recent_transactions: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="List of recent transactions recorded for this customer",
    )


class CustomerListResponse(BaseModel):
    """Paginated customer collection response."""

    items: List[CustomerResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
