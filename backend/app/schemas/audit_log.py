"""Pydantic schemas for System Audit Logging (Phase 15)."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class AuditLogResponse(BaseModel):
    """Sanitized representation of compliance audit trail event."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: Optional[int] = None
    user_email: Optional[str] = None
    user_name: Optional[str] = None
    action: str
    resource_type: str
    resource_id: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    created_at: datetime


class AuditLogListResponse(BaseModel):
    """Paginated collection of audit log events."""

    items: List[AuditLogResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
