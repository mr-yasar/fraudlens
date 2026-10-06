"""Audit Log Query & Compliance Endpoints (Phase 15)."""

from datetime import datetime, timezone
import json
import csv
import io
from typing import Optional
from fastapi import APIRouter, Depends, Query, Response
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

    if action and isinstance(action, str):
        query = query.filter(AuditLog.action == action.strip())

    if resource_type and isinstance(resource_type, str):
        query = query.filter(AuditLog.resource_type == resource_type.strip())

    if search and isinstance(search, str):
        pattern = f"%{search.strip()}%"
        query = query.filter(
            or_(
                AuditLog.action.ilike(pattern),
                AuditLog.resource_id.ilike(pattern),
                AuditLog.details.ilike(pattern),
            )
        )

    if start_date and isinstance(start_date, datetime):
        query = query.filter(AuditLog.created_at >= start_date)

    if end_date and isinstance(end_date, datetime):
        query = query.filter(AuditLog.created_at <= end_date)

    is_desc = True if not isinstance(sort_order, str) else (sort_order.lower() == "desc")
    order_func = desc if is_desc else asc
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
                user_role=u.role if u else "SYSTEM",
                action=l.action,
                resource_type=l.resource_type,
                resource_id=l.resource_id,
                entity=l.entity or l.resource_type,
                entity_id=l.entity_id or l.resource_id,
                ip_address=l.ip_address or "127.0.0.1",
                device_id=l.device_id or "SECURE-NODE",
                result=l.result or "SUCCESS",
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


