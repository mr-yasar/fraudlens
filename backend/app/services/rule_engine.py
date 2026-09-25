"""Centralized Explainable Rule Engine (Phase 14).

Evaluates deterministic velocity, amount, device, location, and authentication rules.
All rules return structured, human-explainable reasons and actionable severity impacts.
"""

from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field

from backend.app.services.behavior_profile_service import DerivedPreAuthFeatures


class RuleCategory(str, Enum):
    VELOCITY = "VELOCITY"
    AMOUNT_DEVIATION = "AMOUNT_DEVIATION"
    LOCATION_CHANGE = "LOCATION_CHANGE"
    DEVICE_CHANGE = "DEVICE_CHANGE"
    FAILED_ATTEMPTS = "FAILED_ATTEMPTS"
    TIME_ANOMALY = "TIME_ANOMALY"
    BEHAVIOUR_DEVIATION = "BEHAVIOUR_DEVIATION"
    MULTI_SIGNAL = "MULTI_SIGNAL"


class RuleSeverity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class RuleActionImpact(str, Enum):
    ALLOW = "ALLOW"
    FLAG_REVIEW = "FLAG_REVIEW"
    ENFORCE_BLOCK = "ENFORCE_BLOCK"


class EvaluatedRule(BaseModel):
    rule_id: str
    rule_name: str
    category: RuleCategory
    triggered: bool
    severity: RuleSeverity
    action_impact: RuleActionImpact
    reason: str
    score_penalty: int = 0
    metadata: Dict[str, Any] = Field(default_factory=dict)


class RuleEngineResult(BaseModel):
    triggered_rules: List[EvaluatedRule]
    hard_block: bool
    recommended_action: RuleActionImpact
    total_rule_penalty_score: int
    rule_summary_reasons: List[str]


class RuleEngine:
    """Authoritative Rule Engine evaluating deterministic risk checks against pre-auth context."""

    HIGH_RISK_CATEGORIES = {
        "crypto", "cryptocurrency", "luxury_goods", "jewelry", "gambling",
        "casino", "wire_transfer", "money_transfer", "electronics",
    }

    @classmethod
    def evaluate(
        cls,
        features: DerivedPreAuthFeatures,
        payment_method: str = "card",
        merchant_name: str = "",
        ml_fraud_prob: float = 0.0,
    ) -> RuleEngineResult:
        """Run all configured deterministic rule modules and aggregate findings."""
        evaluated_rules: List[EvaluatedRule] = []

        # ----------------------------------------------------
        # 1. VELOCITY RULES
        # ----------------------------------------------------
        # Critical velocity burst (>= 5 tx in 1 hour)
        vel_crit = features.velocity_1h >= 5
        evaluated_rules.append(EvaluatedRule(
            rule_id="RULE-VEL-01",
            rule_name="Critical 1-Hour Velocity Burst",
            category=RuleCategory.VELOCITY,
            triggered=vel_crit,
            severity=RuleSeverity.CRITICAL if vel_crit else RuleSeverity.LOW,
            action_impact=RuleActionImpact.ENFORCE_BLOCK if vel_crit else RuleActionImpact.ALLOW,
            reason=f"Customer initiated {features.velocity_1h} transactions within 1 hour (Threshold: 5).",
            score_penalty=35 if vel_crit else 0,
            metadata={"velocity_1h": features.velocity_1h, "threshold": 5},
        ))

        # Elevated velocity (>= 3 tx in 1 hour)
        vel_elev = (features.velocity_1h >= 3 and not vel_crit)
        evaluated_rules.append(EvaluatedRule(
            rule_id="RULE-VEL-02",
            rule_name="Elevated Velocity Acceleration",
            category=RuleCategory.VELOCITY,
            triggered=vel_elev,
            severity=RuleSeverity.HIGH if vel_elev else RuleSeverity.LOW,
            action_impact=RuleActionImpact.FLAG_REVIEW if vel_elev else RuleActionImpact.ALLOW,
            reason=f"Customer initiated {features.velocity_1h} transactions in 1 hour (Threshold: 3).",
            score_penalty=20 if vel_elev else 0,
            metadata={"velocity_1h": features.velocity_1h, "threshold": 3},
        ))

        # ----------------------------------------------------
        # 2. AMOUNT DEVIATION RULES
        # ----------------------------------------------------
        # Severe amount surge (>= 4x baseline with amount >= $1,000)
        amt_severe = (features.amount_ratio >= 4.0 and features.amount >= 1000.0) and not features.is_cold_start
        evaluated_rules.append(EvaluatedRule(
            rule_id="RULE-AMT-01",
            rule_name="Severe Monetary Amount Spike",
            category=RuleCategory.AMOUNT_DEVIATION,
            triggered=amt_severe,
            severity=RuleSeverity.HIGH if amt_severe else RuleSeverity.LOW,
            action_impact=RuleActionImpact.ENFORCE_BLOCK if (amt_severe and features.amount >= 5000.0) else (RuleActionImpact.FLAG_REVIEW if amt_severe else RuleActionImpact.ALLOW),
            reason=f"Transaction amount (${features.amount:,.2f}) is {features.amount_ratio:.1f}x higher than historical baseline (${features.historical_avg_amount:,.2f}).",
            score_penalty=25 if amt_severe else 0,
            metadata={"amount": features.amount, "historical_avg": features.historical_avg_amount, "ratio": features.amount_ratio},
        ))

        # Moderate amount deviation (>= 2.5x baseline)
        amt_mod = (features.amount_ratio >= 2.5 and not amt_severe and not features.is_cold_start)
        evaluated_rules.append(EvaluatedRule(
            rule_id="RULE-AMT-02",
            rule_name="Moderate Amount Deviation",
            category=RuleCategory.AMOUNT_DEVIATION,
            triggered=amt_mod,
            severity=RuleSeverity.MEDIUM if amt_mod else RuleSeverity.LOW,
            action_impact=RuleActionImpact.FLAG_REVIEW if amt_mod else RuleActionImpact.ALLOW,
            reason=f"Transaction amount (${features.amount:,.2f}) is {features.amount_ratio:.1f}x above customer average.",
            score_penalty=15 if amt_mod else 0,
            metadata={"amount": features.amount, "ratio": features.amount_ratio},
        ))

        # ----------------------------------------------------
        # 3. FAILED ATTEMPTS (BRUTE FORCE / CREDENTIAL STUFFING)
        # ----------------------------------------------------
        auth_burst = features.failed_attempts >= 3
        evaluated_rules.append(EvaluatedRule(
            rule_id="RULE-AUTH-01",
            rule_name="Preceding Authentication Failure Burst",
            category=RuleCategory.FAILED_ATTEMPTS,
            triggered=auth_burst,
            severity=RuleSeverity.CRITICAL if auth_burst else RuleSeverity.LOW,
            action_impact=RuleActionImpact.ENFORCE_BLOCK if auth_burst else RuleActionImpact.ALLOW,
            reason=f"Detected {features.failed_attempts} consecutive authentication failures prior to checkout.",
            score_penalty=30 if auth_burst else 0,
            metadata={"failed_attempts": features.failed_attempts},
        ))

        # ----------------------------------------------------
        # 4. ACCOUNT TAKEOVER (ATO) / MULTI-SIGNAL PATTERNS
        # ----------------------------------------------------
        # Critical ATO pattern: New Device + Unusual Location + Severe Amount Spike OR Bot client
        ato_crit = (
            (features.is_new_device and features.is_unusual_location and features.amount_ratio >= 3.0) or
            (features.amount >= 3000.0 and (features.is_new_device or features.is_unusual_location)) or
            (features.amount_ratio >= 10.0 and (features.is_new_device or features.is_unusual_location))
        ) and not features.is_cold_start
        evaluated_rules.append(EvaluatedRule(
            rule_id="RULE-ATO-01",
            rule_name="Account Takeover Signature Pattern",
            category=RuleCategory.MULTI_SIGNAL,
            triggered=ato_crit,
            severity=RuleSeverity.CRITICAL if (ato_crit and (features.amount >= 5000.0 or features.failed_attempts >= 3 or features.device_type == "unknown_bot")) else (RuleSeverity.HIGH if ato_crit else RuleSeverity.LOW),
            action_impact=RuleActionImpact.ENFORCE_BLOCK if (ato_crit and (features.amount >= 5000.0 or features.failed_attempts >= 3 or features.device_type == "unknown_bot")) else (RuleActionImpact.FLAG_REVIEW if ato_crit else RuleActionImpact.ALLOW),
            reason="Unrecognized hardware device and foreign location mismatch combined with severe monetary spike.",
            score_penalty=35 if ato_crit else 0,
            metadata={"is_new_device": features.is_new_device, "is_unusual_location": features.is_unusual_location, "amount_ratio": features.amount_ratio},
        ))

        # Moderate ATO check: New Device with moderate amount surge
        ato_mod = ((features.is_new_device or features.is_unusual_location) and features.amount_ratio >= 2.0 and not ato_crit and not features.is_cold_start)
        evaluated_rules.append(EvaluatedRule(
            rule_id="RULE-ATO-02",
            rule_name="Unusual Device/Location with Elevated Amount",
            category=RuleCategory.DEVICE_CHANGE,
            triggered=ato_mod,
            severity=RuleSeverity.MEDIUM if ato_mod else RuleSeverity.LOW,
            action_impact=RuleActionImpact.FLAG_REVIEW if ato_mod else RuleActionImpact.ALLOW,
            reason=f"Payment from novel device '{features.device_type}' or unfamiliar region with above-average amount.",
            score_penalty=15 if ato_mod else 0,
            metadata={"device": features.device_type, "location": features.location},
        ))

        # ----------------------------------------------------
        # 5. HIGH RISK SECTOR & MERCHANTS
        # ----------------------------------------------------
        cat_lower = features.merchant_category.lower()
        is_high_risk_sector = cat_lower in cls.HIGH_RISK_CATEGORIES
        sector_elevated = is_high_risk_sector and (features.amount >= 2000.0 or features.failed_attempts >= 2 or features.is_new_device)
        evaluated_rules.append(EvaluatedRule(
            rule_id="RULE-CAT-01",
            rule_name="High Risk Sector On Elevated Threat Profile",
            category=RuleCategory.MULTI_SIGNAL,
            triggered=sector_elevated,
            severity=RuleSeverity.CRITICAL if (sector_elevated and features.amount >= 5000.0) else (RuleSeverity.HIGH if sector_elevated else RuleSeverity.LOW),
            action_impact=RuleActionImpact.ENFORCE_BLOCK if (sector_elevated and features.amount >= 5000.0) else (RuleActionImpact.FLAG_REVIEW if sector_elevated else RuleActionImpact.ALLOW),
            reason=f"High-risk merchant sector '{features.merchant_category}' combined with elevated risk signals.",
            score_penalty=20 if sector_elevated else 0,
            metadata={"category": features.merchant_category, "amount": features.amount},
        ))

        # ----------------------------------------------------
        # 6. TIME ANOMALY (OFF-HOURS HIGH VALUE)
        # ----------------------------------------------------
        time_risk = (features.is_night_transaction and features.amount >= 2500.0 and not features.is_cold_start)
        evaluated_rules.append(EvaluatedRule(
            rule_id="RULE-TIME-01",
            rule_name="Off-Hours High Monetary Volume",
            category=RuleCategory.TIME_ANOMALY,
            triggered=time_risk,
            severity=RuleSeverity.MEDIUM if time_risk else RuleSeverity.LOW,
            action_impact=RuleActionImpact.FLAG_REVIEW if time_risk else RuleActionImpact.ALLOW,
            reason=f"High-value payment (${features.amount:,.2f}) executed during late night/early morning hours ({features.transaction_hour:02d}:00).",
            score_penalty=10 if time_risk else 0,
            metadata={"hour": features.transaction_hour, "amount": features.amount},
        ))

        # Filter only triggered rules
        triggered = [r for r in evaluated_rules if r.triggered]
        hard_block = any(r.action_impact == RuleActionImpact.ENFORCE_BLOCK for r in triggered)
        has_review = any(r.action_impact == RuleActionImpact.FLAG_REVIEW for r in triggered)

        if hard_block:
            recommended_action = RuleActionImpact.ENFORCE_BLOCK
        elif has_review:
            recommended_action = RuleActionImpact.FLAG_REVIEW
        else:
            recommended_action = RuleActionImpact.ALLOW

        total_penalty = sum(r.score_penalty for r in triggered)
        summary_reasons = [r.reason for r in triggered]

        return RuleEngineResult(
            triggered_rules=triggered,
            hard_block=hard_block,
            recommended_action=recommended_action,
            total_rule_penalty_score=total_penalty,
            rule_summary_reasons=summary_reasons,
        )
