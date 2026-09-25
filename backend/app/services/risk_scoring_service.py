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
    display_name: Optional[str] = None
    category: Optional[str] = None


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
                    "display_name": f.display_name or f.factor.replace("_", " ").title(),
                    "category": f.category or "risk_factor",
                }
                for f in self.risk_factors
            ],
        }


class RiskScoringEngine:
    """Deterministic, transparent risk scoring engine combining ML probabilities and behavioural signals."""

    LOW_THRESHOLD: int = 30
    HIGH_THRESHOLD: int = 70

    @classmethod
    def get_thresholds(cls) -> Dict[str, int]:
        """Return configured risk score boundaries."""
        return {
            "low_threshold": cls.LOW_THRESHOLD,
            "high_threshold": cls.HIGH_THRESHOLD,
        }

    @classmethod
    def update_thresholds(cls, low: int = 30, high: int = 70) -> None:
        """Update configurable risk scoring boundaries."""
        if low < 0 or high > 100 or low >= high:
            raise ValueError(f"Invalid threshold range: low={low}, high={high}. Must satisfy 0 <= low < high <= 100.")
        cls.LOW_THRESHOLD = low
        cls.HIGH_THRESHOLD = high

    @classmethod
    def classify_risk_level(cls, score: int, prob: Optional[float] = None) -> RiskLevel:
        """Map integer score [0, 100] and ML probability to configurable risk level thresholds:

        - ML prob >= 0.70 or score > HIGH_THRESHOLD (default 70) -> HIGH
        - ML prob >= 0.35 or score > LOW_THRESHOLD (default 30)  -> MEDIUM
        - Otherwise                                            -> LOW
        """
        if (prob is not None and prob >= 0.70) or score > cls.HIGH_THRESHOLD:
            return RiskLevel.HIGH
        elif (prob is not None and prob >= 0.35) or score > cls.LOW_THRESHOLD:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW

    def compute_risk_score(
        self,
        fraud_probability: float,
        transaction_data: Dict[str, Any],
    ) -> RiskScoreResult:
        """Compute application-level 0-100 risk score and factor breakdown.

        Guarantees:
        - Output is always in [0, 100]
        - Deterministic and explainable
        - Strictly independent from fraud probability (fraud_probability is a 0-45 pt contributor, not score = prob * 100)
        """
        factors: List[RiskFactorDetail] = []
        total_score: float = 0.0

        # Safe input extraction across all canonical schemas and aliases
        p = max(0.0, min(1.0, float(fraud_probability)))
        amount = max(0.0, float(transaction_data.get("amount") or transaction_data.get("Amount") or transaction_data.get("transaction_amount") or 0.0))
        merch_avg = max(1.0, float(transaction_data.get("merchant_average_ticket") or transaction_data.get("average_ticket") or 1500.0))
        avg_amount_30d = float(transaction_data.get("customer_historical_avg_amount") or transaction_data.get("Average_Previous_Amount") or transaction_data.get("avg_transaction_amount_30d_customer") or merch_avg)
        vel_1h = max(0.0, float(transaction_data.get("transactions_last_1h") or transaction_data.get("Velocity_1h") or transaction_data.get("transaction_velocity_1h") or 0.0))
        vel_24h = max(0.0, float(transaction_data.get("transactions_last_24h") or transaction_data.get("Velocity_24h") or transaction_data.get("Transactions_Last_24H") or transaction_data.get("transaction_velocity_24h") or 0.0))
        failed_attempts = max(0, int(transaction_data.get("failed_transaction_attempts_24h") or transaction_data.get("failed_login_attempts_24h") or transaction_data.get("Failed_Attempts") or transaction_data.get("Failed_Attempts_Count") or transaction_data.get("failed_attempts") or 0))
        chargebacks = max(0, int(transaction_data.get("previous_chargebacks", 0)))
        account_age = max(0.0, float(transaction_data.get("Account_Age_Days", transaction_data.get("account_age_days", 365.0))))
        is_intl = int(transaction_data.get("International_Transaction", transaction_data.get("is_international", transaction_data.get("Is_International", 0)))) == 1
        is_unusual_loc = int(1 if (transaction_data.get("is_location_changed") is True or transaction_data.get("is_location_changed") == 1 or transaction_data.get("Unusual_Location") == 1 or float(transaction_data.get("location_distance_km", 0) or 0) > 50) else 0)
        is_new_device = int(1 if (transaction_data.get("is_new_device") is True or transaction_data.get("is_new_device") == 1 or transaction_data.get("New_Device") == 1) else 0)
        is_new_bene = int(1 if (transaction_data.get("is_new_beneficiary") is True or transaction_data.get("is_new_beneficiary") == 1) else 0)
        is_high_risk_cat = int(transaction_data.get("is_high_risk_merchant_category", 0)) == 1
        hour = int(transaction_data.get("transaction_hour") or transaction_data.get("Transaction_Hour") or 12)

        # =========================================================================
        # 1. Model Baseline Probability Signal (Max: 60 pts)
        # =========================================================================
        if p >= 0.70:
            model_pts = 45.0 + (p - 0.70) * 50.0  # 45 to 60 pts
            model_pts = min(60.0, model_pts)
            factors.append(RiskFactorDetail(
                factor="ml_model_high_fraud_probability",
                impact_score=round(model_pts, 2),
                severity="HIGH",
                detail=f"Active ML model flagged high fraud probability ({(p * 100):.1f}%)",
            ))
        elif p >= 0.35:
            model_pts = 25.0 + (p - 0.35) * (20.0 / 0.35)  # 25 to 45 pts
            factors.append(RiskFactorDetail(
                factor="ml_model_moderate_fraud_probability",
                impact_score=round(model_pts, 2),
                severity="MEDIUM",
                detail=f"Active ML model indicated elevated fraud risk ({(p * 100):.1f}%)",
            ))
        elif p >= 0.10:
            model_pts = 8.0 + (p - 0.10) * (17.0 / 0.25)
            factors.append(RiskFactorDetail(
                factor="ml_model_baseline",
                impact_score=round(model_pts, 2),
                severity="LOW",
                detail=f"Active ML model probability is baseline ({(p * 100):.1f}%)",
            ))
        else:
            model_pts = p * 80.0  # 0 to 8 pts
            if model_pts > 1.0:
                factors.append(RiskFactorDetail(
                    factor="ml_model_baseline",
                    impact_score=round(model_pts, 2),
                    severity="LOW",
                    detail=f"Active ML model confirmed clean baseline ({(p * 100):.1f}%)",
                ))
        total_score += model_pts

        # =========================================================================
        # 2. Transaction Amount Abnormality Signal (Max: 25 pts)
        # =========================================================================
        amount_ratio = amount / (avg_amount_30d + 1e-5) if avg_amount_30d > 0 else 1.0
        amount_pts = 0.0

        if amount_ratio >= 10.0 or amount >= 100000.0:
            amount_pts = 25.0
            factors.append(RiskFactorDetail(
                factor="extreme_amount_spike",
                impact_score=amount_pts,
                severity="HIGH",
                detail=f"Transaction amount (₹{amount:,.2f}) is {amount_ratio:.1f}x higher than baseline (₹{avg_amount_30d:,.2f})",
            ))
        elif amount_ratio >= 4.0 or amount >= 50000.0:
            amount_pts = 18.0
            factors.append(RiskFactorDetail(
                factor="severe_amount_abnormality",
                impact_score=amount_pts,
                severity="HIGH",
                detail=f"Transaction amount (₹{amount:,.2f}) is {amount_ratio:.1f}x higher than baseline (₹{avg_amount_30d:,.2f})",
            ))
        elif amount_ratio >= 2.0 or amount >= 15000.0:
            amount_pts = 10.0
            factors.append(RiskFactorDetail(
                factor="moderate_amount_abnormality",
                impact_score=amount_pts,
                severity="MEDIUM",
                detail=f"Transaction amount is {amount_ratio:.1f}x baseline (₹{avg_amount_30d:,.2f})",
            ))
        elif amount > 5000.0:
            amount_pts = 5.0
            factors.append(RiskFactorDetail(
                factor="high_absolute_amount",
                impact_score=amount_pts,
                severity="LOW",
                detail=f"Elevated transaction ticket (₹{amount:,.2f})",
            ))
        total_score += amount_pts

        # =========================================================================
        # 3. Transaction Velocity & Burst Acceleration Signal (Max: 20 pts)
        # =========================================================================
        vel_pts = 0.0
        if vel_1h >= 5.0:
            vel_pts = 20.0
            factors.append(RiskFactorDetail(
                factor="extreme_velocity_burst",
                impact_score=vel_pts,
                severity="HIGH",
                detail=f"Critical velocity burst of {int(vel_1h)} transactions in past 1 hour",
            ))
        elif vel_1h >= 3.0:
            vel_pts = 14.0
            factors.append(RiskFactorDetail(
                factor="elevated_velocity_burst",
                impact_score=vel_pts,
                severity="HIGH",
                detail=f"Elevated velocity of {int(vel_1h)} transactions in past 1 hour",
            ))
        elif vel_1h >= 2.0:
            vel_pts = 8.0
            factors.append(RiskFactorDetail(
                factor="moderate_velocity",
                impact_score=vel_pts,
                severity="MEDIUM",
                detail=f"Rapid successive transactions ({int(vel_1h)}) in 1 hour",
            ))
        total_score += vel_pts

        # =========================================================================
        # 4. Beneficiary & History Integrity Signal (Max: 15 pts)
        # =========================================================================
        hist_pts = 0.0
        if chargebacks > 0:
            hist_pts += min(10.0, chargebacks * 5.0)
            factors.append(RiskFactorDetail(
                factor="historical_chargebacks_on_record",
                impact_score=hist_pts,
                severity="HIGH",
                detail=f"Customer account has {chargebacks} recorded chargeback incidents",
            ))
        if account_age < 14.0:
            hist_pts += 5.0
            factors.append(RiskFactorDetail(
                factor="young_account_probation",
                impact_score=5.0,
                severity="MEDIUM",
                detail=f"Account age ({int(account_age)} days) falls in probationary window (< 14 days)",
            ))
        total_score += hist_pts

        # =========================================================================
        # 5. Channel, Device, Beneficiary & Location Risk Signal (Max: 25 pts)
        # =========================================================================
        env_pts = 0.0
        if is_high_risk_cat:
            env_pts += 5.0
            factors.append(RiskFactorDetail(
                factor="high_risk_merchant_category",
                impact_score=5.0,
                severity="MEDIUM",
                detail="Transaction conducted with a designated high-risk merchant category",
            ))

        if is_intl:
            env_pts += 4.0
            factors.append(RiskFactorDetail(
                factor="cross_border_transaction",
                impact_score=4.0,
                severity="LOW",
                detail="Cross-border international payment processing",
            ))

        if is_unusual_loc:
            env_pts += 8.0
            factors.append(RiskFactorDetail(
                factor="unusual_location_authorization",
                impact_score=8.0,
                severity="HIGH",
                detail="Transaction originated from unexpected remote location / distance jump",
            ))

        if is_new_device:
            env_pts += 8.0
            factors.append(RiskFactorDetail(
                factor="new_device_signature",
                impact_score=8.0,
                severity="HIGH",
                detail="Transaction attempted from unrecognized hardware signature",
            ))

        if is_new_bene:
            env_pts += 7.0
            factors.append(RiskFactorDetail(
                factor="new_unrecognized_beneficiary",
                impact_score=7.0,
                severity="MEDIUM",
                detail="First-time transfer to unverified recipient beneficiary",
            ))

        if failed_attempts >= 2:
            env_pts += 8.0
            factors.append(RiskFactorDetail(
                factor="failed_attempts_burst",
                impact_score=8.0,
                severity="HIGH",
                detail=f"Detected {failed_attempts} preceding failed authentication attempts in past 24h",
            ))
        elif failed_attempts == 1:
            env_pts += 3.0
            factors.append(RiskFactorDetail(
                factor="failed_attempt_prior",
                impact_score=3.0,
                severity="LOW",
                detail="One prior failed authentication attempt noted",
            ))

        if hour in [0, 1, 2, 3, 4, 5]:
            env_pts += 4.0
            factors.append(RiskFactorDetail(
                factor="off_hours_night_transaction",
                impact_score=4.0,
                severity="LOW",
                detail=f"Transaction initiated during nocturnal anomaly window ({hour:02d}:00)",
            ))
        total_score += env_pts

        # Final integer clamp strictly [0, 100]
        final_score = int(round(min(100.0, max(0.0, total_score))))

        # Priority guarantee: If ML model flagged critical fraud (p >= 0.70) or amount is astronomical, ensure score reflects HIGH tier (>= 75)
        if (p >= 0.70 or amount_ratio >= 50.0) and final_score < 75:
            final_score = max(final_score, int(round(min(98.0, 75.0 + p * 20.0))))

        risk_level = self.classify_risk_level(final_score)

        return RiskScoreResult(
            risk_score=final_score,
            risk_level=risk_level,
            risk_factors=factors,
        )
