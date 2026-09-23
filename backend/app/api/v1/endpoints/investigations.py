"""Fraud Investigation & Case Management Endpoints (Phase 13)."""

from datetime import datetime
import json
import uuid
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc, asc, or_
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.models.user import User
from backend.app.models.transaction import Transaction
from backend.app.models.investigation import Investigation
from backend.app.models.shap_explanation import ShapExplanation
from backend.app.models.audit_log import AuditLog
from backend.app.models.payment_intent import PaymentIntent, PaymentLifecycleStatus
from backend.app.schemas.user import UserRole
from backend.app.api.deps import require_investigator
from backend.app.schemas.investigation import (
    InvestigationStatus,
    InvestigationDecision,
    InvestigationCreateInput,
    InvestigationUpdateInput,
    InvestigationSummaryResponse,
    InvestigationDetailResponse,
    InvestigationListResponse,
)

router = APIRouter()


@router.post(
    "",
    response_model=InvestigationDetailResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Fraud Investigation Case",
    description="Opens a new investigation case for a suspicious transaction, links investigator, prevents duplicate active cases, and records an audit log.",
)
def create_investigation(
    payload: InvestigationCreateInput,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_investigator),
) -> InvestigationDetailResponse:
    """Open a new investigation case for an existing transaction."""
    # 1. Verify target transaction exists
    tx = db.query(Transaction).filter(Transaction.transaction_id == payload.transaction_id.strip()).first()
    if not tx:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transaction with ID '{payload.transaction_id}' not found.",
        )

    # 2. Prevent duplicate active investigations for same transaction
    active_case = (
        db.query(Investigation)
        .filter(
            Investigation.transaction_id == tx.transaction_id,
            Investigation.status.in_(["OPEN", "UNDER_REVIEW"]),
        )
        .first()
    )
    if active_case:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"An active investigation case ('{active_case.case_id}') already exists for transaction '{tx.transaction_id}'.",
        )

    # 3. Determine investigator assignment
    assigned_id = payload.investigator_id
    if assigned_id is None:
        if current_user.role == UserRole.FRAUD_INVESTIGATOR.value:
            assigned_id = current_user.id
        elif current_user.role == UserRole.ADMIN.value:
            assigned_id = current_user.id
    else:
        # Verify specified investigator exists if provided
        assigned_user = db.query(User).filter(User.id == assigned_id).first()
        if not assigned_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Investigator with User ID '{assigned_id}' not found.",
            )

    # 4. Generate unique Case ID
    case_id = f"CASE-{uuid.uuid4().hex[:8].upper()}"

    # 5. Create Investigation Case
    investigation = Investigation(
        case_id=case_id,
        transaction_id=tx.transaction_id,
        investigator_id=assigned_id,
        status=InvestigationStatus.OPEN.value,
        decision=None,
        notes=payload.notes.strip() if payload.notes else None,
    )
    db.add(investigation)
    db.flush()

    # 6. Record Audit Event
    audit_entry = AuditLog(
        user_id=current_user.id,
        action="INVESTIGATION_CASE_CREATED",
        resource_type="investigation",
        resource_id=case_id,
        details=json.dumps({
            "transaction_id": tx.transaction_id,
            "assigned_to": assigned_id,
            "status": InvestigationStatus.OPEN.value,
            "initial_notes": payload.notes,
        }),
    )
    db.add(audit_entry)
    db.commit()
    db.refresh(investigation)

    # Fetch investigator info if assigned
    inv_user = db.query(User).filter(User.id == investigation.investigator_id).first() if investigation.investigator_id else None

    # Fetch top SHAP explanations for transaction
    shap_recs = db.query(ShapExplanation).filter(ShapExplanation.transaction_id == tx.transaction_id).all()
    shap_list = [{"feature_name": s.feature_name, "shap_value": s.shap_value, "impact": s.impact} for s in shap_recs]

    return InvestigationDetailResponse(
        id=investigation.id,
        case_id=investigation.case_id,
        transaction_id=investigation.transaction_id,
        investigator_id=investigation.investigator_id,
        investigator_name=inv_user.name if inv_user else None,
        investigator_email=inv_user.email if inv_user else None,
        status=investigation.status,
        decision=investigation.decision,
        notes=investigation.notes,
        created_at=investigation.created_at,
        updated_at=investigation.updated_at,
        amount=float(tx.amount) if tx.amount else None,
        risk_score=tx.risk_score,
        risk_level=tx.risk_level,
        prediction="FRAUD" if tx.prediction == 1 else "GENUINE",
        customer_id=tx.customer_id,
        fraud_probability=tx.fraud_probability,
        top_shap_factors=shap_list,
        transaction_details={
            "merchant_category": tx.merchant_category,
            "transaction_country": tx.transaction_country,
            "device_type": tx.device_type,
            "transaction_type": tx.transaction_type,
            "transaction_hour": tx.transaction_hour,
        },
    )


