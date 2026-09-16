"""Pre-Authorization Risk Engine Service (Phase 6).

Authoritative evaluation engine executing:
1. Signal Collection & Behavior Profile Integration
2. Pre-Auth Feature Engineering
3. ML Prediction (Fraud Probability)
4. Deterministic Rule & Velocity Evaluation
5. Multi-Factor Risk Score (0-100)
6. Final Gateway Decision (ALLOW / REVIEW / BLOCK)
"""

import time
import uuid
from typing import Any, Dict, List, Tuple
from sqlalchemy.orm import Session

from backend.app.schemas.payment import (
    PaymentInitiateRequest,
    PreAuthDecisionResult,
    PaymentDecision,
    RiskLevelEnum,
    TriggeredRule,
    RiskFactorExplanation,
)
from backend.app.schemas.prediction import TransactionPredictionInput
from backend.app.models.transaction import Transaction
from backend.app.models.customer import Customer
from backend.app.services.behavior_profile_service import BehaviorProfileService, DerivedPreAuthFeatures
from backend.app.services.prediction_service import FraudPredictionService
from backend.app.services.risk_scoring_service import RiskScoringEngine


class PreAuthRiskEngine:
    """Core pre-authorization fraud evaluation and decisioning service."""

    def __init__(self) -> None:
        self.risk_scoring_engine = RiskScoringEngine()

    def evaluate_pre_auth(
        self,
        db: Session,
        request: PaymentInitiateRequest,
    ) -> PreAuthDecisionResult:
        """Execute full pre-authorization pipeline and produce authoritative gateway decision."""
        start_time = time.perf_counter()
        tx_id = f"PAY-{uuid.uuid4().hex[:12].upper()}"

        # 1. Ensure customer record exists in DB
        cust = db.query(Customer).filter(Customer.customer_id == request.customer_id).first()
        if not cust:
            cust = Customer(
                customer_id=request.customer_id,
                account_age_days=int(request.account_age_days) if request.account_age_days is not None else 30,
            )
            db.add(cust)
            db.flush()

        # 2. Derive pre-authorization features using real database history
        pre_auth_features = BehaviorProfileService.derive_pre_auth_features(
            db=db,
            customer_id=request.customer_id,
            amount=request.amount,
            merchant_category=request.merchant_category,
            device_type=request.device_type,
            location=request.location,
            transaction_country=request.transaction_country,
            transaction_type=request.transaction_type,
            failed_attempts=request.failed_attempts,
        )

        # 3. Execute ML Prediction via FraudPredictionService
        prediction_service = FraudPredictionService.get_instance()

        # Build prediction input payload compatible with fitted pipeline
        tx_input = TransactionPredictionInput(
            transaction_id=tx_id,
            customer_id=request.customer_id,
            # Primary features
            Amount=request.amount,
            Transaction_Hour=pre_auth_features.transaction_hour,
            Transaction_Type=request.transaction_type,
            Device_Type=request.device_type,
            Location=request.location,
            Usual_Location=request.location if not pre_auth_features.is_unusual_location else "Primary Region",
            New_Device=1 if pre_auth_features.is_new_device else 0,
            Account_Age_Days=pre_auth_features.account_age_days,
            Previous_Transaction_Amount=pre_auth_features.historical_avg_amount,
            Average_Previous_Amount=pre_auth_features.historical_avg_amount,
            Amount_Deviation=pre_auth_features.amount_deviation,
            Amount_Ratio=pre_auth_features.amount_ratio,
            Transactions_Last_24H=float(pre_auth_features.velocity_24h),
            Failed_Attempts=request.failed_attempts,
            International_Transaction=1 if pre_auth_features.is_international else 0,
            Unusual_Location=1 if pre_auth_features.is_unusual_location else 0,
            # Legacy compatibility fields
            transaction_amount=request.amount,
            transaction_hour=pre_auth_features.transaction_hour,
            device_type=request.device_type,
            geo_location_region=request.location,
            transaction_type=request.transaction_type,
            account_age_days=pre_auth_features.account_age_days,
            avg_transaction_amount_30d_customer=pre_auth_features.historical_avg_amount,
            transaction_velocity_24h=float(pre_auth_features.velocity_24h),
            transaction_velocity_1h=float(pre_auth_features.velocity_1h),
            merchant_category=request.merchant_category,
            transaction_country=request.transaction_country,
            is_high_risk_merchant_category=1 if request.merchant_category.lower() in BehaviorProfileService.HIGH_RISK_CATEGORIES else 0,
            is_weekend=0,
            customer_total_transactions_30d=float(pre_auth_features.velocity_24h * 5),
        )

        ml_prob = 0.05
        model_name = "unknown"
        model_version = "v1.0.0"

        if prediction_service.is_ready:
            try:
                pred_out = prediction_service.predict_transaction(tx_input, include_shap_summary=False)
                ml_prob = pred_out.fraud_probability
                model_name = pred_out.model_name
                model_version = pred_out.model_version
            except Exception:
                ml_prob = 0.15

        # 4. Evaluate Deterministic Pre-Auth Rule Sets
        triggered_rules, rule_risk_points, hard_block = self._evaluate_rules(
            request=request,
            features=pre_auth_features,
            ml_prob=ml_prob,
        )

        # 5. Compute Holistic Risk Score (0-100) from RiskScoringEngine
        risk_result = self.risk_scoring_engine.compute_risk_score(
            fraud_probability=ml_prob,
            transaction_data={
                "Amount": request.amount,
                "Average_Previous_Amount": pre_auth_features.historical_avg_amount,
                "transaction_velocity_1h": pre_auth_features.velocity_1h,
                "Transactions_Last_24H": pre_auth_features.velocity_24h,
                "Failed_Attempts": request.failed_attempts,
                "Account_Age_Days": pre_auth_features.account_age_days,
                "International_Transaction": 1 if pre_auth_features.is_international else 0,
                "Unusual_Location": 1 if pre_auth_features.is_unusual_location else 0,
                "New_Device": 1 if pre_auth_features.is_new_device else 0,
                "is_high_risk_merchant_category": 1 if request.merchant_category.lower() in BehaviorProfileService.HIGH_RISK_CATEGORIES else 0,
                "Transaction_Hour": pre_auth_features.transaction_hour,
            },
        )

        base_score = risk_result.risk_score
        # Apply rule impact floors
        if hard_block:
            final_risk_score = max(base_score, 80)
        elif any(r.action_impact == "FLAG_REVIEW" for r in triggered_rules):
            final_risk_score = max(base_score, 40)
        else:
            final_risk_score = base_score

        final_risk_score = min(100, max(0, int(round(final_risk_score))))

        # 6. Authoritative Gateway Decision Mapping
        if hard_block or final_risk_score >= 71:
            decision = PaymentDecision.BLOCK
            risk_level = RiskLevelEnum.HIGH
            status_message = "Payment blocked due to high fraud risk indicators."
        elif final_risk_score >= 31:
            decision = PaymentDecision.REVIEW
            risk_level = RiskLevelEnum.MEDIUM
            status_message = "Payment flagged for secondary review / step-up verification."
        else:
            decision = PaymentDecision.ALLOW
            risk_level = RiskLevelEnum.LOW
            status_message = "Payment pre-authorized successfully. Ready for payment processor."

        # 7. Format Top Risk Factor Explanations
        top_factors = [
            RiskFactorExplanation(
                factor=f.factor,
                impact_score=f.impact_score,
                severity=f.severity,
                detail=f.detail,
            )
            for f in risk_result.risk_factors
        ]

        # 8. Persist Pre-Auth Record in DB for Tracking & Audit
        db_tx = Transaction(
            transaction_id=tx_id,
            customer_id=request.customer_id,
            amount=request.amount,
            transaction_hour=pre_auth_features.transaction_hour,
            merchant_category=request.merchant_category,
            transaction_country=request.transaction_country,
            geo_location_region=request.location,
            device_type=request.device_type,
            transaction_type=request.transaction_type,
            fraud_probability=round(ml_prob, 4),
            prediction=1 if decision == PaymentDecision.BLOCK else 0,
            risk_score=float(final_risk_score),
            risk_level=risk_level.value,
        )
        db.add(db_tx)
        db.commit()

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        return PreAuthDecisionResult(
            transaction_id=tx_id,
            customer_id=request.customer_id,
            amount=request.amount,
            currency=request.currency,
            fraud_probability=round(ml_prob, 4),
            risk_score=final_risk_score,
            risk_level=risk_level,
            decision=decision,
            triggered_rules=triggered_rules,
            top_risk_factors=top_factors,
            behavioural_deviation_score=round(pre_auth_features.behaviour_deviation_score, 4),
            is_cold_start=pre_auth_features.is_cold_start,
            model_name=model_name,
            model_version=model_version,
            processing_time_ms=round(elapsed_ms, 2),
            ready_for_provider=(decision == PaymentDecision.ALLOW),
            status_message=status_message,
        )

    def _evaluate_rules(
        self,
        request: PaymentInitiateRequest,
        features: DerivedPreAuthFeatures,
        ml_prob: float,
    ) -> Tuple[List[TriggeredRule], int, bool]:
        """Evaluate deterministic security and velocity rules."""
        rules: List[TriggeredRule] = []
        extra_pts = 0
        hard_block = False

        # Rule 1: High Velocity Burst in 1 Hour
        if features.velocity_1h >= 5:
            rules.append(TriggeredRule(
                rule_id="RULE-VEL-01",
                rule_name="Critical Velocity Burst (1 Hour)",
                severity="CRITICAL",
                description=f"Customer executed {features.velocity_1h} transactions within 1 hour.",
                action_impact="ENFORCE_BLOCK",
            ))
            extra_pts += 25
            hard_block = True
        elif features.velocity_1h >= 3:
            rules.append(TriggeredRule(
                rule_id="RULE-VEL-02",
                rule_name="Elevated Velocity Acceleration",
                severity="HIGH",
                description=f"Customer executed {features.velocity_1h} transactions in 1 hour.",
                action_impact="FLAG_REVIEW",
            ))
            extra_pts += 15

        # Rule 2: Extreme Amount Surge (>4x Historical Baseline or >$5,000 on Non-Cold-Start)
        if ((features.amount_ratio >= 4.0 and request.amount >= 1000.0) or (request.amount >= 5000.0 and features.amount_ratio >= 2.0)) and not features.is_cold_start:
            rules.append(TriggeredRule(
                rule_id="RULE-AMT-01",
                rule_name="Extreme Transaction Amount Spike",
                severity="HIGH",
                description=f"Amount (${request.amount:.2f}) is {features.amount_ratio:.1f}x higher than historical average (${features.historical_avg_amount:.2f}).",
                action_impact="ENFORCE_BLOCK" if request.amount >= 5000.0 else "FLAG_REVIEW",
            ))
            extra_pts += 25
            if request.amount >= 5000.0:
                hard_block = True

        # Rule 3: Account Takeover Pattern (New Device / Location + Amount Spike)
        if (features.is_new_device and features.is_unusual_location and features.amount_ratio >= 3.0) or \
           (request.amount >= 3000.0 and (features.is_new_device or features.is_unusual_location)) or \
           (features.amount_ratio >= 10.0 and (features.is_new_device or features.is_unusual_location)):
            rules.append(TriggeredRule(
                rule_id="RULE-ATO-01",
                rule_name="Critical Account Takeover Signature Pattern",
                severity="CRITICAL",
                description="Novel hardware device signature and geographic mismatch combined with severe monetary volume spike.",
                action_impact="ENFORCE_BLOCK",
            ))
            extra_pts += 30
            hard_block = True
        elif (features.is_new_device or features.is_unusual_location) and features.amount_ratio >= 2.0:
            rules.append(TriggeredRule(
                rule_id="RULE-ATO-02",
                rule_name="Unusual Device/Location with Elevated Amount",
                severity="MEDIUM",
                description="Transaction from a new device or unfamiliar location with an above-average transaction amount.",
                action_impact="FLAG_REVIEW",
            ))
            extra_pts += 15

        # Rule 4: Credential Stuffing / Brute Force Burst
        if request.failed_attempts >= 3:
            rules.append(TriggeredRule(
                rule_id="RULE-AUTH-01",
                rule_name="Preceding Authentication Failure Burst",
                severity="CRITICAL" if request.failed_attempts >= 3 else "HIGH",
                description=f"Detected {request.failed_attempts} repeated failed authentication attempts before checkout.",
                action_impact="ENFORCE_BLOCK",
            ))
            extra_pts += 25
            hard_block = True

        # Rule 5: High Risk Merchant Category (Crypto / Luxury) on elevated risk
        if request.merchant_category.lower() in BehaviorProfileService.HIGH_RISK_CATEGORIES:
            if request.amount >= 2000.0 or request.failed_attempts >= 2 or features.is_new_device:
                rules.append(TriggeredRule(
                    rule_id="RULE-CAT-01",
                    rule_name="High Risk Sector On Elevated Threat Profile",
                    severity="CRITICAL" if request.amount >= 5000.0 else "HIGH",
                    description=f"High risk merchant sector '{request.merchant_category}' combined with elevated threat signals.",
                    action_impact="ENFORCE_BLOCK" if request.amount >= 5000.0 else "FLAG_REVIEW",
                ))
                extra_pts += 20
                if request.amount >= 5000.0:
                    hard_block = True

        return rules, extra_pts, hard_block
