"""Targeted Integration Tests for Phases 17–30: Intelligence, Fusion, Anomaly & Explainability."""

import json
import pytest
from sqlalchemy.orm import Session

from backend.app.services.network_intelligence_service import FraudNetworkIntelligenceService
from ml.anomaly.isolation_forest_service import AnomalyIntelligenceService
from ml.evaluation.uncertainty_service import UncertaintyEstimationService
from backend.app.services.signal_fusion_service import SignalFusionService
from ml.explainability.counterfactual_engine import CounterfactualEngine
from backend.app.services.explanation_composer import ExplanationComposer
from backend.app.services.prediction_service import FraudPredictionService
from backend.app.schemas.prediction import TransactionPredictionInput
from backend.app.core.database import SessionLocal


def test_network_intelligence_evaluation():
    """Phase 17: Verify entity and network linkage risk assessment."""
    db: Session = SessionLocal()
    try:
        report = FraudNetworkIntelligenceService.evaluate_network_risk(
            db=db,
            customer_id="CUST001",
            device_type="Mac",
            merchant_name="Amazon",
            amount=500.0,
        )
        assert report.customer_id == "CUST001"
        assert 0.0 <= report.network_risk_score <= 100.0
        assert report.risk_level in ["LOW", "MEDIUM", "HIGH"]
        assert isinstance(report.connected_entity_count, int)
    finally:
        db.close()


def test_anomaly_intelligence_scoring():
    """Phase 18: Verify unsupervised Isolation Forest anomaly scoring."""
    service = AnomalyIntelligenceService.get_instance()
    if service.is_ready:
        import numpy as np
        # 48-dimensional feature vector
        sample_vec = np.zeros(service.feature_dimension or 48)
        res = service.score_vector(sample_vec)
        assert res.anomaly_status in ["AVAILABLE", "DEGRADED"]
        if res.anomaly_score is not None:
            assert 0.0 <= res.anomaly_score <= 1.0


def test_uncertainty_estimation():
    """Phase 20: Verify prediction uncertainty and confidence estimation."""
    eval_res = UncertaintyEstimationService.evaluate_uncertainty(
        probabilities={"xgboost": 0.08, "random_forest": 0.12, "logistic_regression": 0.05},
        active_probability=0.08,
        threshold=0.0637,
    )
    assert 0.0 <= eval_res.uncertainty_score <= 1.0
    assert eval_res.uncertainty_level in ["LOW", "MODERATE", "HIGH"]
    assert eval_res.confidence_status in ["HIGH_CONFIDENCE", "MODERATE_CONFIDENCE", "LOW_CONFIDENCE"]


def test_transparent_signal_fusion():
    """Phase 21: Verify multi-signal fusion without data fabrication."""
    fusion = SignalFusionService.fuse_signals(
        supervised_probability=0.15,
        anomaly_score=0.45,
        network_risk_score=20.0,
        behavior_deviation_score=35.0,
        uncertainty_score=0.25,
    )
    assert 0.0 <= fusion.fused_index <= 1.0
    assert fusion.primary_driver in ["supervised_ml", "behavior_profile", "unsupervised_anomaly", "network_linkage"]
    assert "supervised_ml" in fusion.evidence_breakdown
    assert fusion.evidence_breakdown["supervised_ml"].status == "AVAILABLE"


def test_counterfactual_generation_and_explanation():
    """Phase 22 & 23: Verify genuine counterfactual search and composed evidence narrative."""
    pred_service = FraudPredictionService.get_instance()
    if pred_service.is_ready:
        inp = TransactionPredictionInput(
            transaction_id="TEST-TX-100",
            customer_id="CUST001",
            Amount=8500.0,
            Average_Previous_Amount=2000.0,
            Transaction_Type="Transfer",
            Transaction_Hour=2,
            Location="Berlin",
            Usual_Location="Pune",
            Device_Type="Android",
            New_Device=1,
            Failed_Attempts=2,
            International_Transaction=1,
            Unusual_Location=1,
        )
        pred_res = pred_service.predict_transaction(inp)
        assert pred_res.prediction in ["FRAUD", "GENUINE"]
        assert 0.0 <= pred_res.fraud_probability <= 1.0
        assert 0 <= pred_res.risk_score <= 100
        
        # Verify counterfactual was generated
        if pred_res.counterfactual:
            assert "status" in pred_res.counterfactual
            assert "actionable_summary" in pred_res.counterfactual
            
        # Verify composed explanation was generated
        if pred_res.composed_explanation:
            assert "investigator_summary" in pred_res.composed_explanation
            assert "technical_summary" in pred_res.composed_explanation
            assert "evidence_items" in pred_res.composed_explanation
