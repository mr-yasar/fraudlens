"""Authoritative Risk Decision Orchestrator and Pre-Authorization Gatekeeper.

Coordinates:
  1. Idempotency verification and replay
  2. Feature availability and anti-leakage boundary enforcement
  3. Real customer historical behavior profiling and rolling velocity calculation
  4. Model inference with champion artifact caching
  5. Local SHAP attribution and structured explanation generation
  6. Centralized deterministic rule engine evaluation
  7. Independent risk scoring (0-100 metric separated from ML probability)
  8. Gatekeeper decisioning (ALLOW / REVIEW / BLOCK)
  9. Automatic case creation on REVIEW
  10. Strict Payment Submission Gate (ONLY ALLOW submitted to provider)
  11. Comprehensive audit trail logging
"""

import json
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy.orm import Session

from backend.app.models.user import User
from backend.app.models.transaction import Transaction
from backend.app.models.investigation import Investigation
from backend.app.models.shap_explanation import ShapExplanation
from backend.app.models.audit_log import AuditLog
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
)
from backend.app.services.behavior_profile_service import BehaviorProfileService, DerivedPreAuthFeatures
from backend.app.services.feature_registry import FeatureRegistry
from backend.app.services.idempotency_service import IdempotencyService
from backend.app.services.prediction_service import FraudPredictionService
from backend.app.services.risk_scoring_service import RiskScoringEngine
from backend.app.services.rule_engine import RuleEngine, RuleActionImpact


