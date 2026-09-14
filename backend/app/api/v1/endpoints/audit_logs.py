"""Audit Log Query & Compliance Endpoints (Phase 15)."""

from datetime import datetime
import json
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc, asc, or_
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.models.user import User
from backend.app.models.audit_log import AuditLog
from backend.app.api.deps import require_investigator
from backend.app.schemas.audit_log import AuditLogResponse, AuditLogListResponse

router = APIRouter()


@router.get(
    "",
    response_model=AuditLogListResponse,
    summary="List Compliance Audit Logs",
    description="Retrieves a paginated, filterable audit trail of security, model, case, and system actions. Never exposes credentials or sensitive secrets.",
)
def list_audit_logs(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    action: Optional[str] = Query(None, description="Filter by exact action name"),
    resource_type: Optional[str] = Query(None, description="Filter by resource type"),
    search: Optional[str] = Query(None, description="Search in action, resource_id, or details"),
    start_date: Optional[datetime] = Query(None, description="Earliest event datetime"),
    end_date: Optional[datetime] = Query(None, description="Latest event datetime"),
    sort_order: str = Query("desc", description="Sort direction: desc (newest first) or asc"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_investigator),
) -> AuditLogListResponse:
    """Retrieve filtered, paginated audit logs."""
    query = db.query(AuditLog).outerjoin(User, AuditLog.user_id == User.id)

    if action:
        query = query.filter(AuditLog.action == action.strip())

    if resource_type:
        query = query.filter(AuditLog.resource_type == resource_type.strip())

    if search:
        pattern = f"%{search.strip()}%"
        query = query.filter(
            or_(
                AuditLog.action.ilike(pattern),
                AuditLog.resource_id.ilike(pattern),
                AuditLog.details.ilike(pattern),
            )
        )

    if start_date:
        query = query.filter(AuditLog.created_at >= start_date)

    if end_date:
        query = query.filter(AuditLog.created_at <= end_date)

    order_func = desc if sort_order.lower() == "desc" else asc
    query = query.order_by(order_func(AuditLog.created_at))

    total = query.count()
    offset = (page - 1) * page_size
    logs = query.offset(offset).limit(page_size).all()

    # Pre-fetch user details
    user_ids = {l.user_id for l in logs if l.user_id}
    users_map = {u.id: u for u in db.query(User).filter(User.id.in_(user_ids)).all()} if user_ids else {}

    items = []
    for l in logs:
        u = users_map.get(l.user_id)
        details_obj = None
        if l.details:
            try:
                details_obj = json.loads(l.details)
            except Exception:
                details_obj = {"raw": l.details}

        items.append(
            AuditLogResponse(
                id=l.id,
                user_id=l.user_id,
                user_email=u.email if u else None,
                user_name=u.name if u else None,
                action=l.action,
                resource_type=l.resource_type,
                resource_id=l.resource_id,
                details=details_obj,
                created_at=l.created_at,
            )
        )

    total_pages = (total + page_size - 1) // page_size if page_size > 0 else 1

    return AuditLogListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )
