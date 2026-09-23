"""Integration Tests for Part 3 (Phases 31–60): Health, Drift, Champion/Challenger, Governance & End-to-End Scenarios."""

import json
import pytest
from sqlalchemy.orm import Session

from backend.app.core.database import SessionLocal
from backend.app.services.model_health_service import ModelHealthService
from backend.app.services.drift_monitoring_service import DriftMonitoringService
from backend.app.services.champion_challenger_service import ChampionChallengerService
from backend.app.services.governance_service import GovernanceService
from backend.app.services.risk_decision_orchestrator import RiskDecisionOrchestrator
from backend.app.schemas.payment import PaymentInitiateRequest
from backend.app.models.transaction import Transaction


def test_model_health_telemetry():
    """Phase 31: Test real runtime operational health calculation."""
    db: Session = SessionLocal()
    try:
        health = ModelHealthService.evaluate_model_health(db, model_name="xgboost", model_version="v1.1.0")
        assert health.status in ["HEALTHY", "WARNING", "DEGRADED", "NOT_ENOUGH_DATA"]
        assert health.total_predictions >= 0
        assert 0.0 <= health.allow_rate <= 1.0
        assert 0.0 <= health.block_rate <= 1.0
        assert 0.0 <= health.review_rate <= 1.0
    finally:
        db.close()


def test_data_and_prediction_drift():
    """Phases 32 & 33: Test statistical drift monitoring."""
    db: Session = SessionLocal()
    try:
        drift = DriftMonitoringService.evaluate_live_drift(db)
        assert drift.overall_drift_status in ["HEALTHY", "POTENTIAL_DRIFT", "CRITICAL_DRIFT", "NOT_ENOUGH_DATA"]
        assert isinstance(drift.feature_drift_reports, list)
    finally:
        db.close()


def test_fairness_and_governance_snapshot():
    """Phases 39, 40, 50: Test fairness auditing and consolidated governance snapshot."""
    db: Session = SessionLocal()
    try:
        fairness = GovernanceService.audit_fairness_on_available_features(db)
        assert fairness.fairness_status in ["VALIDATED_ON_OPERATIONAL_ATTRIBUTES", "INCONCLUSIVE"]
        assert "INCONCLUSIVE" in fairness.protected_demographics_status

        gov_snap = GovernanceService.get_unified_governance_snapshot(db)
        assert "dataset_health" in gov_snap.to_dict()
        assert "model_health" in gov_snap.to_dict()
        assert "drift_status" in gov_snap.to_dict()
        assert "fairness_audit" in gov_snap.to_dict()
    finally:
        db.close()


def test_full_system_scenarios_a_to_c():
    """Phase 52: Full System Scenarios (LOW-risk, HIGH-risk)."""
    db: Session = SessionLocal()
    try:
        # Scenario A: Low-Risk Normal Transaction
        import uuid
        low_req = PaymentInitiateRequest(
            customer_id=f"CUST_GOV_LOW_{uuid.uuid4().hex[:6]}",
            amount=45.0,
            currency="USD",
            payment_method="credit_card",
            merchant_name="Supermarket",
            merchant_category="retail",
            device_type="dedicated_clean_device",
            location="Pune",
            transaction_country="IN",
            transaction_type="Purchase",
            failed_attempts=0,
        )
        res_low = RiskDecisionOrchestrator.evaluate_and_process_payment(db=db, request=low_req)
        assert res_low.decision.value in ["ALLOW", "REVIEW"]
        assert 0 <= res_low.risk_score <= 100
        assert res_low.model_version is not None

        # Scenario C: High-Risk Anomalous International Surge
        high_req = PaymentInitiateRequest(
            customer_id="CUST001",
            amount=98500.0,
            currency="USD",
            payment_method="wire_transfer",
            merchant_name="darknet_market",
            merchant_category="crypto",
            device_type="Unknown_Linux_Bot",
            location="Unknown_Country",
            transaction_country="XX",
            transaction_type="Transfer",
            failed_attempts=5,
        )
        res_high = RiskDecisionOrchestrator.evaluate_and_process_payment(db=db, request=high_req)
        assert res_high.decision.value in ["BLOCK", "REVIEW"]
        assert res_high.risk_score >= 45
    finally:
        db.close()
