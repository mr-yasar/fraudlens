"""Premium User 4 Security Environment API Router.
Strict tenant and user isolation, multi-signal adaptive risk evaluation,
hardware device security, active session controls, cryptographic step-up verification,
explainable security health, and demo test scenarios.
"""

from datetime import datetime, timezone, timedelta
import json
import logging
import secrets
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

logger = logging.getLogger("fraudlens.premium_api")


from backend.app.core.database import get_db
from backend.app.models.user import User
from backend.app.models.customer import Customer
from backend.app.models.device import CustomerDevice
from backend.app.models.session import UserSession
from backend.app.models.transaction import Transaction
from backend.app.models.risk_event import RiskEvent
from backend.app.models.verification_event import VerificationEvent
from backend.app.models.alert import Alert
from backend.app.models.audit_log import AuditLog
from backend.app.models.behavioral_profile import BehavioralProfile
from backend.app.models.beneficiary import Beneficiary
from backend.app.api.deps import get_current_user, get_customer_id_for_user
from backend.app.services.premium_security_service import PremiumSecurityService
from backend.app.services.event_broadcaster import event_broadcaster

router = APIRouter()


# -----------------------------------------------------------------------------
# Pydantic Schemas
# -----------------------------------------------------------------------------
class TransactionEvaluateRequest(BaseModel):
    amount: float = Field(..., gt=0, description="Transfer amount in INR")
    recipient: str = Field(..., min_length=2, description="Beneficiary / recipient name")
    device_id: str = Field(..., description="Hardware device identifier")
    device_name: Optional[str] = Field(None, description="Client device human-readable name")
    location: Optional[str] = Field("Mumbai / Cyber City", description="Originating geographic location")
    transaction_type: Optional[str] = Field("WIRE_TRANSFER", description="Transfer mechanism")
    transaction_hour: Optional[int] = Field(None, description="Simulated transaction hour 0-23")
    currency: Optional[str] = Field("INR", description="Currency denomination")



class VerifyOtpRequest(BaseModel):
    transaction_id: str = Field(..., description="Target transaction ID")
    otp_code: str = Field(..., min_length=6, max_length=6, description="6-digit verification passcode")


class RequestOtpPayload(BaseModel):
    transaction_id: str = Field(..., description="Target transaction ID")


class RunScenarioRequest(BaseModel):
    scenario_id: str = Field(..., description="Identifier of scenario (scenario_a_normal, scenario_b_unusual, scenario_c_high_risk, scenario_d_critical)")


def _enforce_user_isolation(current_user: User, db: Session) -> str:
    """Resolve and enforce isolated customer ID for current authenticated user."""
    customer_id = get_customer_id_for_user(current_user, db)
    if not customer_id:
        customer_id = f"CUST-USER-{current_user.id}"
    return customer_id


# -----------------------------------------------------------------------------
# Endpoints
# -----------------------------------------------------------------------------

