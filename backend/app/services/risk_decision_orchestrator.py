"""Authoritative Risk Decision Orchestrator, Pre-Authorization Gatekeeper, and Approval Lifecycle Engine.

Coordinates:
  1. Idempotency verification and replay
  2. Customer balance sufficiency check
  3. Real customer historical behavior profiling, device & beneficiary resolution
  4. Model inference with champion artifact caching
  5. Local SHAP attribution and structured explanation generation
  6. Centralized deterministic rule engine evaluation
  7. Independent risk scoring (0-100 metric strictly separated from ML probability)
  8. Gatekeeper decisioning (ALLOW / REVIEW / BLOCK)
  9. Approval challenge creation on REVIEW (PENDING_APPROVAL / PENDING_VERIFICATION)
  10. Simulated balance management and secure user step-up approval/rejection lifecycle
  11. Comprehensive audit trail logging & WebSocket broadcasting
"""

import json
import random
import time
import uuid
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Tuple
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from backend.app.models.user import User
from backend.app.models.customer import Customer
from backend.app.models.transaction import Transaction
from backend.app.models.investigation import Investigation
from backend.app.models.shap_explanation import ShapExplanation
from backend.app.models.audit_log import AuditLog
from backend.app.models.beneficiary import Beneficiary
from backend.app.models.device import CustomerDevice
from backend.app.models.approval import TransactionApproval, ApprovalStatus
from backend.app.models.payment_intent import PaymentIntent, PaymentAttempt, PaymentLifecycleStatus
from backend.app.providers.base import ProviderPaymentRequest, ProviderPaymentStatus
from backend.app.providers.factory import PaymentProviderFactory
from backend.app.schemas.payment import (
    PaymentInitiateRequest,
    PreAuthDecisionResult,
    PaymentDecision,
    RiskLevelEnum,
    TriggeredRule,
    RiskFactorExplanation,
    StructuredShapFactor,
    ApprovalDetailResponse,
)
from backend.app.services.behavior_profile_service import BehaviorProfileService, DerivedPreAuthFeatures
from backend.app.services.feature_registry import FeatureRegistry
from backend.app.services.idempotency_service import IdempotencyService
from backend.app.services.prediction_service import FraudPredictionService
from backend.app.services.risk_scoring_service import RiskScoringEngine
from backend.app.services.rule_engine import RuleEngine, RuleActionImpact
from backend.app.services.state_transition_validator import StateTransitionValidator


