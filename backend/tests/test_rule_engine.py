"""Unit tests for Centralized Rule Engine (Phase 14)."""

from backend.app.services.behavior_profile_service import DerivedPreAuthFeatures
from backend.app.services.rule_engine import RuleEngine, RuleActionImpact, RuleSeverity


def _build_features(
    amount=100.0,
    historical_avg=100.0,
    velocity_1h=0,
    is_new_device=False,
    is_unusual_location=False,
    failed_attempts=0,
    merchant_category="retail",
    is_cold_start=False,
) -> DerivedPreAuthFeatures:
    ratio = amount / (historical_avg + 1e-5)
    return DerivedPreAuthFeatures(
        customer_id="CUST-TEST",
        amount=amount,
        historical_avg_amount=historical_avg,
        amount_deviation=amount - historical_avg,
        amount_ratio=ratio,
        is_extreme_amount_surge=(ratio >= 3.0 and amount > 500.0),
        velocity_1h=velocity_1h,
        velocity_24h=velocity_1h,
        is_new_device=is_new_device,
        is_unusual_location=is_unusual_location,
        is_international=False,
        is_night_transaction=False,
        failed_attempts=failed_attempts,
        account_age_days=60.0,
        device_type="web",
        location="US",
        merchant_category=merchant_category,
        transaction_country="US",
        transaction_type="online_payment",
        transaction_hour=14,
        is_cold_start=is_cold_start,
        behaviour_deviation_score=0.1,
    )


def test_rule_engine_routine_transaction_allows():
    """Verify routine transaction triggers zero rules and returns ALLOW."""
    feats = _build_features(amount=85.0, historical_avg=100.0, velocity_1h=1)
    res = RuleEngine.evaluate(feats)
    assert len(res.triggered_rules) == 0
    assert res.hard_block is False
    assert res.recommended_action == RuleActionImpact.ALLOW
    assert res.total_rule_penalty_score == 0


def test_rule_engine_velocity_burst_blocks():
    """Verify critical velocity burst triggers RULE-VEL-01 and hard blocks."""
    feats = _build_features(amount=100.0, velocity_1h=6)
    res = RuleEngine.evaluate(feats)
    assert any(r.rule_id == "RULE-VEL-01" for r in res.triggered_rules)
    assert res.hard_block is True
    assert res.recommended_action == RuleActionImpact.ENFORCE_BLOCK


def test_rule_engine_failed_attempts_blocks():
    """Verify repeated authentication failures trigger RULE-AUTH-01."""
    feats = _build_features(amount=100.0, failed_attempts=4)
    res = RuleEngine.evaluate(feats)
    assert any(r.rule_id == "RULE-AUTH-01" for r in res.triggered_rules)
    assert res.hard_block is True
    assert res.recommended_action == RuleActionImpact.ENFORCE_BLOCK


def test_rule_engine_moderate_deviation_flags_review():
    """Verify moderate device / amount surge triggers FLAG_REVIEW."""
    feats = _build_features(amount=280.0, historical_avg=100.0, is_new_device=True)
    res = RuleEngine.evaluate(feats)
    assert any(r.rule_id == "RULE-ATO-02" for r in res.triggered_rules)
    assert res.hard_block is False
    assert res.recommended_action == RuleActionImpact.FLAG_REVIEW
