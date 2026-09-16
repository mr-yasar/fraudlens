"""Unit tests for Payment Provider Abstraction Layer (Phase 9)."""

import pytest
from backend.app.providers.base import (
    ProviderPaymentRequest,
    ProviderPaymentStatus,
    ProviderTimeoutException,
    ProviderNetworkException,
    ProviderDeclinedException,
)
from backend.app.providers.mock_provider import MockPaymentProvider
from backend.app.providers.sandbox_provider import SandboxPaymentProvider
from backend.app.providers.factory import PaymentProviderFactory


def test_mock_provider_success_flow():
    """Verify MockPaymentProvider succeeds and records transactions."""
    provider = MockPaymentProvider(provider_name="test_mock")
    req = ProviderPaymentRequest(
        internal_payment_id="PAY-TEST-001",
        customer_id="CUST-01",
        amount=150.0,
        currency="USD",
        merchant_name="Acme Corp",
        idempotency_key="idemp-test-01",
    )
    result = provider.create_payment(req)
    assert result.success is True
    assert result.provider_name == "test_mock"
    assert result.provider_status == ProviderPaymentStatus.SUCCEEDED
    assert result.internal_payment_id == "PAY-TEST-001"
    assert result.external_payment_id.startswith("pi_mock_")

    # Verify get status
    status_res = provider.get_payment_status(result.external_payment_id)
    assert status_res.success is True
    assert status_res.provider_status == ProviderPaymentStatus.SUCCEEDED


def test_mock_provider_fault_injection():
    """Verify MockPaymentProvider correctly raises normalized exceptions during faults."""
    # Timeout fault
    timeout_provider = MockPaymentProvider(simulate_fault="timeout")
    req = ProviderPaymentRequest(
        internal_payment_id="PAY-FAULT-001",
        customer_id="CUST-01",
        amount=50.0,
        currency="USD",
        merchant_name="Acme",
        idempotency_key="k1",
    )
    with pytest.raises(ProviderTimeoutException):
        timeout_provider.create_payment(req)

    # Network error fault
    net_provider = MockPaymentProvider(simulate_fault="network_error")
    with pytest.raises(ProviderNetworkException):
        net_provider.create_payment(req)

    # Decline fault
    decline_provider = MockPaymentProvider(simulate_fault="decline")
    with pytest.raises(ProviderDeclinedException):
        decline_provider.create_payment(req)


def test_sandbox_provider_execution_and_signatures():
    """Verify SandboxPaymentProvider authorizes transactions and verifies HMAC signatures."""
    sandbox = SandboxPaymentProvider(
        provider_name="sandbox_test",
        webhook_secret="test_webhook_secret_key_123",
        simulated_latency_ms=0.0,
    )
    req = ProviderPaymentRequest(
        internal_payment_id="PAY-SANDBOX-001",
        customer_id="CUST-SANDBOX-01",
        amount=320.0,
        currency="USD",
        merchant_name="Best Buy",
        idempotency_key="idemp-sand-01",
    )
    result = sandbox.create_payment(req)
    assert result.success is True
    assert result.provider_status == ProviderPaymentStatus.SUCCEEDED
    assert result.external_payment_id.startswith("pi_sand_")

    # Signature verification
    payload_bytes = b'{"id":"evt_123","type":"payment_intent.succeeded"}'
    valid_sig = sandbox.generate_webhook_signature(payload_bytes)
    assert sandbox.verify_webhook_signature(payload_bytes, valid_sig) is True
    assert sandbox.verify_webhook_signature(payload_bytes, "invalid_signature_xyz") is False


def test_payment_provider_factory():
    """Verify PaymentProviderFactory vends singleton and named providers."""
    PaymentProviderFactory.reset()
    p1 = PaymentProviderFactory.get_provider("sandbox")
    p2 = PaymentProviderFactory.get_provider("sandbox")
    assert p1 is p2
    assert p1.provider_name == "sandbox_gateway"

    mock_p = PaymentProviderFactory.get_provider("mock")
    assert mock_p.provider_name == "mock"
