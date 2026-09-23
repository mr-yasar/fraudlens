"""Payment Initiation, Pre-Authorization Gateway, and Webhook Endpoints (Phases 9-27)."""

import json
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Header, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.models.user import User
from backend.app.models.payment_intent import PaymentIntent, WebhookEventRecord, PaymentLifecycleStatus
from backend.app.models.audit_log import AuditLog
from backend.app.api.deps import get_current_user
from backend.app.providers.factory import PaymentProviderFactory
from backend.app.schemas.payment import (
    PaymentInitiateRequest,
    PreAuthDecisionResult,
)
from backend.app.services.behavior_profile_service import BehaviorProfileService
from backend.app.services.risk_decision_orchestrator import RiskDecisionOrchestrator

from backend.app.core.rate_limiter import rate_limit

router = APIRouter()


@router.post(
    "/initiate",
    response_model=PreAuthDecisionResult,
    status_code=status.HTTP_200_OK,
    summary="Evaluate Transaction Risk in Simulation Flow",
    dependencies=[Depends(rate_limit(max_requests=60, window_seconds=60))],
    description=(
        "Evaluates newly submitted transaction request within the application risk engine. "
        "Enforces idempotency, customer behavioral profiling, ML scoring, local SHAP attribution, "
        "explainable rule checks, independent risk scoring, case creation (if REVIEW), and simulated execution (if ALLOW)."
    ),
)
def initiate_payment(
    payload: PaymentInitiateRequest,
    idempotency_key_header: Optional[str] = Header(None, alias="Idempotency-Key"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PreAuthDecisionResult:
    """Evaluate submitted transaction fraud risk and compute multi-factor risk score."""
    try:
        effective_key = idempotency_key_header or payload.idempotency_key
        decision_result = RiskDecisionOrchestrator.evaluate_and_process_payment(
            db=db,
            request=payload,
            current_user=current_user,
            idempotency_key=effective_key,
        )
        return decision_result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Pre-authorization risk check failed: {str(e)}",
        )


@router.get(
    "/customer-profile/{customer_id}",
    summary="Get Customer Behavioral Profile Baseline for Payment Context",
    description="Returns customer historical behavioral metrics (averages, velocity, known devices, locations) used during pre-authorization check.",
)
def get_customer_payment_profile(
    customer_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve historical behavior profile for payment screen context."""
    profile = BehaviorProfileService.get_customer_profile(db=db, customer_id=customer_id)
    return profile.to_dict()


@router.get(
    "/intents/{payment_id}",
    summary="Get Payment Intent Status & Evaluation Details",
)
def get_payment_intent(
    payment_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Fetch payment intent by payment ID."""
    intent = db.query(PaymentIntent).filter(PaymentIntent.payment_id == payment_id).first()
    if not intent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Payment intent '{payment_id}' not found.",
        )
    return {
        "payment_id": intent.payment_id,
        "customer_id": intent.customer_id,
        "amount": intent.amount,
        "currency": intent.currency,
        "merchant_name": intent.merchant_name,
        "merchant_category": intent.merchant_category,
        "lifecycle_status": intent.lifecycle_status,
        "fraud_probability": intent.fraud_probability,
        "risk_score": intent.risk_score,
        "risk_level": intent.risk_level,
        "fraud_decision": intent.fraud_decision,
        "provider_name": intent.provider_name,
        "external_payment_id": intent.external_payment_id,
        "case_id": intent.case_id,
        "created_at": intent.created_at.isoformat() if intent.created_at else None,
        "updated_at": intent.updated_at.isoformat() if intent.updated_at else None,
    }


@router.get(
    "/intents",
    summary="List Recent Payment Intents",
)
def list_payment_intents(
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List recent payment intents with pagination."""
    intents = (
        db.query(PaymentIntent)
        .order_by(PaymentIntent.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return [
        {
            "payment_id": i.payment_id,
            "customer_id": i.customer_id,
            "amount": i.amount,
            "currency": i.currency,
            "merchant_name": i.merchant_name,
            "lifecycle_status": i.lifecycle_status,
            "fraud_decision": i.fraud_decision,
            "risk_score": i.risk_score,
            "risk_level": i.risk_level,
            "external_payment_id": i.external_payment_id,
            "created_at": i.created_at.isoformat() if i.created_at else None,
        }
        for i in intents
    ]


@router.post(
    "/webhook",
    status_code=status.HTTP_200_OK,
    summary="Safe Webhook Ingestion for Payment Lifecycle Events",
    description=(
        "Ingests external payment provider webhook notifications. "
        "Verifies cryptographic signature, rejects duplicates, updates payment intent lifecycle, "
        "and logs an immutable audit event."
    ),
)
async def handle_payment_webhook(
    request: Request,
    signature_header: Optional[str] = Header(None, alias="X-Signature"),
    stripe_signature: Optional[str] = Header(None, alias="Stripe-Signature"),
    db: Session = Depends(get_db),
):
    """Handle incoming asynchronous payment provider events."""
    raw_body = await request.body()
    effective_sig = signature_header or stripe_signature or ""

    adapter = PaymentProviderFactory.get_provider("sandbox_gateway")

    # 1. Cryptographic Signature Verification
    if not adapter.verify_webhook_signature(raw_body, effective_sig):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing webhook signature.",
        )

    # 2. Parse payload
    try:
        payload = json.loads(raw_body.decode("utf-8"))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Malformed JSON in webhook body.",
        )

    event = adapter.parse_webhook_event(payload)

    # 3. Deduplication Check
    existing_record = (
        db.query(WebhookEventRecord)
        .filter(WebhookEventRecord.event_id == event.event_id)
        .first()
    )
    if existing_record:
        return {
            "status": "already_processed",
            "event_id": event.event_id,
            "message": "Duplicate webhook event ignored.",
        }

    # 4. Save Webhook Record
    record = WebhookEventRecord(
        event_id=event.event_id,
        provider_name=event.provider_name,
        event_type=event.event_type,
        external_payment_id=event.external_payment_id,
        internal_payment_id=event.internal_payment_id,
        signature_valid=True,
        processed=True,
        payload_json=json.dumps(payload),
    )
    db.add(record)

    # 5. Synchronize Payment Intent Lifecycle State (if matched)
    if event.internal_payment_id or event.external_payment_id:
        intent = None
        if event.internal_payment_id:
            intent = db.query(PaymentIntent).filter(PaymentIntent.payment_id == event.internal_payment_id).first()
        if not intent and event.external_payment_id:
            intent = db.query(PaymentIntent).filter(PaymentIntent.external_payment_id == event.external_payment_id).first()

        if intent:
            if event.status.value in ("SUCCEEDED", "CAPTURED"):
                intent.lifecycle_status = PaymentLifecycleStatus.SUCCEEDED.value
            elif event.status.value == "FAILED":
                intent.lifecycle_status = PaymentLifecycleStatus.FAILED.value
            elif event.status.value in ("CANCELLED", "REFUNDED"):
                intent.lifecycle_status = PaymentLifecycleStatus.CANCELLED.value

    # 6. Audit Trail Logging
    db.add(AuditLog(
        user_id=None,
        action="WEBHOOK_RECEIVED",
        resource_type="webhook_event",
        resource_id=event.event_id,
        details=json.dumps({
            "event_type": event.event_type,
            "external_id": event.external_payment_id,
            "status": event.status.value,
        }),
    ))
    db.commit()

    return {
        "status": "success",
        "event_id": event.event_id,
        "event_type": event.event_type,
        "payment_synced": bool(event.internal_payment_id or event.external_payment_id),
    }
