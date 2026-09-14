"""Protected example endpoints demonstrating RBAC permissions."""

from datetime import datetime, timezone
from typing import Dict, Any
from fastapi import APIRouter, Depends

from backend.app.models.user import User
from backend.app.api.deps import require_admin, require_investigator

router = APIRouter()


@router.get(
    "/admin/system-status",
    summary="Admin System Status",
    description="Endpoint restricted strictly to ADMIN role.",
)
def get_admin_system_status(
    admin: User = Depends(require_admin),
) -> Dict[str, Any]:
    return {
        "access": "granted",
        "role_required": "ADMIN",
        "current_user": admin.email,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "admin_privileges": [
            "user_management",
            "model_management",
            "dataset_management",
            "audit_logs",
        ],
    }


@router.get(
    "/investigations/cases-summary",
    summary="Investigator Cases Summary",
    description="Endpoint accessible by FRAUD_INVESTIGATOR and ADMIN roles.",
)
def get_investigator_cases_summary(
    user: User = Depends(require_investigator),
) -> Dict[str, Any]:
    return {
        "access": "granted",
        "role_permitted": ["ADMIN", "FRAUD_INVESTIGATOR"],
        "current_user": user.email,
        "user_role": user.role,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "investigator_privileges": [
            "view_customers",
            "view_transactions",
            "view_risk_score",
            "view_shap_explanations",
            "manage_investigations",
        ],
    }
