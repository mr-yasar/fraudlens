"""Unit and integration tests for Safe Webhook Foundation (Phase 27)."""

import json
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.main import app
from backend.app.core.database import Base, get_db
from backend.app.models.customer import Customer
from backend.app.models.payment_intent import PaymentIntent, PaymentLifecycleStatus, WebhookEventRecord
from backend.app.models.audit_log import AuditLog
from backend.app.providers.factory import PaymentProviderFactory


test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="module", autouse=True)
def setup_test_app():
    app.dependency_overrides[get_db] = override_get_db
    Base.metadata.create_all(bind=test_engine)
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_webhook_valid_signature_updates_lifecycle(client):
    """Verify webhook with valid signature updates PaymentIntent lifecycle status to SUCCEEDED."""
    db = TestingSessionLocal()
    c = Customer(customer_id="CUST-WH-01", account_age_days=60)
    db.add(c)
    intent = PaymentIntent(
        payment_id="PAY-WH-001",
        customer_id="CUST-WH-01",
        amount=150.0,
        currency="USD",
        merchant_name="Merchant",
        merchant_category="retail",
        payment_method="card",
        lifecycle_status=PaymentLifecycleStatus.PROCESSING.value,
        fraud_decision="ALLOW",
        risk_score=10,
        risk_level="LOW",
        provider_name="sandbox_gateway",
        external_payment_id="pi_sand_webhook_12345",
    )
    db.add(intent)
    db.commit()
    db.close()

    provider = PaymentProviderFactory.get_provider("sandbox_gateway")

    payload_dict = {
        "id": "evt_sandbox_test_success_999",
        "type": "payment_intent.succeeded",
        "data": {
            "object": {
                "id": "pi_sand_webhook_12345",
                "status": "succeeded",
                "amount": 150.0,
                "currency": "USD",
                "metadata": {"internal_payment_id": "PAY-WH-001"},
            }
        }
    }
    payload_bytes = json.dumps(payload_dict).encode("utf-8")
    sig = provider.generate_webhook_signature(payload_bytes)

    resp = client.post(
        "/api/v1/payment/webhook",
        content=payload_bytes,
        headers={"X-Signature": sig, "Content-Type": "application/json"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    assert data["payment_synced"] is True

    # Verify PaymentIntent in DB updated to SUCCEEDED
    db2 = TestingSessionLocal()
    updated_intent = db2.query(PaymentIntent).filter(PaymentIntent.payment_id == "PAY-WH-001").first()
    assert updated_intent.lifecycle_status == PaymentLifecycleStatus.SUCCEEDED.value
    db2.close()


def test_webhook_invalid_signature_rejected(client):
    """Verify webhook with invalid signature is rejected with 401."""
    payload_bytes = b'{"id":"evt_fake","type":"payment_intent.succeeded"}'
    resp = client.post(
        "/api/v1/payment/webhook",
        content=payload_bytes,
        headers={"X-Signature": "invalid_sig_abc", "Content-Type": "application/json"},
    )
    assert resp.status_code == 401
    assert "Invalid or missing webhook signature" in resp.json()["detail"]


def test_webhook_duplicate_deduplication(client):
    """Verify second delivery of duplicate webhook event is safely acknowledged without double processing."""
    provider = PaymentProviderFactory.get_provider("sandbox_gateway")
    payload_dict = {
        "id": "evt_sandbox_duplicate_test_001",
        "type": "payment_intent.succeeded",
        "data": {
            "object": {
                "id": "pi_sand_dup_123",
                "status": "succeeded",
                "amount": 50.0,
                "currency": "USD",
            }
        }
    }
    payload_bytes = json.dumps(payload_dict).encode("utf-8")
    sig = provider.generate_webhook_signature(payload_bytes)

    # First delivery
    resp1 = client.post("/api/v1/payment/webhook", content=payload_bytes, headers={"X-Signature": sig})
    assert resp1.status_code == 200
    assert resp1.json()["status"] == "success"

    # Duplicate delivery
    resp2 = client.post("/api/v1/payment/webhook", content=payload_bytes, headers={"X-Signature": sig})
    assert resp2.status_code == 200
    assert resp2.json()["status"] == "already_processed"
