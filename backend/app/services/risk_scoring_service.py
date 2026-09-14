"""Multi-Factor Risk Scoring Engine for Financial Fraud Detection."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional
import pandas as pd


class RiskLevel(str, Enum):
    """Holistic Risk Classification Levels."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


@dataclass
class RiskFactorDetail:
    """Breakdown of an individual risk factor contribution."""

    factor: str
    impact_score: float
    severity: str  # 'LOW', 'MEDIUM', 'HIGH'
    detail: str


@dataclass
class RiskScoreResult:
    """Comprehensive output of the risk scoring engine."""

    risk_score: int  # [0, 100]
    risk_level: RiskLevel  # LOW, MEDIUM, HIGH
    risk_factors: List[RiskFactorDetail] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "risk_score": self.risk_score,
            "risk_level": self.risk_level.value,
            "risk_factors": [
                {
                    "factor": f.factor,
                    "impact_score": round(f.impact_score, 2),
                    "severity": f.severity,
                    "detail": f.detail,
                }
                for f in self.risk_factors
            ],
        }


class RiskScoringEngine:
    """Deterministic, transparent risk scoring engine combining ML probabilities and behavioural signals."""

    @staticmethod
    def classify_risk_level(score: int) -> RiskLevel:
        """Map integer score [0, 100] to strict risk level thresholds:

        - 0 to 30   -> LOW
        - 31 to 70  -> MEDIUM
        - 71 to 100 -> HIGH
        """
        if score <= 30:
            return RiskLevel.LOW
        elif score <= 70:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.HIGH

    def compute_risk_score(
        self,
        fraud_probability: float,
        transaction_data: Dict[str, Any],
    ) -> RiskScoreResult:
        """Compute application-level 0-100 risk score and factor breakdown.

        Guarantees:
        - Output is always in [0, 100]
        - Deterministic and explainable
        - Not simply fraud_probability * 100
        """
        factors: List[RiskFactorDetail] = []
        total_score: float = 0.0

        # Safe input extraction (supports both actual CSV columns and legacy columns)
        p = max(0.0, min(1.0, float(fraud_probability)))
        amount = max(0.0, float(transaction_data.get("Amount", transaction_data.get("transaction_amount", 0.0))))
        avg_amount_30d = max(0.0, float(transaction_data.get("Average_Previous_Amount", transaction_data.get("avg_transaction_amount_30d_customer", 0.0))))
        vel_1h = max(0.0, float(transaction_data.get("transaction_velocity_1h", 0.0)))
        vel_24h = max(0.0, float(transaction_data.get("Transactions_Last_24H", transaction_data.get("transaction_velocity_24h", 0.0))))
        failed_attempts = max(0, int(transaction_data.get("Failed_Attempts", 0)))
        chargebacks = max(0, int(transaction_data.get("previous_chargebacks", 0)))
        account_age = max(0.0, float(transaction_data.get("Account_Age_Days", transaction_data.get("account_age_days", 365.0))))
        is_intl = int(transaction_data.get("International_Transaction", transaction_data.get("is_international", 0))) == 1
        is_unusual_loc = int(transaction_data.get("Unusual_Location", 0)) == 1
        is_new_device = int(transaction_data.get("New_Device", 0)) == 1
        is_high_risk_cat = int(transaction_data.get("is_high_risk_merchant_category", 0)) == 1
        hour = int(transaction_data.get("Transaction_Hour", transaction_data.get("transaction_hour", 12)))

        # =========================================================================
        # 1. Model Baseline Probability Signal (Max: 45 pts)
        # =========================================================================
        model_pts = 45.0 * (p ** 1.1)
        total_score += model_pts

        if p >= 0.70:
            factors.append(RiskFactorDetail(
                factor="ml_model_high_fraud_probability",
                impact_score=model_pts,
                severity="HIGH",
                detail=f"Machine learning model flagged high fraud probability ({p:.4f})",
            ))
        elif p >= 0.35:
            factors.append(RiskFactorDetail(
                factor="ml_model_moderate_fraud_probability",
                impact_score=model_pts,
                severity="MEDIUM",
                detail=f"Machine learning model indicated moderate fraud risk ({p:.4f})",
            ))
        elif model_pts > 0:
            factors.append(RiskFactorDetail(
                factor="ml_model_baseline",
                impact_score=model_pts,
                severity="LOW",
                detail=f"Machine learning model baseline probability is low ({p:.4f})",
            ))

        # =========================================================================
        # 2. Transaction Amount Abnormality Signal (Max: 18 pts)
        # =========================================================================
        amount_ratio = amount / (avg_amount_30d + 1e-5) if avg_amount_30d > 0 else 1.0
        amount_pts = 0.0

        if amount_ratio >= 8.0:
            amount_pts = 18.0
            factors.append(RiskFactorDetail(
                factor="extreme_amount_spike",
                impact_score=amount_pts,
                severity="HIGH",
                detail=f"Transaction amount (${amount:.2f}) is {amount_ratio:.1f}x higher than customer 30-day baseline",
            ))
        elif amount_ratio >= 4.0:
            amount_pts = 13.0
            factors.append(RiskFactorDetail(
                factor="severe_amount_abnormality",
                impact_score=amount_pts,
                severity="HIGH",
                detail=f"Transaction amount (${amount:.2f}) is {amount_ratio:.1f}x higher than customer 30-day baseline",
            ))
        elif amount_ratio >= 2.0:
            amount_pts = 7.0
            factors.append(RiskFactorDetail(
                factor="moderate_amount_abnormality",
                impact_score=amount_pts,
                severity="MEDIUM",
                detail=f"Transaction amount is {amount_ratio:.1f}x customer average (${avg_amount_30d:.2f})",
            ))
        elif amount > 3000.0:
            amount_pts = 5.0
            factors.append(RiskFactorDetail(
                factor="high_absolute_amount",
                impact_score=amount_pts,
                severity="MEDIUM",
                detail=f"High transaction monetary volume (${amount:.2f})",
            ))
        total_score += amount_pts

        # =========================================================================
        # 3. Transaction Velocity & Burst Acceleration Signal (Max: 15 pts)
        # =========================================================================
        vel_pts = 0.0
        if vel_1h >= 5.0:
            vel_pts = 15.0
            factors.append(RiskFactorDetail(
                factor="extreme_velocity_burst",
                impact_score=vel_pts,
                severity="HIGH",
                detail=f"Critical velocity burst of {int(vel_1h)} transactions in the past 1 hour",
            ))
        elif vel_1h >= 3.0:
            vel_pts = 10.0
            factors.append(RiskFactorDetail(
                factor="elevated_velocity_burst",
                impact_score=vel_pts,
                severity="HIGH",
                detail=f"Elevated velocity of {int(vel_1h)} transactions in the past 1 hour",
            ))
        elif vel_1h >= 2.0:
            vel_pts = 5.0
            factors.append(RiskFactorDetail(
                factor="moderate_velocity",
                impact_score=vel_pts,
                severity="MEDIUM",
                detail=f"Multiple rapid transactions ({int(vel_1h)}) within 1 hour",
            ))
        total_score += vel_pts

        # =========================================================================
        # 4. Customer History & Chargeback Exposure Signal (Max: 12 pts)
        # =========================================================================
        hist_pts = 0.0
        if chargebacks >= 2:
            hist_pts += 8.0
            factors.append(RiskFactorDetail(
                factor="chronic_chargeback_history",
                impact_score=8.0,
                severity="HIGH",
                detail=f"Customer account has {chargebacks} prior recorded chargebacks/disputes",
            ))
        elif chargebacks == 1:
            hist_pts += 5.0
            factors.append(RiskFactorDetail(
                factor="prior_chargeback_record",
                impact_score=5.0,
                severity="MEDIUM",
                detail="Customer account has 1 prior chargeback incident",
            ))

        if account_age < 7.0:
            hist_pts += 4.0
            factors.append(RiskFactorDetail(
                factor="brand_new_account",
                impact_score=4.0,
                severity="HIGH",
                detail=f"Brand new customer account created {int(account_age)} days ago",
            ))
        elif account_age < 30.0:
            hist_pts += 2.0
            factors.append(RiskFactorDetail(
                factor="young_account_tenure",
                impact_score=2.0,
                severity="LOW",
                detail=f"Relatively new customer tenure ({int(account_age)} days)",
            ))
        total_score += hist_pts

        # =========================================================================
        # 5. Channel, Cross-Border & Temporal Risk Signal (Max: 15 pts)
        # =========================================================================
        env_pts = 0.0
        if is_high_risk_cat:
            env_pts += 4.0
            factors.append(RiskFactorDetail(
                factor="high_risk_merchant_category",
                impact_score=4.0,
                severity="MEDIUM",
                detail="Transaction conducted with a designated high-risk merchant category",
            ))

        if is_intl:
            env_pts += 3.0
            factors.append(RiskFactorDetail(
                factor="cross_border_transaction",
                impact_score=3.0,
                severity="LOW",
                detail="Cross-border international payment processing",
            ))

        if is_unusual_loc:
            env_pts += 4.0
            factors.append(RiskFactorDetail(
                factor="unusual_location_authorization",
                impact_score=4.0,
                severity="HIGH",
                detail="Transaction originated from a geographic location outside customer normal pattern",
            ))

        if is_new_device:
            env_pts += 3.0
            factors.append(RiskFactorDetail(
                factor="new_device_signature",
                impact_score=3.0,
                severity="MEDIUM",
                detail="Transaction attempted from an unrecognized new device hardware signature",
            ))

        if failed_attempts >= 2:
            env_pts += 5.0
            factors.append(RiskFactorDetail(
                factor="failed_attempts_burst",
                impact_score=5.0,
                severity="HIGH",
                detail=f"Detected {failed_attempts} preceding failed authentication attempts",
            ))
        elif failed_attempts == 1:
            env_pts += 2.0
            factors.append(RiskFactorDetail(
                factor="failed_attempt_prior",
                impact_score=2.0,
                severity="LOW",
                detail="One prior failed authentication attempt noted",
            ))

        if hour in [0, 1, 2, 3, 4, 5]:
            env_pts += 3.0
            factors.append(RiskFactorDetail(
                factor="off_hours_night_transaction",
                impact_score=3.0,
                severity="LOW",
                detail=f"Transaction authorized during unusual night operating window ({hour:02d}:00)",
            ))
        total_score += env_pts

        # Final integer clamp strictly [0, 100]
        final_score = int(round(min(100.0, max(0.0, total_score))))
        risk_level = self.classify_risk_level(final_score)

        return RiskScoreResult(
            risk_score=final_score,
            risk_level=risk_level,
            risk_factors=factors,
        )
