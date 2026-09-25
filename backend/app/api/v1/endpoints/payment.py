"""Payment Initiation, Pre-Authorization Gateway, Approvals, Wallet, and Webhook Endpoints."""

import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Header, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.models.user import User
from backend.app.models.customer import Customer
from backend.app.models.payment_intent import PaymentIntent, WebhookEventRecord, PaymentLifecycleStatus
from backend.app.models.beneficiary import Beneficiary
from backend.app.models.device import CustomerDevice
from backend.app.models.approval import TransactionApproval, ApprovalStatus
from backend.app.models.audit_log import AuditLog
from backend.app.api.deps import get_current_user
from backend.app.providers.factory import PaymentProviderFactory
from backend.app.schemas.payment import (
    PaymentInitiateRequest,
    PreAuthDecisionResult,
    ApprovalActionRequest,
    ApprovalDetailResponse,
    BeneficiaryResponse,
    BeneficiaryCreateRequest,
    CustomerWalletResponse,
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
        "Enforces wallet balance sufficiency, customer behavioral profiling, ML scoring, local SHAP attribution, "
        "explainable rule checks, independent risk scoring, step-up verification challenge creation (if REVIEW), "
        "and simulated execution & balance deduction (if ALLOW)."
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
    "/wallet/{customer_id}",
    response_model=CustomerWalletResponse,
    summary="Get Customer Wallet, Balance, and Known Recipients",
    description="Returns simulated wallet balance, known beneficiaries, and device history for the transaction simulation screen.",
)
def get_customer_wallet(
    customer_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CustomerWalletResponse:
    """Retrieve simulated wallet balance and known recipients for payment screen."""
    customer = db.query(Customer).filter(Customer.customer_id == customer_id).first()
    if not customer:
        customer = Customer(
            customer_id=customer_id,
            account_age_days=30,
            simulated_balance=50000.0,
            currency="USD",
        )
        db.add(customer)
        db.commit()
        db.refresh(customer)

    profile = BehaviorProfileService.get_customer_profile(db=db, customer_id=customer_id)

    beneficiaries = (
        db.query(Beneficiary)
        .filter(Beneficiary.customer_id == customer_id)
        .order_by(Beneficiary.last_used_at.desc())
        .all()
    )

    bene_dtos = [
        BeneficiaryResponse(
            id=b.id,
            customer_id=b.customer_id,
            beneficiary_name=b.beneficiary_name,
            beneficiary_account=b.beneficiary_account,
            category=b.category,
            trust_score=b.trust_score,
            is_trusted=b.is_trusted,
            total_transfers=b.total_transfers,
            last_used_at=b.last_used_at,
        )
        for b in beneficiaries
    ]

    return CustomerWalletResponse(
        customer_id=customer.customer_id,
        simulated_balance=float(customer.simulated_balance or 50000.0),
        currency=customer.currency or "USD",
        account_age_days=profile.account_age_days,
        known_beneficiaries=bene_dtos,
        known_devices=profile.known_devices,
        usual_locations=profile.usual_locations,
        total_transactions=profile.total_transactions,
        historical_avg_amount=profile.historical_avg_amount,
    )


@router.post(
    "/approvals/{approval_id}/action",
    summary="Approve, Reject, or Expire a Step-Up Verification Challenge",
    description="Executes authenticated user authorization or cancellation on a pending suspicious transaction.",
)
def process_approval_action(
    approval_id: str,
    payload: ApprovalActionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Process user step-up approval or rejection decision."""
    return RiskDecisionOrchestrator.process_approval_action(
        db=db,
        approval_id=approval_id,
        action=payload.action,
        current_user=current_user,
        notes=payload.notes,
    )


@router.post(
    "/approvals/{approval_id}/approve",
    summary="Quick-Approve Step-Up Verification Challenge",
)
def quick_approve(
    approval_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Approve pending transaction verification and deduct simulated wallet balance."""
    return RiskDecisionOrchestrator.process_approval_action(
        db=db,
        approval_id=approval_id,
        action="APPROVE",
        current_user=current_user,
    )


@router.post(
    "/approvals/{approval_id}/reject",
    summary="Quick-Reject Step-Up Verification Challenge",
)
def quick_reject(
    approval_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Reject pending transaction verification and permanently block transaction."""
    return RiskDecisionOrchestrator.process_approval_action(
        db=db,
        approval_id=approval_id,
        action="REJECT",
        current_user=current_user,
    )


@router.get(
    "/approvals/pending",
    response_model=List[ApprovalDetailResponse],
    summary="List Pending Transaction Approvals",
)
def list_pending_approvals(
    customer_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[ApprovalDetailResponse]:
    """List unresolved step-up verification challenges."""
    query = db.query(TransactionApproval).filter(TransactionApproval.status == ApprovalStatus.PENDING.value)
    if customer_id:
        query = query.filter(TransactionApproval.customer_id == customer_id)
    
    approvals = query.order_by(TransactionApproval.requested_at.desc()).all()
    now = datetime.now(timezone.utc)

    return [
        ApprovalDetailResponse(
            approval_id=a.approval_id,
            payment_id=a.payment_id,
            transaction_id=a.transaction_id,
            customer_id=a.customer_id,
            status=a.status,
            amount=a.amount,
            currency=a.currency,
            risk_score=a.risk_score,
            risk_level=a.risk_level,
            fraud_probability=a.fraud_probability,
            challenge_type=a.challenge_type,
            notes=a.notes,
            requested_at=a.requested_at,
            responded_at=a.responded_at,
            expires_at=a.expires_at,
            is_expired=(now > (a.expires_at.replace(tzinfo=timezone.utc) if a.expires_at.tzinfo is None else a.expires_at)),
        )
        for a in approvals
    ]


@router.get(
    "/customer-profile/{customer_id}",
    summary="Get Customer Behavioral Profile Baseline for Payment Context",
    description="Returns customer historical behavioral metrics used during pre-authorization check.",
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
    "/beneficiaries/{customer_id}",
    response_model=List[BeneficiaryResponse],
    summary="List Customer Known Beneficiaries",
)
def list_beneficiaries(
    customer_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[BeneficiaryResponse]:
    """Retrieve all saved recipients for a customer."""
    benes = (
        db.query(Beneficiary)
        .filter(Beneficiary.customer_id == customer_id)
        .order_by(Beneficiary.last_used_at.desc())
        .all()
    )
    return [
        BeneficiaryResponse(
            id=b.id,
            customer_id=b.customer_id,
            beneficiary_name=b.beneficiary_name,
            beneficiary_account=b.beneficiary_account,
            category=b.category,
            trust_score=b.trust_score,
            is_trusted=b.is_trusted,
            total_transfers=b.total_transfers,
            last_used_at=b.last_used_at,
        )
        for b in benes
    ]


@router.post(
    "/beneficiaries/{customer_id}",
    response_model=BeneficiaryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a New Trusted Beneficiary",
)
def add_beneficiary(
    customer_id: str,
    payload: BeneficiaryCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BeneficiaryResponse:
    """Manually register a new trusted recipient beneficiary."""
    existing = db.query(Beneficiary).filter(
        Beneficiary.customer_id == customer_id,
        Beneficiary.beneficiary_name == payload.beneficiary_name.strip(),
    ).first()
    if existing:
        return BeneficiaryResponse(
            id=existing.id,
            customer_id=existing.customer_id,
            beneficiary_name=existing.beneficiary_name,
            beneficiary_account=existing.beneficiary_account,
            category=existing.category,
            trust_score=existing.trust_score,
            is_trusted=existing.is_trusted,
            total_transfers=existing.total_transfers,
            last_used_at=existing.last_used_at,
        )

    bene = Beneficiary(
        customer_id=customer_id,
        beneficiary_name=payload.beneficiary_name.strip(),
        beneficiary_account=payload.beneficiary_account,
        category=payload.category,
        is_trusted=True,
    )
    db.add(bene)
    db.commit()
    db.refresh(bene)

    return BeneficiaryResponse(
        id=bene.id,
        customer_id=bene.customer_id,
        beneficiary_name=bene.beneficiary_name,
        beneficiary_account=bene.beneficiary_account,
        category=bene.category,
        trust_score=bene.trust_score,
        is_trusted=bene.is_trusted,
        total_transfers=bene.total_transfers,
        last_used_at=bene.last_used_at,
    )


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
        "beneficiary_name": intent.beneficiary_name,
        "lifecycle_status": intent.lifecycle_status,
        "fraud_probability": intent.fraud_probability,
        "risk_score": intent.risk_score,
        "risk_level": intent.risk_level,
        "fraud_decision": intent.fraud_decision,
        "is_new_beneficiary": intent.is_new_beneficiary,
        "is_new_device": intent.is_new_device,
        "approval_id": intent.approval_id,
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
            "beneficiary_name": i.beneficiary_name,
            "lifecycle_status": i.lifecycle_status,
            "fraud_decision": i.fraud_decision,
            "risk_score": i.risk_score,
            "risk_level": i.risk_level,
            "approval_id": i.approval_id,
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
