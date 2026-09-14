"""Pydantic schemas package."""

from backend.app.schemas.user import (
    UserRole,
    Token,
    TokenPayload,
    LoginRequest,
    UserBase,
    UserCreate,
    UserUpdate,
    UserOut,
)
from backend.app.schemas.prediction import (
    TransactionPredictionInput,
    PredictionResponse,
    LocalExplanationResponse,
    GlobalExplanationResponse,
)

from backend.app.schemas.customer import (
    CustomerBase,
    CustomerResponse,
    CustomerBehavioralStats,
    CustomerDetailResponse,
    CustomerListResponse,
)
from backend.app.schemas.transaction import (
    TransactionCreateInput,
    TransactionSummaryResponse,
    TransactionDetailResponse,
    TransactionListResponse,
    RealtimeEvaluationResponse,
)

from backend.app.schemas.investigation import (
    InvestigationStatus,
    InvestigationDecision,
    InvestigationCreateInput,
    InvestigationUpdateInput,
    InvestigationSummaryResponse,
    InvestigationDetailResponse,
    InvestigationListResponse,
)
from backend.app.schemas.admin_ml import (
    DatasetStatusResponse,
    ModelVersionInfo,
    ModelListResponse,
    ModelComparisonResponse,
    TrainModelRequest,
    TrainModelResponse,
    ModelActivationResponse,
)

from backend.app.schemas.dashboard import (
    DashboardStatsResponse,
    AnalyticsReportsResponse,
)
from backend.app.schemas.audit_log import (
    AuditLogResponse,
    AuditLogListResponse,
)

__all__ = [
    "UserRole",
    "Token",
    "TokenPayload",
    "LoginRequest",
    "UserBase",
    "UserCreate",
    "UserUpdate",
    "UserOut",
    "TransactionPredictionInput",
    "PredictionResponse",
    "LocalExplanationResponse",
    "GlobalExplanationResponse",
    "CustomerBase",
    "CustomerResponse",
    "CustomerBehavioralStats",
    "CustomerDetailResponse",
    "CustomerListResponse",
    "TransactionCreateInput",
    "TransactionSummaryResponse",
    "TransactionDetailResponse",
    "TransactionListResponse",
    "RealtimeEvaluationResponse",
    "InvestigationStatus",
    "InvestigationDecision",
    "InvestigationCreateInput",
    "InvestigationUpdateInput",
    "InvestigationSummaryResponse",
    "InvestigationDetailResponse",
    "InvestigationListResponse",
    "DatasetStatusResponse",
    "ModelVersionInfo",
    "ModelListResponse",
    "ModelComparisonResponse",
    "TrainModelRequest",
    "TrainModelResponse",
    "ModelActivationResponse",
    "DashboardStatsResponse",
    "AnalyticsReportsResponse",
    "AuditLogResponse",
    "AuditLogListResponse",
]