@router.get(
    "",
    response_model=InvestigationListResponse,
    summary="List Investigation Cases with Multi-Filter Support",
    description="Retrieves a paginated list of fraud investigation cases with filtering by status, decision, investigator, risk level, and date ranges.",
)
def list_investigations(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search by case ID or transaction ID"),
    status: Optional[str] = Query(None, description="Filter by status: OPEN, UNDER_REVIEW, RESOLVED"),
    decision: Optional[str] = Query(None, description="Filter by decision: CONFIRMED_FRAUD, GENUINE"),
    investigator_id: Optional[int] = Query(None, description="Filter by investigator user ID"),
    risk_level: Optional[str] = Query(None, description="Filter by transaction risk level: LOW, MEDIUM, HIGH"),
    start_date: Optional[datetime] = Query(None, description="Earliest case created_at datetime"),
    end_date: Optional[datetime] = Query(None, description="Latest case created_at datetime"),
    sort_by: str = Query("created_at", description="Sort field: created_at, updated_at, case_id, status"),
    sort_order: str = Query("desc", description="Sort order: asc or desc"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_investigator),
) -> InvestigationListResponse:
    """List investigation cases with comprehensive search and filtering."""
    query = db.query(Investigation).join(Transaction, Investigation.transaction_id == Transaction.transaction_id)

    # Search filter
    if search:
        search_pattern = f"%{search.strip()}%"
        query = query.filter(
            or_(
                Investigation.case_id.ilike(search_pattern),
                Investigation.transaction_id.ilike(search_pattern),
            )
        )

    # Status filter
    if status:
        query = query.filter(Investigation.status == status.upper().strip())

    # Decision filter
    if decision:
        query = query.filter(Investigation.decision == decision.upper().strip())

    # Investigator filter
    if investigator_id is not None:
        query = query.filter(Investigation.investigator_id == investigator_id)

    # Risk level filter
    if risk_level:
        query = query.filter(Transaction.risk_level == risk_level.upper().strip())

    # Date filters
    if start_date is not None:
        query = query.filter(Investigation.created_at >= start_date)
    if end_date is not None:
        query = query.filter(Investigation.created_at <= end_date)

    # Sorting
    sort_col_map = {
        "created_at": Investigation.created_at,
        "updated_at": Investigation.updated_at,
        "case_id": Investigation.case_id,
        "status": Investigation.status,
    }
    sort_col = sort_col_map.get(sort_by, Investigation.created_at)
    order_func = desc if sort_order.lower() == "desc" else asc
    query = query.order_by(order_func(sort_col))

    total = query.count()
    offset = (page - 1) * page_size
    investigations = query.offset(offset).limit(page_size).all()

    # Pre-fetch investigator users for fast enrichment
    inv_user_ids = {inv.investigator_id for inv in investigations if inv.investigator_id}
    users_map = {u.id: u for u in db.query(User).filter(User.id.in_(inv_user_ids)).all()} if inv_user_ids else {}

    # Pre-fetch transactions
    tx_ids = {inv.transaction_id for inv in investigations}
    tx_map = {t.transaction_id: t for t in db.query(Transaction).filter(Transaction.transaction_id.in_(tx_ids)).all()} if tx_ids else {}

    items = []
    for inv in investigations:
        t = tx_map.get(inv.transaction_id)
        u = users_map.get(inv.investigator_id)
        items.append(
            InvestigationSummaryResponse(
                id=inv.id,
                case_id=inv.case_id,
                transaction_id=inv.transaction_id,
                investigator_id=inv.investigator_id,
                investigator_name=u.name if u else None,
                investigator_email=u.email if u else None,
                status=inv.status,
                decision=inv.decision,
                notes=inv.notes,
                created_at=inv.created_at,
                updated_at=inv.updated_at,
                amount=float(t.amount) if t and t.amount else None,
                risk_score=t.risk_score if t else None,
                risk_level=t.risk_level if t else None,
                prediction="FRAUD" if t and t.prediction == 1 else "GENUINE" if t else None,
            )
        )

    total_pages = (total + page_size - 1) // page_size if page_size > 0 else 1

    return InvestigationListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get(
    "/{case_id}",
    response_model=InvestigationDetailResponse,
    summary="Get Investigation Case Details by Case ID",
    description="Retrieves full investigation case details including linked transaction details, customer ID, risk score, fraud probability, and SHAP explanations.",
)
def get_investigation_detail(
    case_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_investigator),
) -> InvestigationDetailResponse:
    """Retrieve full investigation case details."""
    investigation = db.query(Investigation).filter(Investigation.case_id == case_id.strip()).first()
    if not investigation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Investigation case with ID '{case_id}' not found.",
        )

    # Load linked transaction
    tx = db.query(Transaction).filter(Transaction.transaction_id == investigation.transaction_id).first()
    inv_user = db.query(User).filter(User.id == investigation.investigator_id).first() if investigation.investigator_id else None

    # Load SHAP explanations
    shap_recs = db.query(ShapExplanation).filter(ShapExplanation.transaction_id == investigation.transaction_id).all()
    shap_list = [{"feature_name": s.feature_name, "shap_value": s.shap_value, "impact": s.impact} for s in shap_recs]

    return InvestigationDetailResponse(
        id=investigation.id,
        case_id=investigation.case_id,
        transaction_id=investigation.transaction_id,
        investigator_id=investigation.investigator_id,
        investigator_name=inv_user.name if inv_user else None,
        investigator_email=inv_user.email if inv_user else None,
        status=investigation.status,
        decision=investigation.decision,
        notes=investigation.notes,
        created_at=investigation.created_at,
        updated_at=investigation.updated_at,
        amount=float(tx.amount) if tx and tx.amount else None,
        risk_score=tx.risk_score if tx else None,
        risk_level=tx.risk_level if tx else None,
        prediction="FRAUD" if tx and tx.prediction == 1 else "GENUINE" if tx else None,
        customer_id=tx.customer_id if tx else None,
        fraud_probability=tx.fraud_probability if tx else None,
        top_shap_factors=shap_list,
        transaction_details={
            "merchant_category": tx.merchant_category if tx else None,
            "transaction_country": tx.transaction_country if tx else None,
            "device_type": tx.device_type if tx else None,
            "transaction_type": tx.transaction_type if tx else None,
            "transaction_hour": tx.transaction_hour if tx else None,
        } if tx else None,
    )