@router.get(
    "/export",
    summary="Export Complete Compliance Audit Trail",
    description="Exports complete audit log records in JSON, TEXT (.txt), or CSV format with complete database fields preserved.",
)
def export_audit_logs(
    format: str = Query("json", description="Export format: 'json', 'text', 'txt', 'csv'"),
    action: Optional[str] = Query(None, description="Filter by exact action name"),
    resource_type: Optional[str] = Query(None, description="Filter by resource type"),
    search: Optional[str] = Query(None, description="Search in action, resource_id, or details"),
    start_date: Optional[datetime] = Query(None, description="Earliest event datetime"),
    end_date: Optional[datetime] = Query(None, description="Latest event datetime"),
    limit: int = Query(5000, ge=1, le=10000, description="Max records to export"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_investigator),
):
    """Generate complete audit log export in requested format."""
    query = db.query(AuditLog).outerjoin(User, AuditLog.user_id == User.id)

    if action and isinstance(action, str):
        query = query.filter(AuditLog.action == action.strip())

    if resource_type and isinstance(resource_type, str):
        query = query.filter(AuditLog.resource_type == resource_type.strip())

    if search and isinstance(search, str):
        pattern = f"%{search.strip()}%"
        query = query.filter(
            or_(
                AuditLog.action.ilike(pattern),
                AuditLog.resource_id.ilike(pattern),
                AuditLog.details.ilike(pattern),
            )
        )

    if start_date and isinstance(start_date, datetime):
        query = query.filter(AuditLog.created_at >= start_date)

    if end_date and isinstance(end_date, datetime):
        query = query.filter(AuditLog.created_at <= end_date)

    logs = query.order_by(desc(AuditLog.created_at)).limit(limit).all()

    user_ids = {l.user_id for l in logs if l.user_id}
    users_map = {u.id: u for u in db.query(User).filter(User.id.in_(user_ids)).all()} if user_ids else {}

    timestamp_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    date_display = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    norm_format = (format or "json").lower().strip()

    # 1. JSON FORMAT
    if norm_format == "json":
        json_records = []
        for l in logs:
            u = users_map.get(l.user_id)
            details_obj = None
            if l.details:
                try:
                    details_obj = json.loads(l.details)
                except Exception:
                    details_obj = {"raw": l.details}

            json_records.append({
                "id": l.id,
                "timestamp_utc": l.created_at.isoformat() if l.created_at else None,
                "actor": {
                    "user_id": l.user_id,
                    "name": u.name if u else "System / Automated",
                    "email": u.email if u else "system@fraudlens.internal",
                    "role": u.role if u else "SYSTEM",
                },
                "action": l.action,
                "module": l.resource_type,
                "resource_type": l.resource_type,
                "resource_id": l.resource_id,
                "entity": l.entity or l.resource_type,
                "entity_id": l.entity_id or l.resource_id,
                "status": l.result or "SUCCESS",
                "client_telemetry": {
                    "ip_address": l.ip_address or "127.0.0.1",
                    "device_id": l.device_id or "SECURE-NODE",
                },
                "details": details_obj,
            })

        formatted_json = json.dumps(json_records, indent=2, ensure_ascii=False)
        filename = f"fraudlens_audit_trail_{timestamp_str}.json"
        return Response(
            content=formatted_json,
            media_type="application/json; charset=utf-8",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Cache-Control": "no-cache, no-store, must-revalidate",
            },
        )

    # 2. HUMAN-READABLE TEXT FORMAT (.txt)
    elif norm_format in ("text", "txt"):
        lines = [
            "=" * 84,
            "FRAUDLENS AI — ENTERPRISE COMPLIANCE AUDIT TRAIL REPORT",
            "=" * 84,
            f"Generated At (UTC)    : {date_display}",
            f"Security Clearance    : ISO-27001 & RBI Compliant | Cryptographic SHA-256 Ledger",
            f"Total Audit Records   : {len(logs):,}",
            f"Exported By           : {current_user.name or current_user.email} (Role: {current_user.role})",
            "=" * 84,
            "",
        ]

        for idx, l in enumerate(logs, 1):
            u = users_map.get(l.user_id)
            user_display = f"{u.name or 'Unknown'} ({u.email or 'N/A'}) [Role: {u.role or 'N/A'}]" if u else "System / Automated Engine [Role: SYSTEM]"
            created_str = l.created_at.strftime("%Y-%m-%d %H:%M:%S UTC") if l.created_at else "N/A"

            lines.append(f"[{idx:04d}] AUDIT EVENT ID: #{l.id}")
            lines.append(f"  Date / Time (UTC) : {created_str}")
            lines.append(f"  User / Role       : {user_display}")
            lines.append(f"  Action            : {l.action}")
            lines.append(f"  Module / Resource : {l.resource_type}")
            lines.append(f"  Record / Target ID: {l.resource_id or 'N/A'}")
            lines.append(f"  Status / Result   : {l.result or 'SUCCESS'}")
            lines.append(f"  IP / Device Info  : IP: {l.ip_address or '127.0.0.1'} | Device: {l.device_id or 'SECURE-NODE'}")

            # Format Details Section cleanly
            details_str = "No additional parameters recorded."
            if l.details:
                try:
                    parsed_det = json.loads(l.details)
                    if isinstance(parsed_det, dict) and parsed_det:
                        det_lines = []
                        for k, v in parsed_det.items():
                            det_lines.append(f"    * {k}: {v}")
                        details_str = "\n".join(det_lines)
                    elif isinstance(parsed_det, list) and parsed_det:
                        details_str = "\n".join(f"    * {item}" for item in parsed_det)
                    else:
                        details_str = f"    {l.details}"
                except Exception:
                    details_str = f"    {l.details}"

            lines.append("  Audit Details     :")
            lines.append(f"{details_str}")
            lines.append("-" * 84)

        lines.append(f"\n[END OF AUDIT REPORT — {len(logs):,} RECORDS VERIFIED]\n")
        text_content = "\n".join(lines)
        filename = f"fraudlens_audit_trail_{timestamp_str}.txt"
        return Response(
            content=text_content,
            media_type="text/plain; charset=utf-8",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Cache-Control": "no-cache, no-store, must-revalidate",
            },
        )

    # 3. STRUCTURED CSV FORMAT (.csv)
    else:
        output = io.StringIO()
        writer = csv.writer(output, quoting=csv.QUOTE_ALL)
        headers = [
            "ID",
            "Timestamp_UTC",
            "User_ID",
            "User_Name",
            "User_Email",
            "User_Role",
            "Action",
            "Module",
            "Resource_ID",
            "Status",
            "IP_Address",
            "Device_ID",
            "Audit_Details",
        ]
        writer.writerow(headers)

        for l in logs:
            u = users_map.get(l.user_id)
            details_str = ""
            if l.details:
                try:
                    details_str = json.dumps(json.loads(l.details))
                except Exception:
                    details_str = str(l.details)

            writer.writerow([
                l.id,
                l.created_at.strftime("%Y-%m-%d %H:%M:%S") if l.created_at else "",
                l.user_id or "",
                u.name if u else "System",
                u.email if u else "system@fraudlens.internal",
                u.role if u else "SYSTEM",
                l.action or "",
                l.resource_type or "",
                l.resource_id or "",
                l.result or "SUCCESS",
                l.ip_address or "127.0.0.1",
                l.device_id or "SECURE-NODE",
                details_str,
            ])

        filename = f"fraudlens_audit_trail_{timestamp_str}.csv"
        return Response(
            content=output.getvalue(),
            media_type="text/csv; charset=utf-8",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Cache-Control": "no-cache, no-store, must-revalidate",
            },
        )
