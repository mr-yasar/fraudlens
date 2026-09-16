"""Payment Provider Abstraction Layer.

Defines provider-independent interfaces, domain models, and normalized exceptions.
The FraudLens fraud engine interacts exclusively through this abstraction,
ensuring complete decoupling from specific payment gateways.
"""

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class ProviderPaymentStatus(str, Enum):
    """Normalized payment statuses across all external payment providers."""
    PENDING = "PENDING"
    REQUIRES_ACTION = "REQUIRES_ACTION"
    PROCESSING = "PROCESSING"
    AUTHORIZED = "AUTHORIZED"
    CAPTURED = "CAPTURED"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    REFUNDED = "REFUNDED"
    UNKNOWN = "UNKNOWN"


class ProviderErrorType(str, Enum):
    """Normalized error classifications for external provider failures."""
    TIMEOUT = "TIMEOUT"
    NETWORK_ERROR = "NETWORK_ERROR"
    DECLINED = "DECLINED"
    INSUFFICIENT_FUNDS = "INSUFFICIENT_FUNDS"
    AUTHENTICATION_FAILED = "AUTHENTICATION_FAILED"
    MALFORMED_RESPONSE = "MALFORMED_RESPONSE"
    RATE_LIMITED = "RATE_LIMITED"
    CONFIGURATION_ERROR = "CONFIGURATION_ERROR"
    UNKNOWN_ERROR = "UNKNOWN_ERROR"


# Normalized Exceptions
class PaymentProviderException(Exception):
    """Base exception for payment provider operations."""
    def __init__(
        self,
        message: str,
        error_type: ProviderErrorType = ProviderErrorType.UNKNOWN_ERROR,
        provider_name: str = "unknown",
        raw_error: Optional[Any] = None,
        status_code: Optional[int] = None,
    ):
        super().__init__(message)
        self.message = message
        self.error_type = error_type
        self.provider_name = provider_name
        self.raw_error = raw_error
        self.status_code = status_code


class ProviderTimeoutException(PaymentProviderException):
    """Raised when external provider communication times out."""
    def __init__(self, message: str, provider_name: str, raw_error: Optional[Any] = None):
        super().__init__(message, ProviderErrorType.TIMEOUT, provider_name, raw_error, status_code=504)


class ProviderNetworkException(PaymentProviderException):
    """Raised when network connectivity to provider fails."""
    def __init__(self, message: str, provider_name: str, raw_error: Optional[Any] = None):
        super().__init__(message, ProviderErrorType.NETWORK_ERROR, provider_name, raw_error, status_code=502)


class ProviderDeclinedException(PaymentProviderException):
    """Raised when provider declines the card / payment method."""
    def __init__(self, message: str, provider_name: str, raw_error: Optional[Any] = None):
        super().__init__(message, ProviderErrorType.DECLINED, provider_name, raw_error, status_code=400)


class ProviderWebhookSignatureException(PaymentProviderException):
    """Raised when webhook signature verification fails."""
    def __init__(self, message: str, provider_name: str):
        super().__init__(message, ProviderErrorType.AUTHENTICATION_FAILED, provider_name, status_code=401)


class ProviderPaymentRequest(BaseModel):
    """Provider-independent request payload to initiate / capture payment."""
    internal_payment_id: str = Field(..., description="FraudLens internal unique payment ID")
    customer_id: str = Field(..., description="Customer identifier")
    amount: float = Field(..., gt=0, description="Authorized payment amount")
    currency: str = Field(default="USD", min_length=3, max_length=3, description="ISO 4217 currency code")
    payment_method: str = Field(default="card", description="Payment method type")
    merchant_name: str = Field(..., description="Recipient merchant name")
    idempotency_key: str = Field(..., description="Unique client idempotency key")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional context metadata")


class ProviderPaymentResult(BaseModel):
    """Provider-independent result returned from payment capture / authorization."""
    success: bool
    internal_payment_id: str
    external_payment_id: str
    provider_name: str
    provider_status: ProviderPaymentStatus
    amount: float
    currency: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    raw_response: Dict[str, Any] = Field(default_factory=dict)
    error_message: Optional[str] = None
    error_type: Optional[ProviderErrorType] = None


class ProviderWebhookEvent(BaseModel):
    """Normalized webhook payload received from payment provider."""
    event_id: str
    event_type: str
    provider_name: str
    internal_payment_id: Optional[str] = None
    external_payment_id: str
    status: ProviderPaymentStatus
    amount: Optional[float] = None
    currency: Optional[str] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    raw_payload: Dict[str, Any] = Field(default_factory=dict)
    signature_valid: bool = False


class PaymentProviderAdapter(ABC):
    """Abstract interface that all payment gateway adapters must implement."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Name of the payment provider."""
        pass

    @abstractmethod
    def create_payment(self, request: ProviderPaymentRequest) -> ProviderPaymentResult:
        """Submit payment request to provider for authorization / capture."""
        pass

    @abstractmethod
    def get_payment_status(self, external_payment_id: str) -> ProviderPaymentResult:
        """Query external provider for the current status of a payment."""
        pass

    @abstractmethod
    def cancel_payment(self, external_payment_id: str, reason: str = "fraud_prevented") -> ProviderPaymentResult:
        """Cancel or void a pending/authorized payment on the provider."""
        pass

    @abstractmethod
    def verify_webhook_signature(self, payload_bytes: bytes, signature_header: str) -> bool:
        """Cryptographically verify the incoming webhook signature."""
        pass

    @abstractmethod
    def parse_webhook_event(self, payload: Dict[str, Any]) -> ProviderWebhookEvent:
        """Parse raw provider webhook JSON into a normalized ProviderWebhookEvent."""
        pass
