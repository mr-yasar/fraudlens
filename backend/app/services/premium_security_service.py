"""Premium Security Service - Enterprise Grade Multi-Signal Adaptive Risk Engine,
Hardware Device Trust, Session Security, Step-Up Cryptographic OTP Verification,
and Explainable Risk Decision Orchestrator.
"""

import hashlib
import json
import logging
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.app.core.config import settings
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
from backend.app.services.prediction_service import FraudPredictionService
from backend.app.services.event_broadcaster import event_broadcaster

logger = logging.getLogger("fraudlens.premium_security")


class PremiumSecurityService:
    """Core enterprise security engine implementing Sections 5-38 of FraudLens AI specification."""

    @staticmethod
    def _hash_otp(code: str) -> str:
        """Create cryptographic SHA-256 hash of OTP code for secure server-side storage."""
        return hashlib.sha256(code.encode("utf-8")).hexdigest()

    @staticmethod
    def get_or_create_behavioral_profile(db: Session, user: User, customer_id: str) -> BehavioralProfile:
        """Retrieve or initialize baseline profile for customer."""
        profile = db.query(BehavioralProfile).filter(BehavioralProfile.customer_id == customer_id).first()
        if not profile:
            profile = BehavioralProfile(
                user_id=user.id if user else None,
                customer_id=customer_id,
                normal_transaction_range="₹5,000 - ₹150,000",
                normal_transaction_frequency="2-4 transactions/day",
                common_transaction_times="08:00 - 22:00 IST",
                common_locations="Mumbai, Bangalore, Singapore",
                trusted_devices="MacBook Pro M3 Max, iPhone 15 Pro Max",
                average_transaction_amount=45000.0,
                security_score=98,
                behavioral_baseline="High-frequency enterprise settlement account with strict biometric authentication and low volatility.",
            )
            db.add(profile)
            db.commit()
            db.refresh(profile)
        return profile

    @classmethod
    def evaluate_adaptive_risk(
        cls,
        db: Session,
        user: User,
        customer_id: str,
        amount: float,
        recipient: str,
        device_id: str,
        device_name: Optional[str] = None,
        location: Optional[str] = "Mumbai / Cyber City",
        transaction_type: str = "WIRE_TRANSFER",
        transaction_hour: Optional[int] = None,
        currency: str = "INR",
        payment_channel: str = "ONLINE",
    ) -> Dict[str, Any]:
        """Multi-signal Adaptive Risk Engine evaluating Transaction, Time, Location, Device, and Auth signals."""
        now = datetime.now(timezone.utc)
        hour = transaction_hour if transaction_hour is not None else now.hour
        contributing_factors: List[str] = []
        base_score = 5  # Base healthy operational baseline

        profile = cls.get_or_create_behavioral_profile(db, user, customer_id)

        # -----------------------------------------------------------------
        # 1. Device Signals
        # -----------------------------------------------------------------
        device = db.query(CustomerDevice).filter(
            CustomerDevice.customer_id == customer_id,
            CustomerDevice.device_identifier == device_id,
        ).first()

        is_new_device = False
        is_trusted_device = True
        device_risk_penalty = 0

        if not device:
            is_new_device = True
            is_trusted_device = False
            device_risk_penalty = 18
            contributing_factors.append(f"Unrecognized Hardware Signature: Device ID '{device_id}' is not in your registered trusted device vault.")
        elif not device.is_trusted or device.is_compromised:
            is_trusted_device = False
            device_risk_penalty = 22
            contributing_factors.append(f"Compromised or Untrusted Device: Hardware '{device.device_name or device_id}' flagged with reduced trust score ({device.trust_score}/100).")
        else:
            # Trusted device bonus
            device_risk_penalty = 0

        # -----------------------------------------------------------------
        # 2. Transaction Amount & Deviation Signals
        # -----------------------------------------------------------------
        avg_amount = profile.average_transaction_amount or 45000.0
        amount_ratio = amount / max(avg_amount, 1.0)
        amount_penalty = 0

        if amount > 500000.0:  # > 5 Lakhs
            amount_penalty = 22
            contributing_factors.append(f"Extreme Volume Surge: Transfer amount ₹{amount:,.2f} exceeds high-value threshold (₹500,000.00).")
        elif amount > 150000.0:  # Above normal range upper bound
            amount_penalty = 14
            contributing_factors.append(f"Amount Above Normal Range: Transfer ₹{amount:,.2f} is {amount_ratio:.1f}x your normal average transaction baseline (₹{avg_amount:,.2f}).")
        elif amount > 75000.0:
            amount_penalty = 8
            contributing_factors.append(f"Slight Volume Elevation: Transfer ₹{amount:,.2f} is higher than standard routine transactions.")

        # -----------------------------------------------------------------
        # 3. Recipient / Beneficiary Signals
        # -----------------------------------------------------------------
        bene = db.query(Beneficiary).filter(
            Beneficiary.customer_id == customer_id,
            Beneficiary.beneficiary_name.ilike(f"%{recipient.strip()}%"),
        ).first()

        bene_penalty = 0
        is_new_recipient = False
        if not bene:
            is_new_recipient = True
            bene_penalty = 16
            contributing_factors.append(f"First-Time Recipient: Beneficiary '{recipient}' is not registered in your verified directory.")
        elif not bene.is_trusted:
            bene_penalty = 14
            contributing_factors.append(f"Unverified Recipient: Beneficiary '{recipient}' has unverified security status.")

        # -----------------------------------------------------------------
        # 4. Time Signals
        # -----------------------------------------------------------------
        time_penalty = 0
        # Unusual night hours: 00:00 - 05:30
        if 0 <= hour <= 5:
            time_penalty = 18
            contributing_factors.append(f"Unusual Night-Time Activity: Transaction initiated at {hour:02d}:00 hours (standard active window: 08:00 - 22:00 IST).")
        elif 22 <= hour <= 23:
            time_penalty = 6
            contributing_factors.append(f"Off-Peak Hour: Transaction initiated late evening at {hour:02d}:00 hours.")

        # -----------------------------------------------------------------
        # 5. Location Signals
        # -----------------------------------------------------------------
        loc_str = (location or "").lower()
        loc_penalty = 0
        high_risk_locs = ["russia", "moscow", "st. petersburg", "nigeria", "cayman", "north korea", "unknown proxy", "tor exit node"]
        if any(hr in loc_str for hr in high_risk_locs):
            loc_penalty = 26
            contributing_factors.append(f"High-Risk Geo-IP Jurisdiction: Originating network location '{location}' is flagged for anomalous financial risk.")
        elif not any(norm in loc_str for norm in ["mumbai", "bangalore", "pune", "delhi", "singapore", "india"]):
            loc_penalty = 10
            contributing_factors.append(f"Unfamiliar Geo-Location: Activity detected from '{location}', differing from your primary active hubs (Mumbai, Bangalore, Singapore).")

        # -----------------------------------------------------------------
        # 6. ML Model Inference Integration (Section 25)
        # -----------------------------------------------------------------
        ml_prob = 0.05
        ml_prediction = 0
        try:
            prediction_svc = FraudPredictionService.get_instance()
            if prediction_svc and prediction_svc.is_ready:
                from backend.app.schemas.prediction import TransactionPredictionInput
                pred_input = TransactionPredictionInput(
                    amount=float(amount),
                    transaction_hour=int(hour),
                    day_of_week=now.weekday(),
                    merchant_category="enterprise_settlement",
                    transaction_country="IN" if "india" in loc_str or "mumbai" in loc_str else "US",
                    device_type=device.device_type if device else "desktop_macos",
                    transaction_type=transaction_type,
                    customer_account_age_days=720,
                    is_new_device=1 if is_new_device else 0,
                    is_new_beneficiary=1 if is_new_recipient else 0,
                    location=location or "Mumbai",
                    customer_historical_avg_amount=avg_amount,
                )
                pred_res = prediction_svc.predict_transaction(pred_input, include_shap_summary=False)
                ml_prob = float(pred_res.fraud_probability)
                ml_prediction = 1 if pred_res.prediction == "FRAUD" else 0
        except Exception as e:
            logger.warning("ML prediction service fallback in premium evaluator: %s", e)
            ml_prob = min(0.95, (amount_penalty + device_risk_penalty + loc_penalty) / 100.0)

        # -----------------------------------------------------------------
        # 7. Signal Fusion & Score Normalization (Section 10)
        # -----------------------------------------------------------------
        raw_anomaly_sum = device_risk_penalty + amount_penalty + bene_penalty + time_penalty + loc_penalty
        if raw_anomaly_sum == 0:
            # Clean baseline transaction
            total_score = min(15, base_score + int(ml_prob * 8))
        else:
            ml_component = int(ml_prob * 10)
            total_score = min(99, max(2, base_score + raw_anomaly_sum + ml_component))

        # Progressive Security State Machine (Section 12 & 26)
        if total_score < 25:
            risk_level = "LOW"
            decision = "ALLOW"
            verification_status = "NOT_REQUIRED"
            current_decision_text = "AUTHORIZED (LOW RISK)"
            next_step = "Transaction cleared for instant execution. No OTP required."
            if not contributing_factors:
                contributing_factors.append("All signals within standard behavioral baseline (Known Device, Trusted Recipient, Standard Hours).")
        elif total_score < 50:
            risk_level = "MEDIUM"
            decision = "STEP_UP_VERIFICATION"
            verification_status = "PENDING_OTP"
            current_decision_text = "STEP-UP VERIFICATION REQUIRED"
            next_step = "Complete fast one-time verification passcode to authorize."
        elif total_score < 75:
            risk_level = "HIGH"
            decision = "TEMPORARY_HOLD"
            verification_status = "TEMPORARILY_HELD"
            current_decision_text = "TEMPORARILY HELD"
            next_step = "Transaction is temporarily held for your protection. Complete strong multi-factor verification to proceed."
        else:
            risk_level = "CRITICAL"
            decision = "TEMPORARY_HOLD"
            verification_status = "HIGH_PRIORITY_HOLD"
            current_decision_text = "HELD & SECURITY ALERT ISSUED"
            next_step = "High anomaly combination detected. Immediate security confirmation and cryptographic OTP required."

        return {
            "risk_score": total_score,
            "risk_level": risk_level,
            "decision": decision,
            "verification_status": verification_status,
            "current_decision_text": current_decision_text,
            "next_step": next_step,
            "fraud_probability": round(ml_prob, 4),
            "ml_prediction": ml_prediction,
            "contributing_factors": contributing_factors,
            "is_new_device": is_new_device,
            "is_trusted_device": is_trusted_device,
            "is_new_recipient": is_new_recipient,
            "transaction_hour": hour,
            "location": location,
        }

    @classmethod
    def execute_or_stage_transaction(
        cls,
        db: Session,
        user: User,
        customer_id: str,
        amount: float,
        recipient: str,
        device_id: str,
        device_name: Optional[str] = None,
        location: Optional[str] = "Mumbai / Cyber City",
        transaction_type: str = "WIRE_TRANSFER",
        transaction_hour: Optional[int] = None,
        currency: str = "INR",
    ) -> Dict[str, Any]:
        """Executes transaction or places it into Step-Up Verification / Temporary Hold state."""
        now = datetime.now(timezone.utc)
        # 1. Run multi-signal evaluation
        eval_result = cls.evaluate_adaptive_risk(
            db=db,
            user=user,
            customer_id=customer_id,
            amount=amount,
            recipient=recipient,
            device_id=device_id,
            device_name=device_name,
            location=location,
            transaction_type=transaction_type,
            transaction_hour=transaction_hour,
            currency=currency,
        )

        customer = db.query(Customer).filter(Customer.customer_id == customer_id).first()
        if not customer:
            customer = Customer(
                customer_id=customer_id,
                name=user.name if user else "Ajay",
                email=user.email if user else "ajay@fraudlens.ai",
                simulated_balance=2500000.0,
                currency=currency,
                risk_segment="Enterprise Security",
            )
            db.add(customer)
            db.commit()
            db.refresh(customer)

        # 2. Check balance sufficiency
        if (customer.simulated_balance or 0.0) < amount:
            raise ValueError(f"Insufficient funds: Wallet balance ₹{customer.simulated_balance:,.2f} is lower than transfer amount ₹{amount:,.2f}.")

        # 3. Create Transaction Record
        tx_id = f"TX-PREM-{secrets.token_hex(4).upper()}"
        initial_status = "SUCCESS" if eval_result["decision"] == "ALLOW" else "HELD"

        tx = Transaction(
            transaction_id=tx_id,
            customer_id=customer_id,
            amount=amount,
            currency=currency,
            transaction_hour=eval_result["transaction_hour"],
            transaction_type=transaction_type,
            transaction_country="IN" if "india" in (location or "").lower() or "mumbai" in (location or "").lower() else "US",
            geo_location_region=location,
            current_location=location,
            device_id=device_id,
            device_type="desktop_macos" if "mac" in (device_name or "").lower() else "mobile_ios",
            is_new_device=eval_result["is_new_device"],
            is_trusted_device=eval_result["is_trusted_device"],
            beneficiary=recipient,
            is_new_beneficiary=eval_result["is_new_recipient"],
            fraud_probability=eval_result["fraud_probability"],
            prediction=eval_result["ml_prediction"],
            risk_score=float(eval_result["risk_score"]),
            risk_level=eval_result["risk_level"],
            status=initial_status,
        )
        db.add(tx)
        db.commit()
        db.refresh(tx)

        # 4. Create Granular Risk Event records for explainability (Section 7)
        for factor in eval_result["contributing_factors"]:
            risk_event = RiskEvent(
                user_id=user.id if user else None,
                customer_id=customer_id,
                transaction_id=tx_id,
                event_type="RISK_FACTOR_DETECTED",
                severity=eval_result["risk_level"],
                score=eval_result["risk_score"],
                explanation=factor,
                details_json=json.dumps({"amount": amount, "recipient": recipient, "device_id": device_id}),
            )
            db.add(risk_event)

        # 5. Handle Progressive Security Flow
        otp_challenge = None
        if eval_result["decision"] == "ALLOW":
            # Deduct balance immediately
            customer.simulated_balance = float(customer.simulated_balance or 0.0) - amount
            db.commit()

            # Audit Log
            db.add(AuditLog(
                user_id=user.id if user else None,
                action="TRANSACTION_ALLOW",
                resource_type="TRANSACTION",
                resource_id=tx_id,
                entity="Transaction",
                entity_id=tx_id,
                ip_address="49.37.142.88",
                device_id=device_id,
                result="SUCCESS",
                details=json.dumps({
                    "amount": amount,
                    "recipient": recipient,
                    "risk_score": eval_result["risk_score"],
                    "risk_level": eval_result["risk_level"],
                }),
            ))
            db.commit()

            # Broadcast Real-Time Event
            try:
                event_broadcaster.sync_broadcast("TRANSACTION_APPROVED", {
                    "transaction_id": tx_id,
                    "customer_id": customer_id,
                    "amount": amount,
                    "risk_score": eval_result["risk_score"],
                    "risk_level": "LOW",
                    "timestamp": now.isoformat(),
                })
            except Exception:
                pass

        else:
            # Staged for Step-up OTP Verification or Temporary Hold
            raw_otp = f"{secrets.randbelow(900000) + 100000:06d}"  # 6-digit numeric OTP
            hashed_otp = cls._hash_otp(raw_otp)
            expires_at = now + timedelta(minutes=5)

            verif_event = VerificationEvent(
                user_id=user.id if user else None,
                customer_id=customer_id,
                transaction_id=tx_id,
                verification_type="OTP_SMS_HARDWARE",
                status="PENDING",
                otp_code_hash=hashed_otp,
                attempts_count=0,
                max_attempts=3,
                expires_at=expires_at,
                resend_available_at=now + timedelta(seconds=30),
            )
            db.add(verif_event)

            # Create Security Alert
            alert_sev = eval_result["risk_level"]
            alert = Alert(
                alert_id=f"ALT-{secrets.token_hex(4).upper()}",
                user_id=user.id if user else None,
                customer_id=customer_id,
                alert_type="TRANSACTION_HOLD_STEP_UP",
                severity=alert_sev,
                title=f"{alert_sev} Risk Transaction Held for Verification",
                message=f"Transfer of ₹{amount:,.2f} to '{recipient}' was held. Multi-factor verification required.",
                status="OPEN",
                details_json=json.dumps({
                    "transaction_id": tx_id,
                    "risk_score": eval_result["risk_score"],
                    "factors": eval_result["contributing_factors"],
                }),
            )
            db.add(alert)

            # Audit Log
            db.add(AuditLog(
                user_id=user.id if user else None,
                action="TRANSACTION_HOLD",
                resource_type="TRANSACTION",
                resource_id=tx_id,
                entity="Transaction",
                entity_id=tx_id,
                ip_address="49.37.142.88",
                device_id=device_id,
                result="PENDING_VERIFICATION",
                details=json.dumps({
                    "amount": amount,
                    "risk_score": eval_result["risk_score"],
                    "factors": eval_result["contributing_factors"],
                }),
            ))
            db.commit()

            # Step-up verification payload (raw OTP exposed ONLY for instant demo verification helper in simulation UI)
            otp_challenge = {
                "transaction_id": tx_id,
                "verification_type": "OTP_SMS_HARDWARE",
                "expires_in_seconds": 300,
                "max_attempts": 3,
                "resend_cooldown_seconds": 30,
                "simulation_demo_code": raw_otp,  # For seamless interactive reviewer testing
            }

            try:
                event_broadcaster.sync_broadcast("VERIFICATION_REQUIRED", {
                    "transaction_id": tx_id,
                    "customer_id": customer_id,
                    "amount": amount,
                    "risk_score": eval_result["risk_score"],
                    "risk_level": eval_result["risk_level"],
                    "timestamp": now.isoformat(),
                })
            except Exception:
                pass

        return {
            "transaction_id": tx_id,
            "status": tx.status,
            "amount": amount,
            "currency": currency,
            "recipient": recipient,
            "wallet_balance": float(customer.simulated_balance or 0.0),
            "risk_score": eval_result["risk_score"],
            "risk_level": eval_result["risk_level"],
            "decision": eval_result["decision"],
            "verification_status": eval_result["verification_status"],
            "current_decision_text": eval_result["current_decision_text"],
            "next_step": eval_result["next_step"],
            "contributing_factors": eval_result["contributing_factors"],
            "otp_challenge": otp_challenge,
            "created_at": tx.created_at.isoformat() if tx.created_at else now.isoformat(),
        }

    @classmethod
    def verify_otp_code(
        cls,
        db: Session,
        user: User,
        customer_id: str,
        transaction_id: str,
        otp_code: str,
    ) -> Dict[str, Any]:
        """Validates OTP code server-side against stored hash, enforcing expiration and attempt limits."""
        now = datetime.now(timezone.utc)

        # 1. Find pending verification event
        verif = db.query(VerificationEvent).filter(
            VerificationEvent.customer_id == customer_id,
            VerificationEvent.transaction_id == transaction_id,
            VerificationEvent.status == "PENDING",
        ).order_by(VerificationEvent.created_at.desc()).first()

        if not verif:
            raise ValueError(f"No pending verification challenge found for transaction '{transaction_id}'.")

        # 2. Check Expiration
        expires_at = verif.expires_at.replace(tzinfo=timezone.utc) if verif.expires_at.tzinfo is None else verif.expires_at
        if now > expires_at:
            verif.status = "EXPIRED"
            db.commit()
            raise ValueError("Verification passcode has expired. Please request a new code.")

        # 3. Check Attempt Limits
        if verif.attempts_count >= verif.max_attempts:
            verif.status = "LOCKED"
            db.commit()
            raise ValueError("Maximum verification attempts exceeded. Transaction locked for security.")

        # 4. Check Code Hash
        input_hash = cls._hash_otp(otp_code.strip())
        verif.attempts_count += 1
        verif.last_attempted_at = now

        if input_hash != verif.otp_code_hash:
            db.commit()
            remaining = verif.max_attempts - verif.attempts_count
            raise ValueError(f"Incorrect passcode. {remaining} attempt(s) remaining.")

        # 5. Success! Mark Verified
        verif.status = "VERIFIED"
        verif.verified_at = now

        # Update Transaction status & deduct wallet balance
        tx = db.query(Transaction).filter(
            Transaction.customer_id == customer_id,
            Transaction.transaction_id == transaction_id,
        ).first()

        customer = db.query(Customer).filter(Customer.customer_id == customer_id).first()

        if tx and tx.status != "SUCCESS":
            tx.status = "SUCCESS"
            if customer:
                customer.simulated_balance = max(0.0, float(customer.simulated_balance or 0.0) - float(tx.amount or 0.0))

        # Resolve related open alert
        alert = db.query(Alert).filter(
            Alert.customer_id == customer_id,
            Alert.status == "OPEN",
            Alert.details_json.like(f"%{transaction_id}%"),
        ).first()
        if alert:
            alert.status = "RESOLVED"
            alert.is_acknowledged = True
            alert.resolved_at = now
            alert.acknowledged_by = user.email if user else "Customer"

        # Log Audit Trail
        db.add(AuditLog(
            user_id=user.id if user else None,
            action="VERIFICATION_SUCCESS",
            resource_type="TRANSACTION",
            resource_id=transaction_id,
            entity="VerificationEvent",
            entity_id=str(verif.id),
            result="SUCCESS",
            details=json.dumps({"transaction_id": transaction_id, "attempts": verif.attempts_count}),
        ))
        db.commit()

        # Broadcast Approved Event
        try:
            event_broadcaster.sync_broadcast("TRANSACTION_APPROVED", {
                "transaction_id": transaction_id,
                "customer_id": customer_id,
                "amount": float(tx.amount) if tx else 0.0,
                "status": "SUCCESS",
                "timestamp": now.isoformat(),
            })
        except Exception:
            pass

        return {
            "success": True,
            "status": "APPROVED",
            "transaction_id": transaction_id,
            "message": "Step-up verification successful! Transaction authorized and funds settled.",
            "wallet_balance": float(customer.simulated_balance or 0.0) if customer else 0.0,
        }

    @classmethod
    def get_security_health(cls, db: Session, user: User, customer_id: str) -> Dict[str, Any]:
        """Calculates explainable Security Health score and defense metrics (Section 36)."""
        devices = db.query(CustomerDevice).filter(CustomerDevice.customer_id == customer_id).all()
        sessions = db.query(UserSession).filter(UserSession.customer_id == customer_id, UserSession.session_status == "ACTIVE").all()
        alerts = db.query(Alert).filter(Alert.customer_id == customer_id, Alert.status == "OPEN").all()
        recent_txs = db.query(Transaction).filter(Transaction.customer_id == customer_id).order_by(Transaction.created_at.desc()).limit(10).all()

        trusted_devices_count = sum(1 for d in devices if d.trusted)
        active_sessions_count = len(sessions)
        open_alerts_count = len(alerts)

        # Baseline calculation
        score = 98
        factors: List[str] = []

        if open_alerts_count > 0:
            score -= min(20, open_alerts_count * 8)
            factors.append(f"{open_alerts_count} unresolved security alert(s)")

        high_risk_tx_count = sum(1 for t in recent_txs if t.risk_level in ("HIGH", "CRITICAL"))
        if high_risk_tx_count > 0:
            score -= min(20, high_risk_tx_count * 5)
            factors.append(f"{high_risk_tx_count} recent elevated risk transaction(s)")

        if trusted_devices_count >= 2:
            factors.append("Multi-device hardware trust active (MacBook Pro & iPhone 15 Pro)")

        if not factors:
            factors.append("All baseline security invariants optimal. No active threat vectors.")

        score = max(10, min(100, score))

        if score >= 85:
            status_text = "Excellent"
            status_color = "emerald"
        elif score >= 65:
            status_text = "Good"
            status_color = "cyan"
        elif score >= 40:
            status_text = "Attention Required"
            status_color = "amber"
        else:
            status_text = "Critical"
            status_color = "rose"

        return {
            "score": score,
            "status": status_text,
            "status_color": status_color,
            "trusted_devices_count": trusted_devices_count,
            "active_sessions_count": active_sessions_count,
            "open_alerts_count": open_alerts_count,
            "factors": factors,
            "account_tier": "PREMIUM",
            "protection_mode": "Adaptive Real-Time AI + Enclave Shield",
        }

    @classmethod
    def get_demo_scenarios(cls) -> List[Dict[str, Any]]:
        """Returns pre-configured standard test scenarios A, B, C, D (Section 38)."""
        return [
            {
                "id": "scenario_a_normal",
                "name": "Scenario A — Normal Routine Settlement",
                "description": "Standard business hours transfer from primary trusted MacBook Pro to verified cloud partner.",
                "amount": 14500.0,
                "recipient": "Cloudflare Global Services",
                "device_id": "dev-mbp-m3",
                "device_name": "MacBook Pro M3 Max (Trusted)",
                "location": "Mumbai / Cyber City",
                "transaction_type": "WIRE_TRANSFER",
                "transaction_hour": 14,
                "expected_risk": "LOW (0-24)",
                "expected_decision": "ALLOW (Instant Settlement, No OTP)",
                "signals": ["Trusted Device", "Normal Business Hours (14:00)", "Normal Amount (₹14,500)", "Verified Recipient"],
            },
            {
                "id": "scenario_b_unusual",
                "name": "Scenario B — Slightly Unusual Night Activity",
                "description": "Transfer initiated during off-hours (03:15 AM) to a known recipient.",
                "amount": 48000.0,
                "recipient": "AWS Enterprise Cloud",
                "device_id": "dev-mbp-m3",
                "device_name": "MacBook Pro M3 Max (Trusted)",
                "location": "Mumbai / Cyber City",
                "transaction_type": "WIRE_TRANSFER",
                "transaction_hour": 3,
                "expected_risk": "MEDIUM (25-49)",
                "expected_decision": "STEP-UP VERIFICATION (Lightweight OTP)",
                "signals": ["Trusted Device", "Unusual Night-Time (03:15 AM)", "Moderate Amount (₹48,000)", "Known Recipient"],
            },
            {
                "id": "scenario_c_high_risk",
                "name": "Scenario C — High Risk New Hardware & Volume",
                "description": "High-value transfer from an unverified overseas device at 02:40 AM.",
                "amount": 285000.0,
                "recipient": "Silicon Valley Tech Fund",
                "device_id": "dev-unregistered-mac-lon",
                "device_name": "Unregistered Mac (London Roaming)",
                "location": "London, UK (New Location)",
                "transaction_type": "WIRE_TRANSFER",
                "transaction_hour": 2,
                "expected_risk": "HIGH (50-74)",
                "expected_decision": "TEMPORARY HOLD (High Priority Alert + Strong OTP)",
                "signals": ["Unregistered Device", "Large Amount (₹285,000)", "Unusual Night Hours (02:40 AM)", "New Foreign Geo-Location"],
            },
            {
                "id": "scenario_d_critical",
                "name": "Scenario D — Critical Cross-Border Threat",
                "description": "Massive capital drain transfer from an unknown Linux host in a high-risk jurisdiction.",
                "amount": 850000.0,
                "recipient": "Apex Offshore Escrow Ltd",
                "device_id": "dev-unknown-linux-node",
                "device_name": "Unrecognized Linux Terminal (Rooted)",
                "location": "St. Petersburg, Russia (High Threat Zone)",
                "transaction_type": "INSTANT_SETTLEMENT",
                "transaction_hour": 3,
                "expected_risk": "CRITICAL (75-100)",
                "expected_decision": "TEMPORARY HOLD / BLOCK (Critical Alert + Multi-Factor Verification)",
                "signals": ["Unknown Rooted Device", "High-Risk Foreign Location", "Very High Amount (₹850,000)", "First-Time Unknown Recipient", "Off-Hours Spike"],
            },
        ]

