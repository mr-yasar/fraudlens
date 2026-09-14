"""Comprehensive test suite for Phase 9 Risk Scoring Engine."""

import pytest
from backend.app.services.risk_scoring_service import (
    RiskScoringEngine,
    RiskLevel,
    RiskScoreResult,
)


@pytest.fixture
def risk_engine():
    return RiskScoringEngine()


def test_risk_level_boundaries(risk_engine):
    """Verify strict risk level boundary classifications."""
    assert risk_engine.classify_risk_level(0) == RiskLevel.LOW
    assert risk_engine.classify_risk_level(15) == RiskLevel.LOW
    assert risk_engine.classify_risk_level(30) == RiskLevel.LOW

    # Boundary 30 / 31
    assert risk_engine.classify_risk_level(31) == RiskLevel.MEDIUM
    assert risk_engine.classify_risk_level(50) == RiskLevel.MEDIUM
    assert risk_engine.classify_risk_level(70) == RiskLevel.MEDIUM

    # Boundary 70 / 71
    assert risk_engine.classify_risk_level(71) == RiskLevel.HIGH
    assert risk_engine.classify_risk_level(85) == RiskLevel.HIGH
    assert risk_engine.classify_risk_level(100) == RiskLevel.HIGH


def test_low_risk_transaction(risk_engine):
    """Verify normal, low-risk transaction produces LOW risk score <= 30."""
    tx = {
        "transaction_amount": 45.00,
        "avg_transaction_amount_30d_customer": 50.00,
        "transaction_velocity_1h": 0.0,
        "transaction_velocity_24h": 1.0,
        "previous_chargebacks": 0,
        "account_age_days": 365.0,
        "is_international": 0,
        "is_high_risk_merchant_category": 0,
        "transaction_hour": 14,
    }
    result = risk_engine.compute_risk_score(fraud_probability=0.02, transaction_data=tx)

    assert 0 <= result.risk_score <= 30
    assert result.risk_level == RiskLevel.LOW


def test_high_risk_transaction(risk_engine):
    """Verify suspicious transaction with multiple anomaly signals produces HIGH risk score >= 71."""
    tx = {
        "transaction_amount": 1850.00,  # 18.5x customer baseline
        "avg_transaction_amount_30d_customer": 100.00,
        "transaction_velocity_1h": 5.0,  # High burst
        "transaction_velocity_24h": 6.0,
        "previous_chargebacks": 2,  # History of disputes
        "account_age_days": 4.0,  # Brand new account
        "is_international": 1,
        "is_high_risk_merchant_category": 1,
        "transaction_hour": 3,  # Night authorization
    }
    result = risk_engine.compute_risk_score(fraud_probability=0.88, transaction_data=tx)

    assert 71 <= result.risk_score <= 100
    assert result.risk_level == RiskLevel.HIGH
    assert len(result.risk_factors) >= 4


def test_min_and_max_score_boundaries(risk_engine):
    """Verify risk scores never fall below 0 or exceed 100 under extreme inputs."""
    # Extreme negative/zero inputs
    zero_tx = {
        "transaction_amount": -100.0,
        "avg_transaction_amount_30d_customer": 0.0,
        "transaction_velocity_1h": -5.0,
    }
    min_res = risk_engine.compute_risk_score(fraud_probability=-0.5, transaction_data=zero_tx)
    assert min_res.risk_score >= 0

    # Extreme high outlier inputs
    extreme_tx = {
        "transaction_amount": 500000.0,
        "avg_transaction_amount_30d_customer": 10.0,
        "transaction_velocity_1h": 100.0,
        "previous_chargebacks": 50,
        "account_age_days": 0.1,
        "is_international": 1,
        "is_high_risk_merchant_category": 1,
        "transaction_hour": 2,
    }
    max_res = risk_engine.compute_risk_score(fraud_probability=1.5, transaction_data=extreme_tx)
    assert max_res.risk_score <= 100


def test_risk_score_is_not_simply_probability_times_100(risk_engine):
    """Verify risk score differs from raw probability * 100 due to contextual multi-factor adjustments."""
    # Scenario A: Low probability (0.05) but extreme amount spike on a brand new account
    tx_a = {
        "transaction_amount": 2500.00,
        "avg_transaction_amount_30d_customer": 50.00,
        "transaction_velocity_1h": 4.0,
        "account_age_days": 3.0,
        "previous_chargebacks": 1,
    }
    res_a = risk_engine.compute_risk_score(fraud_probability=0.05, transaction_data=tx_a)
    # p * 100 would be 5, but risk score must reflect the contextual danger
    assert res_a.risk_score > 25
    assert res_a.risk_score != int(round(0.05 * 100))

    # Scenario B: High probability (0.80) with clean established account
    tx_b = {
        "transaction_amount": 50.00,
        "avg_transaction_amount_30d_customer": 50.00,
        "transaction_velocity_1h": 0.0,
        "account_age_days": 800.0,
        "previous_chargebacks": 0,
    }
    res_b = risk_engine.compute_risk_score(fraud_probability=0.80, transaction_data=tx_b)
    # Model pts ~35, minimal contextual pts -> score ~35-40 (MEDIUM), whereas p*100 would be 80 (HIGH)
    assert res_b.risk_score != int(round(0.80 * 100))


def test_determinism_and_factor_serialization(risk_engine):
    """Verify deterministic output and factor dictionary conversion."""
    tx = {
        "transaction_amount": 350.00,
        "avg_transaction_amount_30d_customer": 100.00,
        "transaction_velocity_1h": 2.0,
        "previous_chargebacks": 1,
    }
    res1 = risk_engine.compute_risk_score(fraud_probability=0.45, transaction_data=tx)
    res2 = risk_engine.compute_risk_score(fraud_probability=0.45, transaction_data=tx)

    assert res1.risk_score == res2.risk_score
    assert res1.risk_level == res2.risk_level
    assert len(res1.risk_factors) == len(res2.risk_factors)

    d = res1.to_dict()
    assert "risk_score" in d
    assert "risk_level" in d
    assert "risk_factors" in d
    assert isinstance(d["risk_factors"], list)
