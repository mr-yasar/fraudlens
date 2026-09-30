"""Assistant Identity & Authorization Service (Phases 4-6).

Provides:
- Phase 4: Normalized server-side identity context derived strictly from JWT
- Phase 5: Permission & scope enforcement completely independent of the LLM
- Phase 6: Customer row-level data isolation & immutable security audit logging
"""

import re
import json
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy.orm import Session

from backend.app.models.user import User
from backend.app.models.transaction import Transaction
from backend.app.models.audit_log import AuditLog
from backend.app.api.deps import get_customer_id_for_user

logger = logging.getLogger("fraudlens.assistant.identity")

# Canonical customer identities in FraudLens
CUSTOMER_CANONICAL_MAP = {
    "monisha": "CUST_MONISHA_001",
    "mohana": "CUST_MOHANA_002",
    "mogana": "CUST_MOHANA_002",
    "sowmiya": "CUST_SOWMIYA_003",
    "soumya": "CUST_SOWMIYA_003",
    "ajay": "CUST_AJAY_004",
}

ROLE_CUSTOMER = "customer"
ROLE_ADMIN = "admin"
ROLE_INVESTIGATOR = "investigator"
ROLE_GUEST = "guest"


@dataclass
class AssistantIdentityContext:
    user_id: int
    email: str
    name: str
    role: str                       # 'customer' | 'investigator' | 'admin' | 'guest'
    customer_id: Optional[str]      # Canonical ID (e.g. 'CUST_MONISHA_001')
    is_admin: bool
    is_investigator: bool
    is_customer: bool
    authorized_scope: str          # 'OWN_CUSTOMER_DATA' | 'FORENSIC_INVESTIGATION' | 'GLOBAL_SYSTEM' | 'PUBLIC_GUEST'
    session_id: Optional[str] = None
    account_number_masked: str = "•••• 4821"

    def can_access_customer(self, target_customer_id: str) -> bool:
        """Verify whether this identity is authorized to access target customer data."""
        if self.is_admin or self.is_investigator:
            return True
        if not self.is_customer or not self.customer_id:
            return False
        return self.customer_id.upper().strip() == target_customer_id.upper().strip()


# Alias for backward compatibility
AssistantIdentity = AssistantIdentityContext


def resolve_assistant_identity(
    user: Optional[User],
    db: Session,
    session_id: Optional[str] = None,
) -> AssistantIdentityContext:
    """Phase 4: Build normalized, trusted server-side identity context from authenticated user."""
    if not user:
        return AssistantIdentityContext(
            user_id=0,
            email="guest@fraudlens.public",
            name="Guest User",
            role="guest",
            customer_id=None,
            is_admin=False,
            is_investigator=False,
            is_customer=False,
            authorized_scope="PUBLIC_GUEST",
            session_id=session_id,
            account_number_masked="•••• 0000",
        )

    user_role_raw = user.role.value if hasattr(user.role, "value") else str(user.role or "")
    role_normalized = user_role_raw.lower().strip()
    user_name = user.name or user.email.split("@")[0]

    is_admin = role_normalized in ("admin", "superadmin", "administrator")
    is_investigator = role_normalized in ("investigator", "fraud_investigator", "analyst", "soc")
    is_customer = not is_admin and not is_investigator

    # Resolve canonical customer ID
    customer_id = get_customer_id_for_user(user, db) if is_customer else None

    # Derive authorized scope
    if is_admin:
        scope = "GLOBAL_SYSTEM"
    elif is_investigator:
        scope = "FORENSIC_INVESTIGATION"
    elif is_customer:
        scope = "OWN_CUSTOMER_DATA"
    else:
        scope = "PUBLIC_GUEST"

    # Masked account identifier based on customer ID
    last_digits = "4821"
    if customer_id == "CUST_MOHANA_002":
        last_digits = "8912"
    elif customer_id == "CUST_SOWMIYA_003":
        last_digits = "3391"
    elif customer_id == "CUST_AJAY_004":
        last_digits = "7104"

    return AssistantIdentityContext(
        user_id=user.id,
        email=user.email,
        name=user_name,
        role=role_normalized,
        customer_id=customer_id,
        is_admin=is_admin,
        is_investigator=is_investigator,
        is_customer=is_customer,
        authorized_scope=scope,
        session_id=session_id,
        account_number_masked=f"•••• {last_digits}",
    )