@router.get("/dashboard", summary="Get Premium Security Dashboard Overview")
def get_premium_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Returns high-level security overview, health score, active sessions, and recent events."""
    customer_id = _enforce_user_isolation(current_user, db)
    health = PremiumSecurityService.get_security_health(db, current_user, customer_id)

    customer = db.query(Customer).filter(Customer.customer_id == customer_id).first()
    wallet_balance = float(customer.simulated_balance or 0.0) if customer else 2500000.0

    recent_txs = (
        db.query(Transaction)
        .filter(Transaction.customer_id == customer_id)
        .order_by(Transaction.created_at.desc())
        .limit(6)
        .all()
    )

    recent_alerts = (
        db.query(Alert)
        .filter(Alert.customer_id == customer_id)
        .order_by(Alert.created_at.desc())
        .limit(5)
        .all()
    )

    pending_verifications = (
        db.query(VerificationEvent)
        .filter(VerificationEvent.customer_id == customer_id, VerificationEvent.status == "PENDING")
        .count()
    )

    tx_dtos = []
    for t in recent_txs:
        tx_dtos.append({
            "id": t.id,
            "transaction_id": t.transaction_id,
            "amount": float(t.amount or 0.0),
            "currency": t.currency or "INR",
            "recipient": t.beneficiary or "Settlement Partner",
            "location": t.geo_location_region or "Mumbai",
            "device_id": t.device_id or "dev-mbp-m3",
            "status": t.status,
            "risk_score": float(t.risk_score or 5.0),
            "risk_level": t.risk_level or "LOW",
            "decision": t.decision,
            "created_at": t.created_at.isoformat() if t.created_at else None,
        })

    alert_dtos = []
    for a in recent_alerts:
        alert_dtos.append({
            "id": a.id,
            "alert_id": a.alert_id,
            "alert_type": a.alert_type,
            "severity": a.severity,
            "title": a.title or a.alert_type,
            "message": a.message,
            "status": a.status or "OPEN",
            "created_at": a.created_at.isoformat() if a.created_at else None,
        })

    return {
        "customer_id": customer_id,
        "user_name": current_user.name,
        "user_email": current_user.email,
        "account_tier": getattr(current_user, "account_tier", "PREMIUM") or "PREMIUM",
        "wallet_balance": wallet_balance,
        "currency": "INR",
        "security_health": health,
        "pending_verifications_count": pending_verifications,
        "recent_transactions": tx_dtos,
        "recent_alerts": alert_dtos,
    }


@router.get("/security-center", summary="Get Full Security Center Deep-Dive Data")
def get_security_center(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Provides complete explainable security score breakdown, baseline matrix, and protections."""
    customer_id = _enforce_user_isolation(current_user, db)
    health = PremiumSecurityService.get_security_health(db, current_user, customer_id)
    profile = PremiumSecurityService.get_or_create_behavioral_profile(db, current_user, customer_id)

    return {
        "security_health": health,
        "behavioral_baseline": {
            "normal_transaction_range": profile.normal_transaction_range,
            "normal_transaction_frequency": profile.normal_transaction_frequency,
            "common_transaction_times": profile.common_transaction_times,
            "common_locations": profile.common_locations,
            "trusted_devices": profile.trusted_devices,
            "average_transaction_amount": profile.average_transaction_amount,
            "summary": profile.behavioral_baseline,
            "updated_at": profile.updated_at.isoformat() if profile.updated_at else None,
        },
        "active_protections": [
            {"name": "Multi-Signal Adaptive Risk Engine", "status": "ACTIVE", "type": "Real-Time AI", "level": "Strict"},
            {"name": "Hardware Device Vault & Fingerprinting", "status": "ACTIVE", "type": "Cryptographic", "level": "Enforced"},
            {"name": "Zero-Trust Session Invariant Monitor", "status": "ACTIVE", "type": "Continuous", "level": "Real-Time"},
            {"name": "Progressive Step-Up OTP Verification", "status": "ACTIVE", "type": "Multi-Factor", "level": "Automatic"},
            {"name": "Tamper-Resistant Audit Trail", "status": "ACTIVE", "type": "Compliance", "level": "Immutable"},
        ],
    }


