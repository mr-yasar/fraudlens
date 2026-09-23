"""Tests for Master Upgrade Phase 2: Adaptive Threat Intelligence & Federated Learning Simulation."""

import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.main import app
from backend.app.core.database import SessionLocal, get_db
from backend.app.models.transaction import Transaction
from backend.app.models.investigation import Investigation
from backend.app.models.user import User
from backend.app.core.security import get_password_hash, create_access_token
from backend.app.services.threat_intelligence_service import FraudThreatIntelligenceService
from backend.app.services.rule_adaptation_service import RuleAdaptationService
from backend.app.services.federated_learning_service import FederatedLearningSimulationService
from backend.app.services.feedback_loop_service import FeedbackLoopService
from backend.app.schemas.adaptive_intelligence import CandidateRuleCreate


@pytest.fixture
def db_session():
    """Create a scoped database session for testing."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def test_admin_headers(db_session: Session):
    """Generate auth token for testing admin operations."""
    admin = db_session.query(User).filter(User.email == "admin@fraudlens.io").first()
    if not admin:
        admin = User(
            email="admin@fraudlens.io",
            password_hash=get_password_hash("Admin12345!"),
            name="System Administrator",
            role="admin",
            is_active=True,
        )
        db_session.add(admin)
        db_session.commit()
        db_session.refresh(admin)

    token = create_access_token(subject=str(admin.id), role=admin.role)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def client():
    return TestClient(app)


def test_threat_intelligence_service_scan(db_session: Session):
    """Test emerging threat detection, velocity clustering, and drift metrics."""
    import uuid
    uid = uuid.uuid4().hex[:6]
    now = datetime.now(timezone.utc)
    t1 = Transaction(
        transaction_id=f"TX-THREAT-DEV-1-{uid}",
        customer_id=f"CUST-9901-{uid}",
        amount=650.0,
        transaction_hour=2,
        device_type="emulator",
        transaction_country="XX",
        fraud_probability=0.85,
        prediction=1,
        created_at=now,
    )
    t2 = Transaction(
        transaction_id=f"TX-THREAT-DEV-2-{uid}",
        customer_id=f"CUST-9902-{uid}",
        amount=720.0,
        transaction_hour=3,
        device_type="emulator",
        transaction_country="XX",
        fraud_probability=0.88,
        prediction=1,
        created_at=now,
    )
    db_session.add_all([t1, t2])
    db_session.commit()

    summary = FraudThreatIntelligenceService.scan_emerging_threats(db=db_session, limit=100)
    assert summary.total_patterns_detected >= 1
    assert any(p.pattern_type == "DEVICE_SPOOFING" for p in summary.emerging_patterns)
    assert summary.drift_score >= 0.0
    assert "amount_distribution_shift" in summary.feature_drift_indicators


def test_rule_effectiveness_and_metrics(db_session: Session):
    """Test rule effectiveness scoring and hit counting."""
    metrics = RuleAdaptationService.get_rule_effectiveness_metrics(db=db_session)
    assert len(metrics) >= 3
    for m in metrics:
        assert m.rule_id is not None
        assert 0.0 <= m.effectiveness_score <= 1.0
        assert 0.0 <= m.false_positive_rate <= 1.0
        assert m.status == "ACTIVE"


def test_candidate_rule_lifecycle(db_session: Session):
    """Test candidate rule creation, listing, approval, and rejection."""
    payload = CandidateRuleCreate(
        rule_id="CAND-TEST-RULE-01",
        rule_name="Rapid Foreign Night Withdrawal",
        condition_description="Is_Night == True AND Is_International == True AND Amount > $500",
        category="CROSS_BORDER_ANOMALY",
        proposed_action="FLAG_REVIEW",
        rationale="Spike in midnight unauthorized cross-border card testing.",
    )

    created = RuleAdaptationService.create_candidate_rule(payload=payload, db=db_session, admin_id=1)
    assert created.rule_id == "CAND-TEST-RULE-01"
    assert created.status == "CANDIDATE"

    # List candidates
    candidates = RuleAdaptationService.list_candidate_rules()
    assert any(c.rule_id == "CAND-TEST-RULE-01" for c in candidates)

    # Approve
    approved = RuleAdaptationService.approve_candidate_rule("CAND-TEST-RULE-01", db=db_session, admin_id=1)
    assert approved.status == "APPROVED"

    # Reject another
    p2 = CandidateRuleCreate(
        rule_id="CAND-TEST-RULE-02",
        rule_name="Loose Amount Check",
        condition_description="Amount > $10",
        category="AMOUNT_DEVIATION",
        proposed_action="BLOCK",
        rationale="Overly aggressive threshold.",
    )
    RuleAdaptationService.create_candidate_rule(payload=p2, db=db_session, admin_id=1)
    rejected = RuleAdaptationService.reject_candidate_rule("CAND-TEST-RULE-02", reason="High FP rate", db=db_session, admin_id=1)
    assert rejected.status == "REJECTED"


def test_federated_learning_simulation():
    """Test multi-institution federated learning simulation & FedAvg parameter aggregation."""
    res = FederatedLearningSimulationService.run_federated_simulation(rounds=3, differential_privacy_epsilon=3.0)
    
    assert res.simulation_mode == "FEDERATED_LEARNING_SIMULATION"
    assert len(res.participating_institutions) == 3
    assert res.rounds_completed == 3
    
    # Check institutions
    inst_names = [i.institution_name for i in res.participating_institutions]
    assert any("Retail Banking" in name for name in inst_names)
    assert any("NeoBank" in name for name in inst_names)
    assert any("Credit Union" in name for name in inst_names)

    for inst in res.participating_institutions:
        assert inst.data_privacy_status == "ZERO_RAW_DATA_SHARED (LOCAL BOUNDARY PRESERVED)"
        assert inst.local_pr_auc > 0.5
        assert inst.weight_update_norm > 0.0

    # Check global candidate metrics
    g_metrics = res.global_candidate_metrics
    assert g_metrics["pr_auc"] > 0.5
    assert g_metrics["f1_score"] > 0.5
    assert g_metrics["total_federated_samples"] > 1000
    assert res.challenger_eligible is True


def test_investigator_feedback_ground_truth(db_session: Session):
    """Test closed-loop ground truth recording and performance impact."""
    res = FeedbackLoopService.record_ground_truth(
        db=db_session,
        transaction_id="TX-THREAT-DEV-1",
        is_fraud=True,
        source="investigator_test_suite",
        notes="Confirmed unauthorized emulator takeover.",
        user_id=1,
    )

    assert res["transaction_id"] == "TX-THREAT-DEV-1"
    assert res["recorded_outcome"] == "CONFIRMED_FRAUD"
    assert "current_metrics" in res


def test_adaptive_intelligence_api_endpoints(client: TestClient, test_admin_headers: dict):
    """Test HTTP API endpoints for Phase 2 adaptive intelligence."""
    # 1. Threats endpoint
    resp = client.get("/api/v1/adaptive/threats", headers=test_admin_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "emerging_patterns" in data
    assert "drift_score" in data

    # 2. Rule effectiveness endpoint
    resp = client.get("/api/v1/adaptive/rules/effectiveness", headers=test_admin_headers)
    assert resp.status_code == 200
    rules = resp.json()
    assert isinstance(rules, list)

    # 3. Model comparison endpoint
    resp = client.get("/api/v1/adaptive/models/comparison", headers=test_admin_headers)
    assert resp.status_code == 200
    comp = resp.json()
    assert "active_champion" in comp
    assert "challengers" in comp
    assert comp["active_champion"]["name"] == "xgboost"

    # 4. Federated simulation endpoint
    resp = client.post("/api/v1/adaptive/federated/simulate?rounds=2", headers=test_admin_headers)
    assert resp.status_code == 200
    fed_data = resp.json()
    assert fed_data["simulation_mode"] == "FEDERATED_LEARNING_SIMULATION"
    assert len(fed_data["participating_institutions"]) == 3

    # 5. Model governance action endpoint
    gov_payload = {
        "model_name": "federated_global_candidate",
        "version": "fed-sim-v1",
        "action": "APPROVE",
        "reason": "Passed multi-institution validation with 0.88 PR-AUC.",
        "approval_notes": "Eligible for shadow challenger deployment.",
    }
    resp = client.post("/api/v1/adaptive/governance/action", json=gov_payload, headers=test_admin_headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == "RECORDED"
