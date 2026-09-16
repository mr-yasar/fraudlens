"""Mock Payment Provider for Testing and Fault Injection.

Allows deterministic testing of timeouts, network failures, declines,
and successful authorizations without any external network dependency.
"""

import hmac
import hashlib
import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from backend.app.providers.base import (
    PaymentProviderAdapter,
    ProviderPaymentRequest,
    ProviderPaymentResult,
    ProviderPaymentStatus,
    ProviderWebhookEvent,
    ProviderErrorType,
    ProviderTimeoutException,
    ProviderNetworkException,
    ProviderDeclinedException,
)


class MockPaymentProvider(PaymentProviderAdapter):
    """In-memory mock payment provider with configurable outcomes and fault injection."""

    def __init__(
        self,
        provider_name: str = "mock_provider",
        webhook_secret: str = "mock_secret_key_fraudlens_test_12345",
        simulate_fault: Optional[str] = None,
    ):
        self._provider_name = provider_name
        self.webhook_secret = webhook_secret
        self.simulate_fault = simulate_fault
        self.transactions: Dict[str, Dict[str, Any]] = {}

    @property
    def provider_name(self) -> str:
        return self._provider_name

    def create_payment(self, request: ProviderPaymentRequest) -> ProviderPaymentResult:
        """Process payment simulation with fault injection support."""
        if self.simulate_fault == "timeout":
            raise ProviderTimeoutException(
                f"Connection to {self.provider_name} timed out after 5000ms",
                provider_name=self.provider_name,
            )
        elif self.simulate_fault == "network_error":
            raise ProviderNetworkException(
                f"Failed to reach {self.provider_name} gateway endpoint",
                provider_name=self.provider_name,
            )
        elif self.simulate_fault == "decline":
            raise ProviderDeclinedException(
                "Card declined: Do not honor (Code: 05)",
                provider_name=self.provider_name,
            )

        external_id = f"pi_mock_{uuid.uuid4().hex[:12]}"
        self.transactions[external_id] = {
            "internal_payment_id": request.internal_payment_id,
            "external_payment_id": external_id,
            "amount": request.amount,
            "currency": request.currency,
            "status": ProviderPaymentStatus.SUCCEEDED,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        return ProviderPaymentResult(
            success=True,
            internal_payment_id=request.internal_payment_id,
            external_payment_id=external_id,
            provider_name=self.provider_name,
            provider_status=ProviderPaymentStatus.SUCCEEDED,
            amount=request.amount,
            currency=request.currency,
            raw_response={
                "id": external_id,
                "status": "succeeded",
                "payment_method": request.payment_method,
                "idempotency_key": request.idempotency_key,
            },
        )

    def get_payment_status(self, external_payment_id: str) -> ProviderPaymentResult:
        """Query status of simulated payment."""
        record = self.transactions.get(external_payment_id)
        if not record:
            return ProviderPaymentResult(
                success=False,
                internal_payment_id="unknown",
                external_payment_id=external_payment_id,
                provider_name=self.provider_name,
                provider_status=ProviderPaymentStatus.UNKNOWN,
                amount=0.0,
                currency="USD",
                error_message="Payment not found",
                error_type=ProviderErrorType.UNKNOWN_ERROR,
            )

        return ProviderPaymentResult(
            success=True,
            internal_payment_id=record["internal_payment_id"],
            external_payment_id=external_payment_id,
            provider_name=self.provider_name,
            provider_status=record["status"],
            amount=record["amount"],
            currency=record["currency"],
            raw_response=record,
        )

    def cancel_payment(self, external_payment_id: str, reason: str = "fraud_prevented") -> ProviderPaymentResult:
        """Cancel simulated payment."""
        record = self.transactions.get(external_payment_id)
        if record:
            record["status"] = ProviderPaymentStatus.CANCELLED

        return ProviderPaymentResult(
            success=True,
            internal_payment_id=record["internal_payment_id"] if record else "unknown",
            external_payment_id=external_payment_id,
            provider_name=self.provider_name,
            provider_status=ProviderPaymentStatus.CANCELLED,
            amount=record["amount"] if record else 0.0,
            currency=record["currency"] if record else "USD",
            raw_response={"status": "cancelled", "reason": reason},
        )

    def verify_webhook_signature(self, payload_bytes: bytes, signature_header: str) -> bool:
        """HMAC-SHA256 signature verification."""
        if not signature_header:
            return False
        expected_sig = hmac.new(
            self.webhook_secret.encode("utf-8"),
            payload_bytes,
            hashlib.sha256,
        ).hexdigest()
        return hmac.compare_digest(expected_sig, signature_header)

    def parse_webhook_event(self, payload: Dict[str, Any]) -> ProviderWebhookEvent:
        """Parse simulated webhook payload into normalized model."""
        event_id = payload.get("id", f"evt_mock_{uuid.uuid4().hex[:8]}")
        event_type = payload.get("type", "payment_intent.succeeded")
        data_obj = payload.get("data", {}).get("object", {})

        ext_id = data_obj.get("id", payload.get("external_payment_id", "unknown"))
        status_str = data_obj.get("status", "succeeded").upper()

        status_mapping = {
            "SUCCEEDED": ProviderPaymentStatus.SUCCEEDED,
            "FAILED": ProviderPaymentStatus.FAILED,
            "CANCELED": ProviderPaymentStatus.CANCELLED,
            "PROCESSING": ProviderPaymentStatus.PROCESSING,
            "REQUIRES_ACTION": ProviderPaymentStatus.REQUIRES_ACTION,
        }
        status = status_mapping.get(status_str, ProviderPaymentStatus.UNKNOWN)

        return ProviderWebhookEvent(
            event_id=event_id,
            event_type=event_type,
            provider_name=self.provider_name,
            internal_payment_id=data_obj.get("metadata", {}).get("internal_payment_id"),
            external_payment_id=ext_id,
            status=status,
            amount=data_obj.get("amount", payload.get("amount")),
            currency=data_obj.get("currency", payload.get("currency", "USD")),
            raw_payload=payload,
            signature_valid=True,
        )
