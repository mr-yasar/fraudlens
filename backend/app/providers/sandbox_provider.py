"""Sandbox Payment Provider Adapter for Realistic UAT / Demo Execution.

Simulates an external payment gateway (e.g., Stripe Sandbox / Mock UAT)
with realistic IDs, authorization codes, signature computation, and state lifecycles.
"""

import hmac
import hashlib
import json
import uuid
import time
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from backend.app.providers.base import (
    PaymentProviderAdapter,
    ProviderPaymentRequest,
    ProviderPaymentResult,
    ProviderPaymentStatus,
    ProviderWebhookEvent,
    ProviderErrorType,
    ProviderDeclinedException,
    ProviderTimeoutException,
)


class SandboxPaymentProvider(PaymentProviderAdapter):
    """Realistic Sandbox Payment Provider adapter."""

    def __init__(
        self,
        provider_name: str = "sandbox_gateway",
        webhook_secret: str = "whsec_sandbox_fraudlens_demo_secret_998877",
        simulated_latency_ms: float = 20.0,
    ):
        self._provider_name = provider_name
        self.webhook_secret = webhook_secret
        self.simulated_latency_ms = simulated_latency_ms
        self._ledger: Dict[str, Dict[str, Any]] = {}

    @property
    def provider_name(self) -> str:
        return self._provider_name

    def create_payment(self, request: ProviderPaymentRequest) -> ProviderPaymentResult:
        """Submit payment to sandbox gateway."""
        if self.simulated_latency_ms > 0:
            time.sleep(self.simulated_latency_ms / 1000.0)

        # Standard sandbox decline rule: amount ending in .99 or specific trigger amounts
        if request.amount == 9999.99:
            raise ProviderDeclinedException(
                "Sandbox Declined: Insufficient balance on test instrument",
                provider_name=self.provider_name,
            )

        external_id = f"pi_sand_{uuid.uuid4().hex[:14]}"
        auth_code = f"AUTH_{uuid.uuid4().hex[:6].upper()}"

        record = {
            "internal_payment_id": request.internal_payment_id,
            "external_payment_id": external_id,
            "authorization_code": auth_code,
            "amount": request.amount,
            "currency": request.currency.upper(),
            "payment_method": request.payment_method,
            "merchant_name": request.merchant_name,
            "status": ProviderPaymentStatus.SUCCEEDED,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "idempotency_key": request.idempotency_key,
        }
        self._ledger[external_id] = record

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
                "authorization_code": auth_code,
                "network_status": "approved_by_network",
                "risk_score": 5,
                "seller_message": "Payment complete.",
            },
        )

    def get_payment_status(self, external_payment_id: str) -> ProviderPaymentResult:
        """Fetch status of sandbox payment."""
        record = self._ledger.get(external_payment_id)
        if not record:
            return ProviderPaymentResult(
                success=False,
                internal_payment_id="unknown",
                external_payment_id=external_payment_id,
                provider_name=self.provider_name,
                provider_status=ProviderPaymentStatus.UNKNOWN,
                amount=0.0,
                currency="USD",
                error_message="Sandbox transaction not found",
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
        """Void / Cancel sandbox payment."""
        record = self._ledger.get(external_payment_id)
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
        """Validate HMAC-SHA256 signature."""
        if not signature_header:
            return False
        # Remove 't=...,v1=' prefix if present (Stripe-like header formatting)
        sig = signature_header
        if "v1=" in signature_header:
            parts = dict(item.split("=") for item in signature_header.split(",") if "=" in item)
            sig = parts.get("v1", "")

        expected = hmac.new(
            self.webhook_secret.encode("utf-8"),
            payload_bytes,
            hashlib.sha256,
        ).hexdigest()
        return hmac.compare_digest(expected, sig)

    def generate_webhook_signature(self, payload_bytes: bytes) -> str:
        """Helper to generate valid signature for tests."""
        return hmac.new(
            self.webhook_secret.encode("utf-8"),
            payload_bytes,
            hashlib.sha256,
        ).hexdigest()

    def parse_webhook_event(self, payload: Dict[str, Any]) -> ProviderWebhookEvent:
        """Parse raw sandbox webhook payload into normalized event model."""
        event_id = payload.get("id", f"evt_sand_{uuid.uuid4().hex[:10]}")
        event_type = payload.get("type", "payment_intent.succeeded")
        data_obj = payload.get("data", {}).get("object", payload)

        ext_id = data_obj.get("id", data_obj.get("external_payment_id", "unknown"))
        status_raw = str(data_obj.get("status", "succeeded")).upper()

        status_mapping = {
            "SUCCEEDED": ProviderPaymentStatus.SUCCEEDED,
            "CAPTURED": ProviderPaymentStatus.CAPTURED,
            "AUTHORIZED": ProviderPaymentStatus.AUTHORIZED,
            "FAILED": ProviderPaymentStatus.FAILED,
            "CANCELLED": ProviderPaymentStatus.CANCELLED,
            "CANCELED": ProviderPaymentStatus.CANCELLED,
            "REFUNDED": ProviderPaymentStatus.REFUNDED,
        }
        status = status_mapping.get(status_raw, ProviderPaymentStatus.UNKNOWN)

        return ProviderWebhookEvent(
            event_id=event_id,
            event_type=event_type,
            provider_name=self.provider_name,
            internal_payment_id=data_obj.get("metadata", {}).get("internal_payment_id") or data_obj.get("internal_payment_id"),
            external_payment_id=ext_id,
            status=status,
            amount=float(data_obj.get("amount", 0.0)),
            currency=data_obj.get("currency", "USD").upper(),
            raw_payload=payload,
            signature_valid=True,
        )