class RiskDecisionOrchestrator:
    """Authoritative service orchestrating pre-authorization risk decisions, approvals, and payment execution."""

    @classmethod
    def _ensure_customer(cls, db: Session, customer_id: str, account_age_days: Optional[float] = None) -> Customer:
        """Fetch or create customer entity with default simulated wallet balance."""
        customer = db.query(Customer).filter(Customer.customer_id == customer_id).first()
        if not customer:
            customer = Customer(
                customer_id=customer_id,
                account_age_days=int(account_age_days) if account_age_days is not None else 30,
                simulated_balance=1500000.0,
                currency="INR",
            )
            db.add(customer)
            db.flush()
        return customer

    @classmethod
    def evaluate_and_process_payment(
        cls,
        db: Session,
        request: PaymentInitiateRequest,
        current_user: Optional[User] = None,
        idempotency_key: Optional[str] = None,
        provider_name: str = "sandbox_gateway",
    ) -> PreAuthDecisionResult:
        """Execute the end-to-end pre-authorization evaluation and payment simulation lifecycle."""
        start_time = time.perf_counter()
        effective_idempotency_key = idempotency_key or request.idempotency_key
        request_dict = request.model_dump()

        # -----------------------------------------------------------------
        # STEP 1: Idempotency Check
        # -----------------------------------------------------------------
        if effective_idempotency_key:
            cached_record, is_duplicate = IdempotencyService.check_idempotency(
                db=db,
                idempotency_key=effective_idempotency_key,
                request_payload=request_dict,
            )
            if is_duplicate and cached_record:
                cached_data = json.loads(cached_record.response_json)
                cached_data["idempotent_replay"] = True
                return PreAuthDecisionResult(**cached_data)

        # -----------------------------------------------------------------
        # STEP 2: Customer Balance Verification (Simulated Wallet Protection)
        # -----------------------------------------------------------------
        customer = cls._ensure_customer(db, request.customer_id, request.account_age_days)
        balance_before = float(customer.simulated_balance or 0.0)

        if balance_before < request.amount and (request.customer_id.startswith("CUST-SIM-") or balance_before <= 0):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient funds in simulated wallet: Available {customer.currency} {balance_before:.2f}, Requested {request.currency} {request.amount:.2f}",
            )

        # -----------------------------------------------------------------
        # STEP 3: Customer Behavioral Intelligence & Novelty Signals
        # -----------------------------------------------------------------
        from backend.app.services.behavior_intelligence_service import CustomerBehaviourIntelligenceService
        from backend.app.services.device_session_service import DeviceSessionRiskService
        from backend.app.services.network_intelligence_service import FraudNetworkIntelligenceService

        target_beneficiary = (request.beneficiary_name or request.merchant_name or "").strip()

        beh_report = CustomerBehaviourIntelligenceService.evaluate_behavior(
            db=db,
            customer_id=request.customer_id,
            amount=request.amount,
            merchant_name=target_beneficiary,
            merchant_category=request.merchant_category,
            device_type=request.device_type,
            location=request.location,
            transaction_country=request.transaction_country,
            transaction_type=request.transaction_type,
            failed_attempts=request.failed_attempts,
            current_timestamp=datetime.now(timezone.utc),
        )

        dev_assessment = DeviceSessionRiskService.evaluate_device_session(
            db=db,
            customer_id=request.customer_id,
            device_type=request.device_type,
            failed_attempts=request.failed_attempts,
            channel=request.transaction_type,
            current_timestamp=datetime.now(timezone.utc),
        )

        net_report = FraudNetworkIntelligenceService.evaluate_network_risk(
            db=db,
            customer_id=request.customer_id,
            device_type=request.device_type,
            merchant_name=target_beneficiary,
            amount=request.amount,
        )

        pre_auth_features: DerivedPreAuthFeatures = BehaviorProfileService.derive_pre_auth_features(
            db=db,
            customer_id=request.customer_id,
            amount=request.amount,
            merchant_category=request.merchant_category,
            device_type=request.device_type,
            location=request.location,
            transaction_country=request.transaction_country,
            transaction_type=request.transaction_type,
            failed_attempts=request.failed_attempts,
            beneficiary_name=request.beneficiary_name,
            merchant_name=request.merchant_name,
            current_timestamp=datetime.now(timezone.utc),
        )

        # -----------------------------------------------------------------
        # STEP 4: Feature Availability Enforcement (Anti-Leakage Control)
        # -----------------------------------------------------------------
        raw_feature_dict = pre_auth_features.to_dict()
        safe_features = FeatureRegistry.validate_and_filter_pre_auth_features(raw_feature_dict)

        # -----------------------------------------------------------------
        # STEP 5: Hardened ML Inference
        # -----------------------------------------------------------------
        pred_service = FraudPredictionService.get_instance()
        model_name = pred_service.model_name
        model_version = pred_service.model_version

        model_input_dict = {
            "Amount": request.amount,
            "Average_Previous_Amount": pre_auth_features.historical_avg_amount,
            "Amount_to_Average_Ratio": pre_auth_features.amount_ratio,
            "Transaction_Hour": pre_auth_features.transaction_hour,
            "Account_Age_Days": pre_auth_features.account_age_days,
            "Velocity_1h": pre_auth_features.velocity_1h,
            "Velocity_24h": pre_auth_features.velocity_24h,
            "Failed_Attempts_Count": pre_auth_features.failed_attempts,
            "Is_New_Device": int(pre_auth_features.is_new_device),
            "Is_New_Beneficiary": int(pre_auth_features.is_new_beneficiary),
            "Is_Unusual_Location": int(pre_auth_features.is_unusual_location),
            "Is_International": int(pre_auth_features.is_international),
            "Is_Night_Transaction": int(pre_auth_features.is_night_transaction),
            "Merchant_Category": request.merchant_category,
            "Device_Type": request.device_type,
            "Transaction_Type": request.transaction_type,
            "Transaction_Country": request.transaction_country,
            "Geo_Location_Region": request.location,
        }

        X_proc = None
        enriched_dict = model_input_dict

        try:
            if pred_service.is_ready and pred_service.preprocessor and pred_service.model:
                input_df, enriched_dict = pred_service._prepare_row_df(model_input_dict)
                X_proc = pred_service.preprocessor.transform(input_df)
                if hasattr(pred_service.model, "predict_proba"):
                    proba_arr = pred_service.model.predict_proba(X_proc)
                    ml_prob = float(proba_arr[0][1])
                else:
                    ml_prob = float(pred_service.model.predict(X_proc)[0])
            else:
                base_prob = min(0.95, (request.amount / 10000.0) * 0.5)
                ml_prob = base_prob + (0.3 if pre_auth_features.is_new_device else 0.0)
        except Exception as exc:
            import logging
            logging.getLogger("fraudlens.orchestrator").warning("ML inference exception in orchestrator: %s", exc)
            ml_prob = min(0.95, (request.amount / 10000.0) * 0.5) + (0.3 if pre_auth_features.is_new_device else 0.0)

        ml_prob = min(1.0, max(0.0, float(ml_prob)))

        # -----------------------------------------------------------------
        # STEP 6: SHAP Local Attribution
        # -----------------------------------------------------------------
        structured_shap: List[StructuredShapFactor] = []
        shap_status = "EXPLANATION_UNAVAILABLE"
        explanation_id = None

        if pred_service.is_ready and pred_service.shap_explainer and X_proc is not None:
            try:
                local_exp = pred_service.shap_explainer.explain_local(
                    X_processed=X_proc,
                    feature_dict=enriched_dict,
                    prediction=1 if ml_prob >= pred_service.threshold else 0,
                    probability=ml_prob,
                )
                explanation_id = local_exp.explanation_id
                shap_status = "COMPUTED"

                for item in (local_exp.top_positive_factors or [])[:3]:
                    val = model_input_dict.get(item.feature, "N/A")
                    structured_shap.append(StructuredShapFactor(
                        feature=item.feature,
                        raw_value=val,
                        contribution=round(float(item.attribution_value), 4),
                        direction="INCREASES_RISK",
                        severity="HIGH" if abs(item.attribution_value) > 0.2 else "MEDIUM",
                        human_interpretation=f"The factor '{item.feature}' ({val}) increased fraud risk by {abs(item.attribution_value)*100:.1f}%.",
                    ))
                for item in (local_exp.top_negative_factors or [])[:2]:
                    val = model_input_dict.get(item.feature, "N/A")
                    structured_shap.append(StructuredShapFactor(
                        feature=item.feature,
                        raw_value=val,
                        contribution=round(float(item.attribution_value), 4),
                        direction="DECREASES_RISK",
                        severity="LOW",
                        human_interpretation=f"Consistent baseline for '{item.feature}' reduced transaction risk.",
                    ))

                shap_record = ShapExplanation(
                    explanation_id=local_exp.explanation_id,
                    transaction_id=None,
                    model_name=pred_service.model_name,
                    model_version=pred_service.model_version,
                    base_value=float(local_exp.base_value),
                    prediction_value=float(local_exp.prediction_value),
                    feature_names_json=json.dumps(local_exp.feature_names),
                    feature_values_json=json.dumps(local_exp.feature_values),
                    shap_values_json=json.dumps(local_exp.shap_values),
                )
                db.add(shap_record)
            except Exception:
                shap_status = "EXPLANATION_UNAVAILABLE"

        # -----------------------------------------------------------------
        # STEP 7: Centralized Rule Engine Evaluation
        # -----------------------------------------------------------------
        rule_result = RuleEngine.evaluate(
            features=pre_auth_features,
            payment_method=request.payment_method,
            merchant_name=target_beneficiary,
            ml_fraud_prob=ml_prob,
        )

        triggered_rule_dtos = [
            TriggeredRule(
                rule_id=r.rule_id,
                rule_name=r.rule_name,
                severity=r.severity.value,
                description=r.reason,
                action_impact=r.action_impact.value,
            )
            for r in rule_result.triggered_rules
        ]

        # -----------------------------------------------------------------
        # STEP 8: Independent Multi-Factor Risk Scoring & Decision
        # -----------------------------------------------------------------
        risk_calc = RiskScoringEngine()
        risk_result = risk_calc.compute_risk_score(
            fraud_probability=ml_prob,
            transaction_data=model_input_dict,
        )
        base_score = risk_result.risk_score

        if dev_assessment.is_spoofed_environment or "KNOWN_FRAUD_RING_LINK" in net_report.cluster_indicators:
            final_risk_score = max(base_score, 85)
        elif rule_result.hard_block:
            final_risk_score = max(base_score, 82)
        elif rule_result.recommended_action == RuleActionImpact.FLAG_REVIEW or dev_assessment.combined_hardware_score >= 60 or net_report.network_risk_score >= 50:
            final_risk_score = min(68, max(base_score, 45))
        else:
            final_risk_score = base_score

        final_risk_score = min(100, max(0, int(round(final_risk_score))))

        # Decision classification
        tx_id = f"PAY-{uuid.uuid4().hex[:12].upper()}"
        case_id = None
        approval_id = None
        generated_otp = None
        verification_required = False
        balance_after = balance_before

        if rule_result.hard_block or dev_assessment.is_spoofed_environment or final_risk_score >= 85:
            decision = PaymentDecision.BLOCK
            risk_level = RiskLevelEnum.HIGH
            lifecycle_status = PaymentLifecycleStatus.BLOCKED
            status_message = "Transaction prohibited and blocked due to critical risk signals."
            balance_after = balance_before  # No deduction on block
        elif rule_result.recommended_action == RuleActionImpact.FLAG_REVIEW or final_risk_score >= 31:
            decision = PaymentDecision.REVIEW
            risk_level = RiskLevelEnum.MEDIUM if final_risk_score <= 70 else RiskLevelEnum.HIGH
            lifecycle_status = PaymentLifecycleStatus.REVIEW_REQUIRED
            status_message = "Transaction flagged for step-up verification / user confirmation."
            verification_required = True
            balance_after = balance_before  # No deduction until approved
            
            # Create Approval record with dynamic 6-digit numeric OTP
            approval_id = f"APP-{uuid.uuid4().hex[:10].upper()}"
            generated_otp = f"{random.randint(100000, 999999)}"
            approval_rec = TransactionApproval(
                approval_id=approval_id,
                payment_id=tx_id,
                transaction_id=tx_id,
                customer_id=request.customer_id,
                user_id=current_user.id if current_user else None,
                status=ApprovalStatus.PENDING.value,
                amount=request.amount,
                currency=request.currency,
                risk_score=final_risk_score,
                risk_level=risk_level.value,
                fraud_probability=round(ml_prob, 4),
                challenge_type="SMS_OTP",
                verification_token=generated_otp,
                notes=f"Flagged for {risk_level.value} risk review. Score: {final_risk_score}/100. Generated OTP: {generated_otp}",
                expires_at=datetime.now(timezone.utc) + timedelta(minutes=15),
            )
            db.add(approval_rec)

            case_id = f"CASE-{uuid.uuid4().hex[:8].upper()}"
            investigation = Investigation(
                case_id=case_id,
                transaction_id=tx_id,
                investigator_id=None,
                status="open",
                decision=None,
                notes=(
                    f"Auto-flagged transaction review. Risk Score: {final_risk_score}/100, "
                    f"ML Probability: {ml_prob:.4f}. Triggered: {', '.join(rule_result.rule_summary_reasons) or 'Elevated Risk Score'}."
                ),
            )
            db.add(investigation)
        else:
            decision = PaymentDecision.ALLOW
            risk_level = RiskLevelEnum.LOW
            lifecycle_status = PaymentLifecycleStatus.SUCCEEDED
            status_message = "Payment pre-authorized successfully. Transaction verified, authorized, and completed."
            
            # Deduct simulated balance immediately on successful low-risk transaction
            customer.simulated_balance = max(0.0, balance_before - request.amount)
            balance_after = customer.simulated_balance

            # Auto-learn beneficiary if not recorded
            if target_beneficiary:
                existing_bene = db.query(Beneficiary).filter(
                    Beneficiary.customer_id == request.customer_id,
                    Beneficiary.beneficiary_name == target_beneficiary,
                ).first()
                if not existing_bene:
                    new_bene = Beneficiary(
                        customer_id=request.customer_id,
                        beneficiary_name=target_beneficiary,
                        category=request.merchant_category,
                        is_trusted=True,
                    )
                    db.add(new_bene)
                else:
                    existing_bene.total_transfers = (existing_bene.total_transfers or 1) + 1
                    existing_bene.last_used_at = datetime.now(timezone.utc)

            # Auto-learn device if not recorded
            if request.device_type:
                existing_dev = db.query(CustomerDevice).filter(
                    CustomerDevice.customer_id == request.customer_id,
                    CustomerDevice.device_type == request.device_type,
                ).first()
                if not existing_dev:
                    new_dev = CustomerDevice(
                        customer_id=request.customer_id,
                        device_identifier=f"dev-{request.device_type}-{uuid.uuid4().hex[:6]}",
                        device_type=request.device_type,
                        location_region=request.location,
                        is_trusted=True,
                    )
                    db.add(new_dev)

        # Risk factor explanations
        top_factors = [
            RiskFactorExplanation(
                factor=f.factor,
                impact_score=f.impact_score,
                severity=f.severity,
                detail=f.detail,
            )
            for f in risk_result.risk_factors
        ]

        # -----------------------------------------------------------------
        # STEP 9: Safe Provider Sandbox Submission (if ALLOW)
        # -----------------------------------------------------------------
        provider_res = None
        ext_payment_id = None
        provider_status_str = None

        if decision == PaymentDecision.ALLOW:
            adapter = PaymentProviderFactory.get_provider(provider_name)
            prov_req = ProviderPaymentRequest(
                internal_payment_id=tx_id,
                customer_id=request.customer_id,
                amount=request.amount,
                currency=request.currency,
                payment_method=request.payment_method,
                merchant_name=target_beneficiary,
                idempotency_key=effective_idempotency_key or tx_id,
            )
            provider_res = adapter.create_payment(prov_req)
            ext_payment_id = provider_res.external_payment_id
            provider_status_str = provider_res.provider_status.value

        # -----------------------------------------------------------------
        # STEP 10: Persist PaymentIntent, Transaction & Audit Logs
        # -----------------------------------------------------------------
        payment_intent = PaymentIntent(
            payment_id=tx_id,
            customer_id=request.customer_id,
            amount=request.amount,
            currency=request.currency,
            merchant_name=target_beneficiary,
            merchant_category=request.merchant_category,
            payment_method=request.payment_method,
            beneficiary_name=request.beneficiary_name or target_beneficiary,
            lifecycle_status=lifecycle_status.value,
            is_new_beneficiary=pre_auth_features.is_new_beneficiary,
            is_new_device=pre_auth_features.is_new_device,
            fraud_probability=round(ml_prob, 4),
            risk_score=final_risk_score,
            risk_level=risk_level.value,
            fraud_decision=decision.value,
            behaviour_deviation_score=round(pre_auth_features.behaviour_deviation_score, 4),
            is_cold_start=pre_auth_features.is_cold_start,
            model_version=f"{model_name}_{model_version}",
            explanation_id=explanation_id,
            provider_name=provider_name,
            external_payment_id=ext_payment_id,
            idempotency_key=effective_idempotency_key,
            case_id=case_id,
            approval_id=approval_id,
        )
        db.add(payment_intent)

        if provider_res:
            attempt = PaymentAttempt(
                payment_id=tx_id,
                attempt_number=1,
                provider_name=provider_name,
                external_payment_id=ext_payment_id,
                status=provider_status_str or "SUCCEEDED",
                raw_response=json.dumps(provider_res.raw_response),
            )
            db.add(attempt)

        # Mirror record in transactions table
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
            beneficiary=request.beneficiary_name or target_beneficiary,
            status="SUCCESS" if decision == PaymentDecision.ALLOW else ("PENDING_VERIFICATION" if decision == PaymentDecision.REVIEW else "BLOCKED"),
            approval_id=approval_id,
            is_new_beneficiary=pre_auth_features.is_new_beneficiary,
            is_new_device=pre_auth_features.is_new_device,
            fraud_probability=round(ml_prob, 4),
            prediction=1 if decision == PaymentDecision.BLOCK else 0,
            risk_score=float(final_risk_score),
            risk_level=risk_level.value,
        )
        db.add(db_tx)

        # Audit events
        user_id = current_user.id if current_user else None
        audit_events = [
            AuditLog(
                user_id=user_id,
                action="TRANSACTION_CREATED",
                resource_type="transaction",
                resource_id=tx_id,
                details=json.dumps({
                    "amount": request.amount,
                    "currency": request.currency,
                    "customer_id": request.customer_id,
                    "beneficiary": target_beneficiary,
                    "is_new_beneficiary": pre_auth_features.is_new_beneficiary,
                    "is_new_device": pre_auth_features.is_new_device,
                }),
            ),
            AuditLog(
                user_id=user_id,
                action="RISK_EVALUATED",
                resource_type="transaction",
                resource_id=tx_id,
                details=json.dumps({
                    "risk_score": final_risk_score,
                    "risk_level": risk_level.value,
                    "fraud_probability": round(ml_prob, 4),
                    "decision": decision.value,
                    "lifecycle_status": lifecycle_status.value,
                }),
            ),
        ]

        if decision == PaymentDecision.ALLOW:
            audit_events.append(AuditLog(
                user_id=user_id,
                action="SIMULATED_BALANCE_DEDUCTED",
                resource_type="customer_wallet",
                resource_id=request.customer_id,
                details=json.dumps({"deducted": request.amount, "balance_before": balance_before, "balance_after": balance_after}),
            ))
        elif decision == PaymentDecision.REVIEW:
            audit_events.append(AuditLog(
                user_id=user_id,
                action="VERIFICATION_REQUIRED",
                resource_type="approval",
                resource_id=approval_id,
                details=json.dumps({"payment_id": tx_id, "risk_score": final_risk_score}),
            ))

        db.add_all(audit_events)
        db.commit()

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        decision_result = PreAuthDecisionResult(
            transaction_id=tx_id,
            payment_id=tx_id,
            customer_id=request.customer_id,
            amount=request.amount,
            currency=request.currency,
            fraud_probability=round(ml_prob, 4),
            risk_score=final_risk_score,
            risk_level=risk_level,
            decision=decision,
            lifecycle_status=lifecycle_status.value,
            triggered_rules=triggered_rule_dtos,
            top_risk_factors=top_factors,
            structured_explanations=structured_shap,
            shap_status=shap_status,
            explanation_id=explanation_id,
            case_id=case_id,
            approval_id=approval_id,
            otp_code=generated_otp,
            verification_required=verification_required,
            is_new_beneficiary=pre_auth_features.is_new_beneficiary,
            is_new_device=pre_auth_features.is_new_device,
            simulated_balance_before=balance_before,
            simulated_balance_after=balance_after,
            external_payment_id=ext_payment_id,
            provider_name=provider_name,
            provider_status=provider_status_str,
            idempotency_key=effective_idempotency_key,
            idempotent_replay=False,
            behavioural_deviation_score=round(pre_auth_features.behaviour_deviation_score, 4),
            is_cold_start=pre_auth_features.is_cold_start,
            model_name=model_name,
            model_version=model_version,
            processing_time_ms=round(elapsed_ms, 2),
            ready_for_provider=(decision == PaymentDecision.ALLOW),
            status_message=status_message,
            device_risk_score=dev_assessment.combined_hardware_score,
            session_risk_score=dev_assessment.session_risk_score,
            network_risk_score=net_report.network_risk_score,
            connected_entities_count=net_report.connected_entity_count,
            behaviour_intelligence=beh_report.to_dict(),
            device_session_intelligence=dev_assessment.to_dict(),
            network_intelligence=net_report.to_dict(),
        )

        # -----------------------------------------------------------------
        # STEP 11: Idempotency Storage & Live Event Broadcasting
        # -----------------------------------------------------------------
        if effective_idempotency_key:
            IdempotencyService.store_idempotency(
                db=db,
                idempotency_key=effective_idempotency_key,
                request_payload=request_dict,
                resource_id=tx_id,
                status_code=200,
                response_data=decision_result.model_dump(),
            )

        from backend.app.services.event_broadcaster import EventBroadcaster
        EventBroadcaster.get_instance().sync_broadcast("payment.evaluated", {
            "payment_id": tx_id,
            "customer_id": request.customer_id,
            "amount": request.amount,
            "currency": request.currency,
            "decision": decision.value,
            "risk_score": final_risk_score,
            "risk_level": risk_level.value,
            "fraud_probability": round(ml_prob, 4),
            "lifecycle_status": lifecycle_status.value,
            "approval_id": approval_id,
            "verification_required": verification_required,
            "simulated_balance": balance_after,
            "processing_time_ms": round(elapsed_ms, 2),
        })

        return decision_result

    @classmethod
    def process_approval_action(
        cls,
        db: Session,
        approval_id: str,
        action: str,
        current_user: Optional[User] = None,
        notes: Optional[str] = None,
        challenge_response: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Execute user step-up approval / rejection / expiration workflow."""
        action_clean = action.upper().strip()
        if action_clean not in ("APPROVE", "REJECT", "EXPIRE"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid approval action '{action}'. Permissible actions: 'APPROVE', 'REJECT', 'EXPIRE'.",
            )

        approval = db.query(TransactionApproval).filter(TransactionApproval.approval_id == approval_id).first()
        if not approval:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Approval challenge '{approval_id}' not found.",
            )

        # Check authorization: non-investigators can only act on their own approvals
        if current_user and current_user.role not in ("ADMIN", "FRAUD_INVESTIGATOR"):
            is_authorized = False
            if approval.user_id is not None and approval.user_id == current_user.id:
                is_authorized = True
            elif approval.customer_id:
                cust_match = (
                    approval.customer_id == str(current_user.id)
                    or approval.customer_id == current_user.email
                    or approval.customer_id == f"CUST-{current_user.id:04d}"
                )
                if not cust_match:
                    cust_obj = db.query(Customer).filter(Customer.customer_id == approval.customer_id).first()
                    if cust_obj and cust_obj.email and cust_obj.email.lower() == current_user.email.lower():
                        cust_match = True
                if cust_match:
                    is_authorized = True
            if not is_authorized:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You are not authorized to take action on this approval challenge.",
                )


        if approval.status != ApprovalStatus.PENDING.value:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Approval '{approval_id}' has already been resolved with status '{approval.status}'. Replay prevented.",
            )

        now = datetime.now(timezone.utc)
        expires_at = approval.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)

        # Check expiration
        if action_clean != "EXPIRE" and now > expires_at:
            approval.status = ApprovalStatus.EXPIRED.value
            approval.responded_at = now
            if approval.payment_id:
                pi = db.query(PaymentIntent).filter(PaymentIntent.payment_id == approval.payment_id).first()
                if pi:
                    pi.lifecycle_status = PaymentLifecycleStatus.EXPIRED.value
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_410_GONE,
                detail="Verification request has expired. Transaction cancelled.",
            )

        customer = db.query(Customer).filter(Customer.customer_id == approval.customer_id).first()
        tx = db.query(Transaction).filter(Transaction.transaction_id == approval.transaction_id).first() if approval.transaction_id else None
        pi = db.query(PaymentIntent).filter(PaymentIntent.payment_id == approval.payment_id).first() if approval.payment_id else None

        user_id = current_user.id if current_user else approval.user_id

        if action_clean == "APPROVE":
            # Real OTP verification: If a challenge_response is provided or if approval has a token
            if approval.verification_token:
                if challenge_response:
                    if challenge_response.strip() != approval.verification_token.strip():
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Invalid OTP code! The entered code '{challenge_response}' does not match the 6-digit security OTP sent to your registered mobile phone.",
                        )
                elif current_user and current_user.role not in ("ADMIN", "FRAUD_INVESTIGATOR"):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="SMS OTP verification required. Please enter the 6-digit code received on your mobile device.",
                    )

            # Check balance sufficiency
            if customer and float(customer.simulated_balance or 0.0) < approval.amount:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Insufficient simulated wallet balance: Available ${customer.simulated_balance:.2f}, Required ${approval.amount:.2f}",
                )

            # Enforce state transition
            if pi:
                StateTransitionValidator.enforce_transition(pi.lifecycle_status, PaymentLifecycleStatus.APPROVED.value)
                pi.lifecycle_status = PaymentLifecycleStatus.SUCCEEDED.value

            approval.status = ApprovalStatus.APPROVED.value
            approval.responded_at = now
            approval.notes = notes or approval.notes

            if customer:
                customer.simulated_balance = max(0.0, float(customer.simulated_balance or 0.0) - approval.amount)

            if tx:
                tx.status = "SUCCESS"

            # Auto-save beneficiary as trusted
            if pi and pi.beneficiary_name:
                bene = db.query(Beneficiary).filter(
                    Beneficiary.customer_id == approval.customer_id,
                    Beneficiary.beneficiary_name == pi.beneficiary_name,
                ).first()
                if not bene:
                    db.add(Beneficiary(
                        customer_id=approval.customer_id,
                        beneficiary_name=pi.beneficiary_name,
                        category=pi.merchant_category or "transfer",
                        is_trusted=True,
                    ))

            # Audit events
            db.add(AuditLog(
                user_id=user_id,
                action="USER_VERIFICATION_APPROVED",
                resource_type="approval",
                resource_id=approval_id,
                details=json.dumps({"amount": approval.amount, "notes": notes}),
            ))
            db.add(AuditLog(
                user_id=user_id,
                action="SIMULATED_BALANCE_DEDUCTED",
                resource_type="customer_wallet",
                resource_id=approval.customer_id,
                details=json.dumps({"deducted": approval.amount, "new_balance": customer.simulated_balance if customer else None}),
            ))

            db.commit()

            from backend.app.services.event_broadcaster import EventBroadcaster
            EventBroadcaster.get_instance().sync_broadcast("payment.approved", {
                "approval_id": approval_id,
                "payment_id": approval.payment_id,
                "customer_id": approval.customer_id,
                "status": "APPROVED",
                "lifecycle_status": "SUCCEEDED",
                "simulated_balance": customer.simulated_balance if customer else None,
            })

            return {
                "approval_id": approval_id,
                "status": "APPROVED",
                "lifecycle_status": "SUCCEEDED",
                "payment_id": approval.payment_id,
                "amount": approval.amount,
                "simulated_balance": customer.simulated_balance if customer else None,
                "message": "Transaction step-up verification approved and completed.",
            }

        elif action_clean == "REJECT":
            if pi:
                StateTransitionValidator.enforce_transition(pi.lifecycle_status, PaymentLifecycleStatus.BLOCKED.value)
                pi.lifecycle_status = PaymentLifecycleStatus.BLOCKED.value

            approval.status = ApprovalStatus.REJECTED.value
            approval.responded_at = now
            approval.notes = notes or approval.notes

            if tx:
                tx.status = "BLOCKED"

            db.add(AuditLog(
                user_id=user_id,
                action="USER_VERIFICATION_REJECTED",
                resource_type="approval",
                resource_id=approval_id,
                details=json.dumps({"amount": approval.amount, "notes": notes}),
            ))

            db.commit()

            from backend.app.services.event_broadcaster import EventBroadcaster
            EventBroadcaster.get_instance().sync_broadcast("payment.rejected", {
                "approval_id": approval_id,
                "payment_id": approval.payment_id,
                "customer_id": approval.customer_id,
                "status": "REJECTED",
                "lifecycle_status": "BLOCKED",
            })

            return {
                "approval_id": approval_id,
                "status": "REJECTED",
                "lifecycle_status": "BLOCKED",
                "payment_id": approval.payment_id,
                "amount": approval.amount,
                "message": "Transaction rejected by user and permanently blocked.",
            }

        else:  # EXPIRE
            if pi:
                pi.lifecycle_status = PaymentLifecycleStatus.BLOCKED.value

            approval.status = ApprovalStatus.EXPIRED.value
            approval.responded_at = now

            if tx:
                tx.status = "BLOCKED"

            db.add(AuditLog(
                user_id=user_id,
                action="VERIFICATION_EXPIRED",
                resource_type="approval",
                resource_id=approval_id,
                details=json.dumps({"amount": approval.amount}),
            ))

            db.commit()

            return {
                "approval_id": approval_id,
                "status": "EXPIRED",
                "lifecycle_status": "BLOCKED",
                "payment_id": approval.payment_id,
                "amount": approval.amount,
                "message": "Verification challenge expired. Transaction blocked.",
            }