@router.put(
    "/{case_id}",
    response_model=InvestigationDetailResponse,
    include_in_schema=False,
)
@router.patch(
    "/{case_id}",
    response_model=InvestigationDetailResponse,
    summary="Update Investigation Case Status, Decision, or Assignment",
    description="Updates case workflow state with validation. When setting status to RESOLVED, a valid decision and notes are strictly enforced.",
)
def update_investigation(
    case_id: str,
    payload: InvestigationUpdateInput,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_investigator),
) -> InvestigationDetailResponse:
    """Update investigation case status, decision, notes, or investigator assignment."""
    investigation = db.query(Investigation).filter(Investigation.case_id == case_id.strip()).first()
    if not investigation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Investigation case with ID '{case_id}' not found.",
        )

    # Check permission for investigator role (Admin can update any case; investigator can update assigned or open cases)
    if current_user.role == UserRole.FRAUD_INVESTIGATOR.value:
        if investigation.investigator_id is not None and investigation.investigator_id != current_user.id:
            # If case is assigned to another investigator, non-admin cannot arbitrarily overwrite
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not authorized to modify an investigation case assigned to another investigator.",
            )

    audit_actions = []

    # 1. Update status and validate transitions
    target_status = payload.status or investigation.status
    target_decision = payload.decision or investigation.decision
    target_notes = payload.notes if payload.notes is not None else investigation.notes

    if target_status == InvestigationStatus.RESOLVED.value:
        # Require a valid decision when resolving
        if not target_decision:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A valid decision ('CONFIRMED_FRAUD' or 'GENUINE') is required to resolve an investigation case.",
            )
        # Require notes when resolving
        if not target_notes or not target_notes.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Investigator notes are required when resolving an investigation case.",
            )

    if payload.status is not None and payload.status != investigation.status:
        audit_actions.append(f"Status changed from {investigation.status} to {payload.status}")
        investigation.status = payload.status

    # 2. Update decision
    if payload.decision is not None and payload.decision != investigation.decision:
        audit_actions.append(f"Decision updated to {payload.decision}")
        investigation.decision = payload.decision

    # 3. Update notes
    if payload.notes is not None:
        investigation.notes = payload.notes.strip()

    # 4. Update investigator assignment
    if payload.investigator_id is not None and payload.investigator_id != investigation.investigator_id:
        if current_user.role != UserRole.ADMIN.value and payload.investigator_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only administrators can reassign cases to other investigators.",
            )
        assigned_user = db.query(User).filter(User.id == payload.investigator_id).first()
        if not assigned_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Investigator with User ID '{payload.investigator_id}' not found.",
            )
        audit_actions.append(f"Investigator assigned to User ID {payload.investigator_id}")
        investigation.investigator_id = payload.investigator_id

    # 5. Record AuditLog if any changes occurred
    if audit_actions or payload.notes is not None:
        action_name = "INVESTIGATION_CASE_RESOLVED" if investigation.status == InvestigationStatus.RESOLVED.value else "INVESTIGATION_CASE_UPDATED"
        audit_entry = AuditLog(
            user_id=current_user.id,
            action=action_name,
            resource_type="investigation",
            resource_id=case_id,
            details=json.dumps({
                "changes": audit_actions,
                "status": investigation.status,
                "decision": investigation.decision,
                "notes": investigation.notes,
            }),
        )
        # Sync linked PaymentIntent lifecycle status if present
        linked_payment = db.query(PaymentIntent).filter(PaymentIntent.payment_id == investigation.transaction_id).first()
        if linked_payment:
            if investigation.decision == "CONFIRMED_FRAUD":
                linked_payment.lifecycle_status = PaymentLifecycleStatus.BLOCKED.value
            elif investigation.decision == "GENUINE":
                linked_payment.lifecycle_status = PaymentLifecycleStatus.APPROVED.value
            elif investigation.status == "UNDER_REVIEW":
                linked_payment.lifecycle_status = PaymentLifecycleStatus.REVIEW_REQUIRED.value

        db.commit()
        db.refresh(investigation)

    tx = db.query(Transaction).filter(Transaction.transaction_id == investigation.transaction_id).first()
    inv_user = db.query(User).filter(User.id == investigation.investigator_id).first() if investigation.investigator_id else None
    shap_recs = db.query(ShapExplanation).filter(ShapExplanation.transaction_id == investigation.transaction_id).all()
    shap_list = [{"feature_name": s.feature_name, "shap_value": s.shap_value, "impact": s.impact} for s in shap_recs]

    return InvestigationDetailResponse(
        id=investigation.id,
        case_id=investigation.case_id,
        transaction_id=investigation.transaction_id,
        investigator_id=investigation.investigator_id,
        investigator_name=inv_user.name if inv_user else None,
        investigator_email=inv_user.email if inv_user else None,
        status=investigation.status,
        decision=investigation.decision,
        notes=investigation.notes,
        created_at=investigation.created_at,
        updated_at=investigation.updated_at,
        amount=float(tx.amount) if tx and tx.amount else None,
        risk_score=tx.risk_score if tx else None,
        risk_level=tx.risk_level if tx else None,
        prediction="FRAUD" if tx and tx.prediction == 1 else "GENUINE" if tx else None,
        customer_id=tx.customer_id if tx else None,
        fraud_probability=tx.fraud_probability if tx else None,
        top_shap_factors=shap_list,
        transaction_details={
            "merchant_category": tx.merchant_category if tx else None,
            "transaction_country": tx.transaction_country if tx else None,
            "device_type": tx.device_type if tx else None,
            "transaction_type": tx.transaction_type if tx else None,
            "transaction_hour": tx.transaction_hour if tx else None,
        } if tx else None,
    )
