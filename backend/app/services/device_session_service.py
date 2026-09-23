"""
Device and Session Risk Intelligence Service.
Part C: Fraud Intelligence Fabric.

Evaluates device telemetry, session anomalies, and hardware fingerprint novelty
with zero storage or inspection of raw credentials, OTP, PIN, or CVV.
"""

import hashlib
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from backend.app.models.transaction import Transaction
from backend.app.models.payment_intent import PaymentIntent


@dataclass
class DeviceSessionAssessment:
    """Diagnostic outcome for hardware device and active session telemetry."""
    device_fingerprint: str
    session_id: str
    device_type: str
    is_novel_device: bool
    is_spoofed_environment: bool
    device_risk_score: float           # 0.0 - 100.0
    session_risk_score: float          # 0.0 - 100.0
    combined_hardware_score: float     # 0.0 - 100.0
    risk_level: str                    # LOW | MEDIUM | HIGH
    session_age_minutes: int
    session_transaction_count: int
    failed_attempts_in_session: int
    is_high_risk_channel: bool
    evidence: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class DeviceSessionRiskService:
    """Evaluates device trust, session anomalies, and spoofing indicators."""

    HIGH_RISK_KEYWORDS = ["tor", "proxy", "vpn", "emulator", "spoofed", "bot", "headless"]

    @classmethod
    def generate_anonymized_device_id(
        cls,
        device_raw: Optional[str],
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> str:
        """Derive deterministic non-reversible SHA-256 device fingerprint."""
        components = f"{device_raw or 'web_generic'}:{ip_address or '0.0.0.0'}:{user_agent or 'std_client'}"
        return f"dev_{hashlib.sha256(components.encode('utf-8')).hexdigest()[:16]}"

    @classmethod
    def evaluate_device_session(
        cls,
        db: Session,
        customer_id: str,
        device_type: Optional[str] = "web",
        device_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        session_id: Optional[str] = None,
        failed_attempts: int = 0,
        channel: Optional[str] = "web",
        current_timestamp: Optional[datetime] = None,
    ) -> DeviceSessionAssessment:
        """
        Evaluate device novelty, hardware spoofing, and session velocity.
        Guarantees strict privacy with zero credential storage.
        """
        now = current_timestamp or datetime.now(timezone.utc)
        effective_session_id = session_id or f"sess_{hashlib.sha256(f'{customer_id}_{now.strftime('%Y%m%d%H')}'.encode('utf-8')).hexdigest()[:12]}"
        anonymized_device = device_id or cls.generate_anonymized_device_id(device_type, ip_address)

        dev_norm = (device_type or "web").lower().strip()
        channel_norm = (channel or "web").lower().strip()

        # Check customer history for known devices
        historical_transactions = (
            db.query(Transaction)
            .filter(Transaction.customer_id == customer_id)
            .order_by(Transaction.created_at.desc())
            .limit(50)
            .all()
        )

        known_devices = {
            t.device_type.lower().strip()
            for t in historical_transactions
            if t.device_type
        }

        # Check PaymentIntent ledger as well
        recent_intents = (
            db.query(PaymentIntent)
            .filter(PaymentIntent.customer_id == customer_id)
            .order_by(PaymentIntent.created_at.desc())
            .limit(20)
            .all()
        )

        # Device novelty detection
        is_novel = (dev_norm not in known_devices) if known_devices else False

        # Session transaction velocity
        session_tx_count = sum(
            1 for t in historical_transactions
            if t.created_at and (
                (t.created_at.replace(tzinfo=timezone.utc) if t.created_at.tzinfo is None else t.created_at)
                >= (now - timedelta(minutes=30))
            )
        ) + 1  # include current

        session_age_est = min(120, max(5, session_tx_count * 8))

        # Check for spoofed / anonymized / emulator signatures
        is_spoofed = any(kw in dev_norm for kw in cls.HIGH_RISK_KEYWORDS) or any(kw in (ip_address or "").lower() for kw in ["185.220.", "tor_exit"])
        is_high_risk_ch = channel_norm in ["api", "tor_exit_node", "headless_browser", "unknown_proxy"]

        # Compute Device Risk Score (0 - 100)
        dev_score = 0.0
        evidence: List[str] = []

        if is_spoofed:
            dev_score += 65.0
            evidence.append(f"High-risk spoofed or anonymized proxy environment detected ('{dev_norm}').")

        if is_novel:
            dev_score += 25.0
            evidence.append(f"Unrecognized device profile '{dev_norm}' for customer {customer_id}.")

        if is_high_risk_ch:
            dev_score += 20.0
            evidence.append(f"High-risk transaction submission channel '{channel_norm}'.")

        # Compute Session Risk Score (0 - 100)
        sess_score = 0.0
        if failed_attempts >= 3:
            sess_score += 45.0
            evidence.append(f"Severe session authentication risk: {failed_attempts} failed attempts in current session.")
        elif failed_attempts >= 1:
            sess_score += 15.0
            evidence.append(f"{failed_attempts} failed authentication attempt in active session.")

        if session_tx_count >= 4:
            sess_score += 35.0
            evidence.append(f"High session velocity burst: {session_tx_count} checkout attempts within 30 minutes.")
        elif session_tx_count >= 2:
            sess_score += 10.0

        # Combined score
        combined_score = min(100.0, max(0.0, round((dev_score * 0.6) + (sess_score * 0.4), 2)))

        if combined_score >= 70.0:
            level = "HIGH"
        elif combined_score >= 35.0:
            level = "MEDIUM"
        else:
            level = "LOW"

        return DeviceSessionAssessment(
            device_fingerprint=anonymized_device,
            session_id=effective_session_id,
            device_type=dev_norm,
            is_novel_device=is_novel,
            is_spoofed_environment=is_spoofed,
            device_risk_score=round(min(100.0, dev_score), 2),
            session_risk_score=round(min(100.0, sess_score), 2),
            combined_hardware_score=combined_score,
            risk_level=level,
            session_age_minutes=session_age_est,
            session_transaction_count=session_tx_count,
            failed_attempts_in_session=failed_attempts,
            is_high_risk_channel=is_high_risk_ch,
            evidence=evidence,
        )