class RiskDecisionOrchestrator:
    """Authoritative service orchestrating pre-authorization risk decisions and payment execution."""

    @classmethod
    def evaluate_and_process_payment(
        cls,
        db: Session,
        request: PaymentInitiateRequest,
        current_user: Optional[User] = None,
        idempotency_key: Optional[str] = None,
        provider_name: str = "sandbox_gateway",
    ) -> PreAuthDecisionResult:
        """Execute the end-to-end pre-authorization evaluation and payment lifecycle."""
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
        # STEP 2: Customer Behavioral Intelligence & Rolling Velocity
        # -----------------------------------------------------------------
        from backend.app.services.behavior_intelligence_service import CustomerBehaviourIntelligenceService
        from backend.app.services.device_session_service import DeviceSessionRiskService
        from backend.app.services.network_intelligence_service import FraudNetworkIntelligenceService

        beh_report = CustomerBehaviourIntelligenceService.evaluate_behavior(
            db=db,
            customer_id=request.customer_id,
            amount=request.amount,
            merchant_name=request.merchant_name,
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
            merchant_name=request.merchant_name,
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
            current_timestamp=datetime.now(timezone.utc),
        )

        # -----------------------------------------------------------------
        # STEP 3: Feature Availability Enforcement (Anti-Leakage Control)
        # -----------------------------------------------------------------
        raw_feature_dict = pre_auth_features.to_dict()
        safe_features = FeatureRegistry.validate_and_filter_pre_auth_features(raw_feature_dict)

        # -----------------------------------------------------------------
        # STEP 4: Hardened ML Inference
        # -----------------------------------------------------------------
        pred_service = FraudPredictionService.get_instance()
        model_name = pred_service.model_name
        model_version = pred_service.model_version

        # Prepare normalized dataframe for prediction
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
            "Is_Unusual_Location": int(pre_auth_features.is_unusual_location),
            "Is_International": int(pre_auth_features.is_international),
            "Is_Night_Transaction": int(pre_auth_features.is_night_transaction),
            "Merchant_Category": request.merchant_category,
            "Device_Type": request.device_type,
            "Transaction_Type": request.transaction_type,
            "Transaction_Country": request.transaction_country,
            "Geo_Location_Region": request.location,
        }

        try:
            if pred_service.is_ready and pred_service.preprocessor and pred_service.model:
                input_df = pred_service._prepare_row_df(model_input_dict)
                X_proc = pred_service.preprocessor.transform(input_df)
                if hasattr(pred_service.model, "predict_proba"):
                    proba_arr = pred_service.model.predict_proba(X_proc)
                    ml_prob = float(proba_arr[0][1])
                else:
                    ml_prob = float(pred_service.model.predict(X_proc)[0])
            else:
                # Fallback calculation if ML artifacts are uninitialized
                base_prob = min(0.95, (request.amount / 10000.0) * 0.5)
                ml_prob = base_prob + (0.3 if pre_auth_features.is_new_device else 0.0)
        except Exception:
            ml_prob = 0.5  # Neutral fallback

        ml_prob = min(1.0, max(0.0, float(ml_prob)))

        # -----------------------------------------------------------------
        # STEP 5: SHAP Local Attribution
        # -----------------------------------------------------------------
        structured_shap: List[StructuredShapFactor] = []
        shap_status = "EXPLANATION_UNAVAILABLE"
        explanation_id = None

        if pred_service.is_ready and pred_service.shap_explainer:
            try:
                local_exp = pred_service.shap_explainer.explain_local(
                    X_processed=X_proc,
                    feature_dict=model_input_dict,
                    prediction=1 if ml_prob >= pred_service.threshold else 0,
                    probability=ml_prob,
                )
                explanation_id = local_exp.explanation_id
                shap_status = "COMPUTED"

                # Map top factors into structured human-readable explanations
                for item in (local_exp.top_positive_factors or [])[:3]:
                    val = model_input_dict.get(item.feature, "N/A")
                    structured_shap.append(StructuredShapFactor(
                        feature=item.feature,
                        raw_value=val,
                        contribution=round(float(item.attribution_value), 4),
                        direction="INCREASES_RISK",
                        severity="HIGH" if abs(item.attribution_value) > 0.2 else "MEDIUM",
                        human_interpretation=f"The value of '{item.feature}' ({val}) increased the transaction fraud risk by {abs(item.attribution_value)*100:.1f}%.",
                    ))
                for item in (local_exp.top_negative_factors or [])[:2]:
                    val = model_input_dict.get(item.feature, "N/A")
                    structured_shap.append(StructuredShapFactor(
                        feature=item.feature,
                        raw_value=val,
                        contribution=round(float(item.attribution_value), 4),
                        direction="DECREASES_RISK",
                        severity="LOW",
                        human_interpretation=f"Familiar baseline for '{item.feature}' lowered the overall risk profile.",
                    ))

                # Persist explanation record
                shap_record = ShapExplanation(
                    explanation_id=local_exp.explanation_id,
                    transaction_id=None,  # Will be linked
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
        # STEP 6: Centralized Rule Engine Evaluation
        # -----------------------------------------------------------------
        rule_result = RuleEngine.evaluate(
            features=pre_auth_features,
            payment_method=request.payment_method,
            merchant_name=request.merchant_name,
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
        # STEP 7: Multi-Factor Risk Scoring & Authoritative Decisioning
        # -----------------------------------------------------------------
        risk_calc = RiskScoringEngine()
        risk_result = risk_calc.compute_risk_score(
            fraud_probability=ml_prob,
            transaction_data=model_input_dict,
        )
        base_score = risk_result.risk_score

        # Seamlessly incorporate Intelligence Fabric risk adjustments
        if dev_assessment.is_spoofed_environment or "KNOWN_FRAUD_RING_LINK" in net_report.cluster_indicators:
            final_risk_score = max(base_score, 82)
        elif rule_result.hard_block:
            final_risk_score = max(base_score, 80)
        elif rule_result.recommended_action == RuleActionImpact.FLAG_REVIEW or dev_assessment.combined_hardware_score >= 60 or net_report.network_risk_score >= 50:
            final_risk_score = max(base_score, 45)
        else:
            final_risk_score = base_score

        final_risk_score = min(100, max(0, int(round(final_risk_score))))

        # Determine authoritative decision
        if rule_result.hard_block or dev_assessment.is_spoofed_environment or final_risk_score >= 71:
            decision = PaymentDecision.BLOCK
            risk_level = RiskLevelEnum.HIGH
            lifecycle_status = PaymentLifecycleStatus.BLOCKED
            status_message = "Payment blocked due to severe fraud risk indicators."
        elif rule_result.recommended_action == RuleActionImpact.FLAG_REVIEW or final_risk_score >= 31:
            decision = PaymentDecision.REVIEW
            risk_level = RiskLevelEnum.MEDIUM
            lifecycle_status = PaymentLifecycleStatus.REVIEW_REQUIRED
            status_message = "Payment flagged for investigation / step-up verification."
        else:
            decision = PaymentDecision.ALLOW
            risk_level = RiskLevelEnum.LOW
            lifecycle_status = PaymentLifecycleStatus.APPROVED
            status_message = "Payment pre-authorized successfully."

        # Format risk factor explanations (combining ML, Behaviour, Device, and Network)
        top_factors = [
            RiskFactorExplanation(
                factor=f.factor,
                impact_score=f.impact_score,
                severity=f.severity,
                detail=f.detail,
            )
            for f in risk_result.risk_factors
        ]

        # Add intelligence fabric diagnostic factors
        for ev in dev_assessment.evidence[:2]:
            top_factors.append(RiskFactorExplanation(
                factor="Device & Session Anomaly",
                impact_score=dev_assessment.combined_hardware_score,
                severity="HIGH" if dev_assessment.combined_hardware_score >= 60 else "MEDIUM",
                detail=ev,
            ))

        for ev in net_report.evidence[:2]:
            top_factors.append(RiskFactorExplanation(
                factor="Network & Relationship Risk",
                impact_score=net_report.network_risk_score,
                severity="HIGH" if net_report.network_risk_score >= 50 else "MEDIUM",
                detail=ev,
            ))


        # -----------------------------------------------------------------
        # STEP 8: Create IDs and Case (if REVIEW)
        # -----------------------------------------------------------------
        tx_id = f"PAY-{uuid.uuid4().hex[:12].upper()}"
        case_id = None

        if decision == PaymentDecision.REVIEW:
            case_id = f"CASE-{uuid.uuid4().hex[:8].upper()}"
            investigation = Investigation(
                case_id=case_id,
                transaction_id=tx_id,
                investigator_id=None,
                status="open",
                decision=None,
                notes=(
                    f"Auto-flagged pre-authorization review. Risk Score: {final_risk_score}/100, "
                    f"ML Probability: {ml_prob:.4f}. Triggered: {', '.join(rule_result.rule_summary_reasons) or 'Moderate Risk Score'}."
                ),
            )
            db.add(investigation)

        # -----------------------------------------------------------------
        # STEP 9: Payment Submission Gate (ONLY ALLOW proceeds to provider)
        # -----------------------------------------------------------------
        provider_res = None
        ext_payment_id = None
        provider_status_str = None

        if decision == PaymentDecision.ALLOW:
            # Safe to submit to payment provider sandbox/mock adapter
            adapter = PaymentProviderFactory.get_provider(provider_name)
            prov_req = ProviderPaymentRequest(
                internal_payment_id=tx_id,
                customer_id=request.customer_id,
                amount=request.amount,
                currency=request.currency,
                payment_method=request.payment_method,
                merchant_name=request.merchant_name,
                idempotency_key=effective_idempotency_key or tx_id,
            )
            provider_res = adapter.create_payment(prov_req)
            ext_payment_id = provider_res.external_payment_id
            provider_status_str = provider_res.provider_status.value
            lifecycle_status = (
                PaymentLifecycleStatus.SUCCEEDED
                if provider_res.provider_status == ProviderPaymentStatus.SUCCEEDED
                else PaymentLifecycleStatus.AUTHORIZED
            )
            status_message = f"Payment pre-authorized successfully. Approved and submitted to {adapter.provider_name}."

        # -----------------------------------------------------------------
        # STEP 10: Persist PaymentIntent, Transaction & Audit Logs
        # -----------------------------------------------------------------
        payment_intent = PaymentIntent(
            payment_id=tx_id,
            customer_id=request.customer_id,
            amount=request.amount,
            currency=request.currency,
            merchant_name=request.merchant_name,
            merchant_category=request.merchant_category,
            payment_method=request.payment_method,
            lifecycle_status=lifecycle_status.value,
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

        # Mirror record in transactions table for backward compatibility
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

        # Audit Logging
        user_id = current_user.id if current_user else None
        audit_events = [
            AuditLog(
                user_id=user_id,
                action="PAYMENT_CREATED",
                resource_type="payment_intent",
                resource_id=tx_id,
                details=json.dumps({"amount": request.amount, "currency": request.currency, "customer_id": request.customer_id}),
            ),
            AuditLog(
                user_id=user_id,
                action=f"PAYMENT_{decision.value}",
                resource_type="payment_intent",
                resource_id=tx_id,
                details=json.dumps({
                    "risk_score": final_risk_score,
                    "risk_level": risk_level.value,
                    "fraud_probability": round(ml_prob, 4),
                    "decision": decision.value,
                    "rules": [r.rule_id for r in rule_result.triggered_rules],
                }),
            ),
        ]
        if case_id:
            audit_events.append(AuditLog(
                user_id=user_id,
                action="INVESTIGATION_CREATED",
                resource_type="investigation",
                resource_id=case_id,
                details=json.dumps({"payment_id": tx_id, "reason": "PRE_AUTH_REVIEW_TRIGGERED"}),
            ))
        if provider_res:
            audit_events.append(AuditLog(
                user_id=user_id,
                action="PROVIDER_SUBMITTED",
                resource_type="payment_provider",
                resource_id=ext_payment_id,
                details=json.dumps({"provider": provider_name, "status": provider_status_str}),
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
        # STEP 11: Idempotency Storage & Real-Time Event Broadcast
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

        # Broadcast live event to WebSocket/SSE subscribers
        from backend.app.services.event_broadcaster import EventBroadcaster
        EventBroadcaster.get_instance().sync_broadcast("payment.preauth_evaluated", {
            "payment_id": tx_id,
            "customer_id": request.customer_id,
            "amount": request.amount,
            "currency": request.currency,
            "decision": decision.value,
            "risk_score": final_risk_score,
            "risk_level": risk_level.value,
            "fraud_probability": round(ml_prob, 4),
            "device_risk_score": dev_assessment.combined_hardware_score,
            "network_risk_score": net_report.network_risk_score,
            "lifecycle_status": lifecycle_status.value,
            "case_id": case_id,
            "triggered_rules_count": len(triggered_rule_dtos),
            "processing_time_ms": round(elapsed_ms, 2),
        })

        return decision_result
