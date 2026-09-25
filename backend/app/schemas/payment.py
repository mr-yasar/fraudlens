"""Schemas for Payment Initiation, Pre-Authorization Risk Engine, and Payment Intent Domain."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class PaymentDecision(str, Enum):
    """Pre-authorization gateway fraud decision."""
    ALLOW = "ALLOW"
    REVIEW = "REVIEW"
    BLOCK = "BLOCK"


class RiskLevelEnum(str, Enum):
    """Standardized risk severity levels."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class PaymentLifecycleStatus(str, Enum):
    """Explicit Payment and Transaction Lifecycle states."""
    CREATED = "CREATED"
    INITIATED = "INITIATED"
    ANALYZING = "ANALYZING"
    RISK_EVALUATING = "RISK_EVALUATING"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    PENDING_VERIFICATION = "PENDING_VERIFICATION"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    BLOCKED = "BLOCKED"
    SUBMITTED = "SUBMITTED"
    PROCESSING = "PROCESSING"
    AUTHORIZED = "AUTHORIZED"
    SUCCEEDED = "SUCCEEDED"
    SUCCESS = "SUCCESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"


class PaymentInitiateRequest(BaseModel):
    """Payload sent by checkout payment screen when user initiates payment."""

    customer_id: str = Field(..., description="Customer identifier initiating transaction", min_length=1)
    amount: float = Field(..., description="Payment monetary amount", gt=0.0)
    currency: str = Field(default="USD", description="Currency code (USD, INR, EUR, GBP)")
    merchant_name: str = Field(default="Acme Store", description="Name of merchant or billing entity")
    merchant_category: str = Field(default="retail", description="Merchant category code or sector")
    payment_method: str = Field(default="credit_card", description="Payment instrument (credit_card, debit_card, upi, bank_transfer)")
    device_type: str = Field(default="web", description="Device platform (web, mobile_ios, mobile_android, pos, unknown_bot)")
    location: str = Field(default="US", description="Client geographic region or city")
    transaction_country: str = Field(default="US", description="Two-letter ISO transaction origin country")
    transaction_type: str = Field(default="online_payment", description="Transaction processing channel")
    beneficiary_name: Optional[str] = Field(default=None, description="Optional explicit transfer recipient / beneficiary name")
    beneficiary_account: Optional[str] = Field(default=None, description="Optional recipient account number or UPI ID")
    failed_attempts: int = Field(default=0, ge=0, description="Preceding failed authentication attempts in session")
    account_age_days: Optional[float] = Field(default=None, ge=0.0, description="Optional override for account tenure")
    idempotency_key: Optional[str] = Field(default=None, description="Optional client idempotency key")
    notes: Optional[str] = Field(default=None, description="Optional client transaction note / reference")


class TriggeredRule(BaseModel):
    """Individual rule triggered during pre-authorization evaluation."""

    rule_id: str
    rule_name: str
    severity: str  # 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'
    description: str
    action_impact: str  # 'FLAG_REVIEW', 'ENFORCE_BLOCK', 'INCREASE_SCORE'


class RiskFactorExplanation(BaseModel):
    """Human-readable explanation of risk driver."""

    factor: str
    impact_score: float
    severity: str
    detail: str


class StructuredShapFactor(BaseModel):
    """Structured SHAP factor explanation."""
    feature: str
    raw_value: Any
    contribution: float
    direction: str  # "INCREASES_RISK" or "DECREASES_RISK"
    severity: str   # "LOW", "MEDIUM", "HIGH", "CRITICAL"
    human_interpretation: str