def detect_cross_user_target(query: str, identity: AssistantIdentityContext) -> Optional[str]:
    """Detect if query mentions another specific customer persona."""
    q_lower = query.lower()
    for name, cid in CUSTOMER_CANONICAL_MAP.items():
        # If user asks about someone other than themselves
        if re.search(rf"\b{name}\b", q_lower):
            if identity.is_customer and identity.customer_id and identity.customer_id.upper() != cid.upper():
                return cid
    return None


def verify_and_enforce_isolation(
    identity: AssistantIdentityContext,
    user_prompt: str,
    db: Session,
    requested_tx_id: Optional[str] = None,
) -> Tuple[bool, Optional[str]]:
    """Phases 5 & 6: Validate request boundaries before any data enters LLM context.
    
    Returns:
        (is_allowed: bool, refusal_message: Optional[str])
    """
    # Admins and investigators have authorized broad scope
    if identity.is_admin or identity.is_investigator:
        return True, None

    # 1. Cross-Customer Persona Inspection Detection
    cross_target = detect_cross_user_target(user_prompt, identity)
    if cross_target:
        logger.warning(
            "Security Event: Customer %s attempted cross-user query target %s",
            identity.email,
            cross_target,
        )
        _log_security_audit_event(
            db=db,
            user_id=identity.user_id,
            action="UNAUTHORIZED_CROSS_USER_ATTEMPT",
            details={"email": identity.email, "target": cross_target, "query_snippet": user_prompt[:80]},
        )
        return (
            False,
            "I can't provide another user's account information. I can help you review your own transactions or security activity instead.",
        )

    # 2. Foreign Transaction ID Ownership Check
    target_tx = requested_tx_id
    if not target_tx:
        tx_match = re.search(r"\b(TXN[_-]?[A-Za-z0-9_-]+)\b", user_prompt, re.IGNORECASE)
        if tx_match:
            target_tx = tx_match.group(1).upper()

    if target_tx and identity.is_customer:
        tx_record = db.query(Transaction).filter(Transaction.transaction_id == target_tx).first()
        if tx_record:
            is_owner = False
            if identity.customer_id and tx_record.customer_id:
                is_owner = identity.customer_id.upper().strip() == tx_record.customer_id.upper().strip()
            if not is_owner and tx_record.customer and tx_record.customer.email:
                is_owner = identity.email.lower() == tx_record.customer.email.lower()

            if not is_owner:
                logger.warning(
                    "Security Event: Customer %s attempted access to foreign tx %s",
                    identity.email,
                    target_tx,
                )
                _log_security_audit_event(
                    db=db,
                    user_id=identity.user_id,
                    action="UNAUTHORIZED_FOREIGN_TRANSACTION_ATTEMPT",
                    details={"email": identity.email, "tx_id": target_tx},
                )
                return (
                    False,
                    "I can't provide information on transactions belonging to another account. I can help you review your own transactions instead.",
                )

    # 3. Privileged Admin Data / Audit Log Access Attempt
    q_lower = user_prompt.lower()
    privileged_patterns = [
        r"\b(show|get|dump|list)\b.*?\b(all users|other users|audit logs|admin database|system secrets|raw sql)\b",
        r"\b(admin password|system prompt|internal prompt)\b",
    ]
    for pattern in privileged_patterns:
        if re.search(pattern, q_lower):
            logger.warning(
                "Security Event: Customer %s attempted privileged query %s",
                identity.email,
                pattern,
            )
            _log_security_audit_event(
                db=db,
                user_id=identity.user_id,
                action="UNAUTHORIZED_PRIVILEGED_QUERY_ATTEMPT",
                details={"email": identity.email, "pattern": pattern},
            )
            return (
                False,
                "You don't have permission to access that information. I can help you with your account security or personal transactions.",
            )

    return True, None


def _log_security_audit_event(
    db: Session,
    user_id: int,
    action: str,
    details: Dict[str, Any],
) -> None:
    """Log immutable security audit event into database."""
    try:
        audit = AuditLog(
            user_id=user_id if user_id > 0 else None,
            action=action,
            resource_type="ai_assistant_boundary",
            resource_id="assistant_guard",
            details=json.dumps(details),
        )
        db.add(audit)
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error("Failed to write assistant audit log: %s", e)