@router.get("/devices", summary="List Registered Hardware Devices")
def get_devices(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Lists registered hardware devices for the isolated user with trust scores and states."""
    customer_id = _enforce_user_isolation(current_user, db)
    devices = (
        db.query(CustomerDevice)
        .filter(CustomerDevice.customer_id == customer_id)
        .order_by(CustomerDevice.last_seen_at.desc())
        .all()
    )

    return [
        {
            "id": d.id,
            "device_id": d.device_identifier,
            "device_name": d.device_name or d.device_identifier,
            "device_type": d.device_type,
            "os": d.os or "Unknown OS",
            "browser": d.browser or d.browser_or_client or "Web Client",
            "trusted": bool(d.is_trusted and not d.is_compromised),
            "trust_score": d.trust_score if d.trust_score is not None else (100 if d.is_trusted else 25),
            "status": d.status or ("ACTIVE" if d.is_trusted else "SUSPICIOUS"),
            "first_seen": d.first_seen_at.isoformat() if d.first_seen_at else None,
            "last_seen": d.last_seen_at.isoformat() if d.last_seen_at else None,
        }
        for d in devices
    ]


@router.post("/devices/{device_identifier}/trust", summary="Mark Device as Trusted")
def trust_device(
    device_identifier: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Server-side authorized action to trust a registered hardware device."""
    customer_id = _enforce_user_isolation(current_user, db)
    device = db.query(CustomerDevice).filter(
        CustomerDevice.customer_id == customer_id,
        CustomerDevice.device_identifier == device_identifier,
    ).first()

    if not device:
        # Create registered trusted device
        device = CustomerDevice(
            user_id=current_user.id,
            customer_id=customer_id,
            device_identifier=device_identifier,
            device_name=device_identifier.replace("dev-", "").replace("-", " ").title(),
            device_type="desktop_macos",
            is_trusted=True,
            is_compromised=False,
            trust_score=98,
            status="ACTIVE",
        )
        db.add(device)
    else:
        device.is_trusted = True
        device.is_compromised = False
        device.trust_score = 98
        device.status = "ACTIVE"

    # Audit Log
    db.add(AuditLog(
        user_id=current_user.id,
        action="DEVICE_TRUST_UPDATED",
        resource_type="DEVICE",
        resource_id=device_identifier,
        entity="CustomerDevice",
        entity_id=device_identifier,
        result="SUCCESS",
        details=f"Device '{device_identifier}' marked as trusted with trust score 98.",
    ))
    db.commit()

    return {"success": True, "device_id": device_identifier, "status": "TRUSTED", "trust_score": 98}


@router.post("/devices/{device_identifier}/revoke", summary="Revoke or Untrust a Device")
def revoke_device(
    device_identifier: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Revokes device trust and flags it for anomaly re-evaluation."""
    customer_id = _enforce_user_isolation(current_user, db)
    device = db.query(CustomerDevice).filter(
        CustomerDevice.customer_id == customer_id,
        CustomerDevice.device_identifier == device_identifier,
    ).first()

    if not device:
        raise HTTPException(status_code=404, detail=f"Device '{device_identifier}' not found.")

    device.is_trusted = False
    device.trust_score = 20
    device.status = "REVOKED"

    db.add(AuditLog(
        user_id=current_user.id,
        action="DEVICE_REVOKED",
        resource_type="DEVICE",
        resource_id=device_identifier,
        entity="CustomerDevice",
        entity_id=device_identifier,
        result="SUCCESS",
        details=f"Trust revoked for device '{device_identifier}'.",
    ))
    db.commit()

    return {"success": True, "device_id": device_identifier, "status": "REVOKED", "trust_score": 20}


@router.get("/sessions", summary="List Active User Sessions")
def get_sessions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Lists current active user sessions with IP, approximate location, device, and risk status."""
    customer_id = _enforce_user_isolation(current_user, db)
    sessions = (
        db.query(UserSession)
        .filter(UserSession.customer_id == customer_id)
        .order_by(UserSession.last_active.desc())
        .all()
    )

    return [
        {
            "id": s.id,
            "session_id": s.session_id,
            "device_id": s.device_id,
            "device_name": s.device_name or s.device_id,
            "ip_address": s.ip_address,
            "approximate_location": s.approximate_location,
            "session_status": s.session_status,
            "risk_score": s.risk_score,
            "login_time": s.login_time.isoformat() if s.login_time else None,
            "last_active": s.last_active.isoformat() if s.last_active else None,
        }
        for s in sessions
    ]


@router.post("/sessions/{session_id}/revoke", summary="Revoke an Active Session")
def revoke_session(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Terminates an active session immediately with audit record."""
    customer_id = _enforce_user_isolation(current_user, db)
    session = db.query(UserSession).filter(
        UserSession.customer_id == customer_id,
        UserSession.session_id == session_id,
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found.")

    session.session_status = "REVOKED"
    db.add(AuditLog(
        user_id=current_user.id,
        action="SESSION_REVOCATION",
        resource_type="SESSION",
        resource_id=session_id,
        entity="UserSession",
        entity_id=session_id,
        result="SUCCESS",
        details=f"Active session '{session_id}' revoked by user.",
    ))
    db.commit()

    return {"success": True, "session_id": session_id, "status": "REVOKED"}


@router.get("/transactions", summary="List User Transactions with Explainability")
def get_transactions(
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Lists isolated transactions for user with normalized risk scores and explainable factors."""
    customer_id = _enforce_user_isolation(current_user, db)
    txs = (
        db.query(Transaction)
        .filter(Transaction.customer_id == customer_id)
        .order_by(Transaction.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    results = []
    for t in txs:
        # Fetch related risk events for factors
        risk_events = (
            db.query(RiskEvent)
            .filter(RiskEvent.transaction_id == t.transaction_id)
            .all()
        )
        factors = [re.explanation for re in risk_events] if risk_events else []

        results.append({
            "id": t.id,
            "transaction_id": t.transaction_id,
            "amount": float(t.amount or 0.0),
            "currency": t.currency or "INR",
            "recipient": t.beneficiary or "Settlement Partner",
            "transaction_type": t.transaction_type or "WIRE_TRANSFER",
            "location": t.geo_location_region or "Mumbai",
            "device_id": t.device_id or "dev-mbp-m3",
            "status": t.status,
            "risk_score": float(t.risk_score or 5.0),
            "risk_level": t.risk_level or "LOW",
            "decision": t.decision,
            "fraud_probability": float(t.fraud_probability or 0.05),
            "verification_status": "COMPLETED" if t.status == "SUCCESS" else ("HELD" if t.status == "HELD" else "NONE"),
            "contributing_factors": factors,
            "created_at": t.created_at.isoformat() if t.created_at else None,
        })

    return results


@router.get("/transactions/{transaction_id}", summary="Get Detailed Transaction with Explainable Audit")
def get_transaction_detail(
    transaction_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Fetches full transaction breakdown, SHAP explainability, verification logs, and factors."""
    customer_id = _enforce_user_isolation(current_user, db)
    t = db.query(Transaction).filter(
        Transaction.customer_id == customer_id,
        Transaction.transaction_id == transaction_id,
    ).first()

    if not t:
        raise HTTPException(status_code=404, detail=f"Transaction '{transaction_id}' not found or access denied.")

    risk_events = db.query(RiskEvent).filter(RiskEvent.transaction_id == transaction_id).all()
    factors = [re.explanation for re in risk_events]

    verif = db.query(VerificationEvent).filter(VerificationEvent.transaction_id == transaction_id).first()

    return {
        "transaction_id": t.transaction_id,
        "amount": float(t.amount or 0.0),
        "currency": t.currency or "INR",
        "recipient": t.beneficiary,
        "transaction_type": t.transaction_type,
        "location": t.geo_location_region,
        "device_id": t.device_id,
        "status": t.status,
        "risk_score": float(t.risk_score or 5.0),
        "risk_level": t.risk_level,
        "decision": t.decision,
        "fraud_probability": float(t.fraud_probability or 0.05),
        "contributing_factors": factors,
        "verification_event": {
            "status": verif.status,
            "attempts_count": verif.attempts_count,
            "max_attempts": verif.max_attempts,
            "expires_at": verif.expires_at.isoformat() if verif.expires_at else None,
            "verified_at": verif.verified_at.isoformat() if verif.verified_at else None,
        } if verif else None,
        "created_at": t.created_at.isoformat() if t.created_at else None,
    }


@router.post("/transactions/evaluate", summary="Evaluate and Execute / Hold Transaction")
def evaluate_transaction(
    payload: TransactionEvaluateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Processes transaction through Multi-Signal Adaptive Risk Engine (ALLOW / STEP_UP_VERIFICATION / TEMPORARY_HOLD)."""
    customer_id = _enforce_user_isolation(current_user, db)
    try:
        result = PremiumSecurityService.execute_or_stage_transaction(
            db=db,
            user=current_user,
            customer_id=customer_id,
            amount=payload.amount,
            recipient=payload.recipient,
            device_id=payload.device_id,
            device_name=payload.device_name,
            location=payload.location,
            transaction_type=payload.transaction_type or "WIRE_TRANSFER",
            transaction_hour=payload.transaction_hour,
            currency=payload.currency or "INR",
        )
        return result
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error("Error evaluating premium transaction: %s", e)
        raise HTTPException(status_code=500, detail="Security Verification Engine temporarily unavailable. Please retry.")


@router.post("/verification/verify-otp", summary="Verify OTP Code Server-Side")
def verify_otp(
    payload: VerifyOtpRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Validates 6-digit OTP passcode with expiration, attempt limits, and safe state transitions."""
    customer_id = _enforce_user_isolation(current_user, db)
    try:
        res = PremiumSecurityService.verify_otp_code(
            db=db,
            user=current_user,
            customer_id=customer_id,
            transaction_id=payload.transaction_id,
            otp_code=payload.otp_code,
        )
        return res
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error("Error verifying OTP: %s", e)
        raise HTTPException(status_code=500, detail="OTP Verification service error. Please retry.")


@router.post("/verification/request-otp", summary="Request or Resend OTP")
def request_otp(
    payload: RequestOtpPayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generates a fresh OTP passcode enforcing resend cooldown."""
    customer_id = _enforce_user_isolation(current_user, db)
    now = datetime.now(timezone.utc)

    verif = db.query(VerificationEvent).filter(
        VerificationEvent.customer_id == customer_id,
        VerificationEvent.transaction_id == payload.transaction_id,
    ).order_by(VerificationEvent.created_at.desc()).first()

    if not verif:
        raise HTTPException(status_code=404, detail="No active verification requirement for this transaction.")

    # Check cooldown
    if verif.resend_available_at:
        resend_at = verif.resend_available_at.replace(tzinfo=timezone.utc) if verif.resend_available_at.tzinfo is None else verif.resend_available_at
        if now < resend_at:
            remaining_secs = int((resend_at - now).total_seconds())
            raise HTTPException(status_code=429, detail=f"Please wait {remaining_secs}s before requesting a new code.")

    raw_otp = f"{secrets.randbelow(900000) + 100000:06d}"
    verif.otp_code_hash = PremiumSecurityService._hash_otp(raw_otp)
    verif.attempts_count = 0
    verif.status = "PENDING"
    verif.expires_at = now + timedelta(minutes=5)
    verif.resend_available_at = now + timedelta(seconds=30)
    db.commit()

    return {
        "success": True,
        "transaction_id": payload.transaction_id,
        "expires_in_seconds": 300,
        "simulation_demo_code": raw_otp,
        "message": "A new verification passcode has been dispatched to your authorized device.",
    }


@router.get("/alerts", summary="List Security Alerts")
def get_alerts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Fetches in-app security alerts (INFO, WARNING, HIGH, CRITICAL)."""
    customer_id = _enforce_user_isolation(current_user, db)
    alerts = (
        db.query(Alert)
        .filter(Alert.customer_id == customer_id)
        .order_by(Alert.created_at.desc())
        .all()
    )

    return [
        {
            "id": a.id,
            "alert_id": a.alert_id,
            "alert_type": a.alert_type,
            "severity": a.severity,
            "title": a.title or a.alert_type,
            "message": a.message,
            "status": a.status or ("ACKNOWLEDGED" if a.is_acknowledged else "OPEN"),
            "is_acknowledged": a.is_acknowledged,
            "created_at": a.created_at.isoformat() if a.created_at else None,
            "resolved_at": a.resolved_at.isoformat() if a.resolved_at else None,
        }
        for a in alerts
    ]


@router.post("/alerts/{alert_id}/acknowledge", summary="Acknowledge or Resolve Alert")
def acknowledge_alert(
    alert_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Marks security alert as acknowledged and resolved."""
    customer_id = _enforce_user_isolation(current_user, db)
    alert = db.query(Alert).filter(
        Alert.customer_id == customer_id,
        Alert.alert_id == alert_id,
    ).first()

    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found.")

    now = datetime.now(timezone.utc)
    alert.is_acknowledged = True
    alert.status = "RESOLVED"
    alert.acknowledged_at = now
    alert.resolved_at = now
    alert.acknowledged_by = current_user.email
    db.commit()

    return {"success": True, "alert_id": alert_id, "status": "RESOLVED"}


@router.get("/audit-trail", summary="List Immutable Audit Trail Records")
def get_audit_trail(
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Returns tamper-resistant security audit log entries for isolated user."""
    logs = (
        db.query(AuditLog)
        .filter(AuditLog.user_id == current_user.id)
        .order_by(AuditLog.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    return [
        {
            "id": l.id,
            "action": l.action,
            "resource_type": l.resource_type,
            "resource_id": l.resource_id,
            "entity": l.entity or l.resource_type,
            "entity_id": l.entity_id or l.resource_id,
            "ip_address": l.ip_address or "49.37.142.88",
            "device_id": l.device_id or "dev-mbp-m3",
            "result": l.result or "SUCCESS",
            "details": l.details,
            "timestamp": l.created_at.isoformat() if l.created_at else None,
        }
        for l in logs
    ]


@router.get("/scenarios", summary="List Available Demo Scenarios A, B, C, D")
def list_scenarios():
    """Returns preconfigured demo scenarios (Section 38)."""
    return PremiumSecurityService.get_demo_scenarios()


@router.post("/scenarios/run", summary="Execute Demo Scenario A, B, C, or D")
def run_scenario(
    payload: RunScenarioRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Executes a demo scenario through the real risk engine."""
    customer_id = _enforce_user_isolation(current_user, db)
    scenarios = {s["id"]: s for s in PremiumSecurityService.get_demo_scenarios()}
    scenario = scenarios.get(payload.scenario_id)

    if not scenario:
        raise HTTPException(status_code=400, detail=f"Unknown scenario ID '{payload.scenario_id}'.")

    try:
        result = PremiumSecurityService.execute_or_stage_transaction(
            db=db,
            user=current_user,
            customer_id=customer_id,
            amount=scenario["amount"],
            recipient=scenario["recipient"],
            device_id=scenario["device_id"],
            device_name=scenario["device_name"],
            location=scenario["location"],
            transaction_type=scenario["transaction_type"],
            transaction_hour=scenario.get("transaction_hour"),
            currency="INR",
        )
        result["scenario"] = scenario
        return result
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error("Error executing scenario: %s", e)
        raise HTTPException(status_code=500, detail="Scenario execution error.")