class PreAuthDecisionResult(BaseModel):
    """Authoritative pre-authorization decision produced by backend risk engine."""

    transaction_id: str
    payment_id: Optional[str] = None
    customer_id: str
    amount: float
    currency: str
    fraud_probability: float = Field(..., description="Raw ML model output [0.0, 1.0]")
    risk_score: int = Field(..., description="Deterministic multi-factor score [0, 100]")
    risk_level: RiskLevelEnum = Field(..., description="Risk tier: LOW, MEDIUM, HIGH")
    decision: PaymentDecision = Field(..., description="Authoritative gateway action: ALLOW, REVIEW, BLOCK")
    lifecycle_status: str = Field(default="CREATED", description="Explicit payment domain lifecycle status")
    triggered_rules: List[TriggeredRule] = Field(default_factory=list)
    top_risk_factors: List[RiskFactorExplanation] = Field(default_factory=list)
    structured_explanations: List[StructuredShapFactor] = Field(default_factory=list)
    shap_status: str = Field(default="COMPUTED", description="Status of SHAP explanation ('COMPUTED' or 'EXPLANATION_UNAVAILABLE')")
    explanation_id: Optional[str] = None
    case_id: Optional[str] = None
    approval_id: Optional[str] = None
    verification_required: bool = False
    is_new_beneficiary: bool = False
    is_new_device: bool = False
    simulated_balance_before: Optional[float] = None
    simulated_balance_after: Optional[float] = None
    external_payment_id: Optional[str] = None
    provider_name: Optional[str] = None
    provider_status: Optional[str] = None
    idempotency_key: Optional[str] = None
    idempotent_replay: bool = False
    behavioural_deviation_score: float = 0.0
    is_cold_start: bool = False
    model_name: str = "xgboost"
    model_version: str = "v1.0.0"
    processing_time_ms: float = 0.0
    ready_for_provider: bool = Field(..., description="True only if decision == ALLOW")
    status_message: str = ""
    # Fraud Intelligence Fabric additions
    device_risk_score: Optional[float] = None
    session_risk_score: Optional[float] = None
    network_risk_score: Optional[float] = None
    connected_entities_count: Optional[int] = None
    behaviour_intelligence: Optional[Dict[str, Any]] = None
    device_session_intelligence: Optional[Dict[str, Any]] = None
    network_intelligence: Optional[Dict[str, Any]] = None
    otp_code: Optional[str] = Field(default=None, description="Dynamic 6-digit OTP generated for SMS verification challenge")


class ApprovalActionRequest(BaseModel):
    """Payload to approve, reject, or expire a pending verification challenge."""
    action: str = Field(..., description="Action: 'APPROVE', 'REJECT', or 'EXPIRE'")
    notes: Optional[str] = Field(default=None, description="Optional user or reviewer remarks")
    challenge_response: Optional[str] = Field(default=None, description="Security confirmation code/OTP if required")


class ApprovalDetailResponse(BaseModel):
    """Details of a step-up verification / approval request."""
    approval_id: str
    payment_id: Optional[str]
    transaction_id: Optional[str]
    customer_id: str
    status: str
    amount: float
    currency: str
    risk_score: int
    risk_level: str
    fraud_probability: float
    challenge_type: str
    notes: Optional[str]
    requested_at: datetime
    responded_at: Optional[datetime]
    expires_at: datetime
    is_expired: bool = False
    otp_code: Optional[str] = Field(default=None, description="6-digit SMS OTP verification code")


class BeneficiaryResponse(BaseModel):
    """Beneficiary / Recipient item representation."""
    id: int
    customer_id: str
    beneficiary_name: str
    beneficiary_account: Optional[str] = None
    category: str
    trust_score: float
    is_trusted: bool
    total_transfers: int
    last_used_at: Optional[datetime] = None


class BeneficiaryCreateRequest(BaseModel):
    """Payload to add a new beneficiary manually."""
    beneficiary_name: str = Field(..., min_length=1)
    beneficiary_account: Optional[str] = None
    category: str = Field(default="transfer")


class CustomerWalletResponse(BaseModel):
    """Customer wallet, balance, and behavioral baseline summary."""
    customer_id: str
    simulated_balance: float
    currency: str
    account_age_days: float
    known_beneficiaries: List[BeneficiaryResponse] = Field(default_factory=list)
    known_devices: List[str] = Field(default_factory=list)
    usual_locations: List[str] = Field(default_factory=list)
    total_transactions: int = 0
    historical_avg_amount: float = 0.0
