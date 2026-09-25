"""Database models package exporting all SQLAlchemy declarative models."""

from backend.app.core.database import Base
from backend.app.models.user import User
from backend.app.models.customer import Customer
from backend.app.models.merchant import Merchant
from backend.app.models.transaction import Transaction
from backend.app.models.investigation import Investigation
from backend.app.models.shap_explanation import ShapExplanation
from backend.app.models.model_version import ModelVersion
from backend.app.models.audit_log import AuditLog
from backend.app.models.payment_intent import PaymentIntent, PaymentAttempt, WebhookEventRecord, PaymentLifecycleStatus
from backend.app.models.idempotency import IdempotencyRecord
from backend.app.models.alert import Alert
from backend.app.models.beneficiary import Beneficiary
from backend.app.models.device import CustomerDevice
from backend.app.models.approval import TransactionApproval, ApprovalStatus

__all__ = [
    "Base",
    "User",
    "Customer",
    "Merchant",
    "Transaction",
    "Investigation",
    "ShapExplanation",
    "ModelVersion",
    "AuditLog",
    "PaymentIntent",
    "PaymentAttempt",
    "WebhookEventRecord",
    "PaymentLifecycleStatus",
    "IdempotencyRecord",
    "Alert",
    "Beneficiary",
    "CustomerDevice",
    "TransactionApproval",
    "ApprovalStatus",
]
