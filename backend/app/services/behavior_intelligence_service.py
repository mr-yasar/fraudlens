"""
Continuous Customer Behaviour Intelligence Service.
Part B: Fraud Intelligence Fabric.

Calculates multi-dimensional customer behavioral baselines, deviation scores,
and explicit signal availability tracking without mutating historical records.
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
from sqlalchemy import func, desc
from sqlalchemy.orm import Session

from backend.app.models.customer import Customer
from backend.app.models.transaction import Transaction
from backend.app.models.payment_intent import PaymentIntent


@dataclass
class SignalStatusMap:
    """Explicit status tracking for pre-auth signals."""
    amount: str = "AVAILABLE"          # AVAILABLE | UNAVAILABLE | INFERRED
    velocity: str = "AVAILABLE"        # AVAILABLE | UNAVAILABLE | INFERRED
    location: str = "AVAILABLE"        # AVAILABLE | UNAVAILABLE | INFERRED
    device: str = "AVAILABLE"          # AVAILABLE | UNAVAILABLE | INFERRED
    session: str = "INFERRED"          # AVAILABLE | UNAVAILABLE | INFERRED
    channel: str = "AVAILABLE"         # AVAILABLE | UNAVAILABLE | INFERRED
    beneficiary: str = "AVAILABLE"     # AVAILABLE | UNAVAILABLE | INFERRED
    cold_start: bool = False


@dataclass
class BehaviourIntelligenceReport:
    """Comprehensive behavioral profile and transaction deviation report."""
    customer_id: str
    is_cold_start: bool
    confidence_level: str              # HIGH | MEDIUM | LOW | COLD_START
    confidence_score: float            # 0.0 - 1.0
    total_historical_transactions: int
    account_age_days: float

    # Statistical Baselines
    historical_avg_amount: float
    historical_median_amount: float
    historical_max_amount: float
    historical_std_amount: float

    # Usual Context Attributes
    usual_transaction_hours: List[int]
    usual_locations: List[str]
    usual_devices: List[str]
    usual_channels: List[str]
    usual_merchant_categories: List[str]
    home_country: str

    # Current Transaction Deviations
    amount_deviation: float
    amount_ratio: float
    timing_deviation_hours: int
    is_unusual_time: bool
    is_unusual_location: bool
    is_new_device: bool
    is_new_beneficiary: bool
    is_cross_border: bool

    # Velocities
    velocity_5m: int
    velocity_15m: int
    velocity_1h: int
    velocity_24h: int
    failed_attempts_count: int

    # Overall Composite Score
    behaviour_deviation_score: float   # 0.0 - 100.0
    behaviour_risk_level: str          # LOW | MEDIUM | HIGH
    signals: Dict[str, Any] = field(default_factory=dict)
    evidence: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class CustomerBehaviourIntelligenceService:
    """Analyzes continuous customer transaction telemetry against historical baselines."""

    POPULATION_AVG_AMOUNT = 120.0
    POPULATION_MEDIAN_AMOUNT = 75.0
    POPULATION_MAX_AMOUNT = 500.0

    @classmethod
    def evaluate_behavior(
        cls,
        db: Session,
        customer_id: str,
        amount: float,
        merchant_name: Optional[str] = None,
        merchant_category: Optional[str] = "retail",
        device_type: Optional[str] = "web",
        device_id: Optional[str] = None,
        location: Optional[str] = "US",
        transaction_country: Optional[str] = "US",
        transaction_type: Optional[str] = "online_payment",
        failed_attempts: int = 0,
        current_timestamp: Optional[datetime] = None,
    ) -> BehaviourIntelligenceReport:
        """
        Derive authoritative customer behavioral intelligence.
        Supports cold-start accounts with safe priors and confidence scaling.
        """
        now = current_timestamp or datetime.now(timezone.utc)
        current_hour = now.hour

        # Fetch Customer record
        customer = db.query(Customer).filter(Customer.customer_id == customer_id).first()
        acc_age = float(customer.account_age_days) if (customer and customer.account_age_days is not None) else 30.0

        # Fetch historical transactions (ordered by recency)
        history = (
            db.query(Transaction)
            .filter(Transaction.customer_id == customer_id)
            .order_by(desc(Transaction.created_at))
            .limit(100)
            .all()
        )

        n_history = len(history)
        is_cold_start = (n_history < 2)

        # Confidence calculation
        if is_cold_start:
            confidence_level = "COLD_START"
            confidence_score = 0.2 if n_history == 1 else 0.0
        elif n_history < 5:
            confidence_level = "LOW"
            confidence_score = round(n_history / 10.0, 2)
        elif n_history < 15:
            confidence_level = "MEDIUM"
            confidence_score = round(0.5 + (n_history / 30.0), 2)
        else:
            confidence_level = "HIGH"
            confidence_score = 1.0

        # Rolling velocities
        t_5m = now - timedelta(minutes=5)
        t_15m = now - timedelta(minutes=15)
        t_1h = now - timedelta(hours=1)
        t_24h = now - timedelta(hours=24)

        vel_5m = 0
        vel_15m = 0
        vel_1h = 0
        vel_24h = 0

        amounts: List[float] = []
        hours_hist: List[int] = []
        locations_hist: List[str] = []
        devices_hist: List[str] = []
        categories_hist: List[str] = []
        merchants_hist: List[str] = []
        countries_hist: List[str] = []

        for tx in history:
            tx_time = tx.created_at
            if tx_time:
                # timezone normalization
                if tx_time.tzinfo is None:
                    tx_time = tx_time.replace(tzinfo=timezone.utc)
                if tx_time >= t_5m:
                    vel_5m += 1
                if tx_time >= t_15m:
                    vel_15m += 1
                if tx_time >= t_1h:
                    vel_1h += 1
                if tx_time >= t_24h:
                    vel_24h += 1

            if tx.amount:
                amounts.append(float(tx.amount))
            if tx.transaction_hour is not None:
                hours_hist.append(int(tx.transaction_hour))
            if tx.geo_location_region:
                locations_hist.append(tx.geo_location_region.strip())
            if tx.device_type:
                devices_hist.append(tx.device_type.strip().lower())
            if tx.merchant_category:
                categories_hist.append(tx.merchant_category.strip().lower())
            if tx.transaction_country:
                countries_hist.append(tx.transaction_country.strip().upper())

        # Also inspect recent PaymentIntents for merchant history and rapid velocity
        recent_intents = (
            db.query(PaymentIntent)
            .filter(PaymentIntent.customer_id == customer_id)
            .order_by(desc(PaymentIntent.created_at))
            .limit(20)
            .all()
        )
        for pi in recent_intents:
            if pi.merchant_name:
                merchants_hist.append(pi.merchant_name.strip().lower())

        # Compute baselines
        if not is_cold_start and amounts:
            avg_amount = float(np.mean(amounts))
            med_amount = float(np.median(amounts))
            max_amount = float(np.max(amounts))
            std_amount = float(np.std(amounts)) if len(amounts) > 1 else (avg_amount * 0.25)
        else:
            avg_amount = cls.POPULATION_AVG_AMOUNT
            med_amount = cls.POPULATION_MEDIAN_AMOUNT
            max_amount = cls.POPULATION_MAX_AMOUNT
            std_amount = 50.0

        # Most frequent historical signals
        usual_hours = list(set(hours_hist)) if hours_hist else [12, 14, 18]
        usual_locations = list(dict.fromkeys(locations_hist))[:5] if locations_hist else ["US"]
        usual_devices = list(dict.fromkeys(devices_hist))[:5] if devices_hist else ["web"]
        usual_categories = list(dict.fromkeys(categories_hist))[:5] if categories_hist else ["retail"]
        home_country = countries_hist[0] if countries_hist else "US"

        # Deviation calculations
        amount_dev = float(amount - avg_amount)
        amount_ratio = float(amount / max(1.0, avg_amount))

        # Timing deviation
        if usual_hours:
            hour_diffs = [abs(current_hour - h) for h in usual_hours]
            min_hour_diff = min(hour_diffs)
            timing_dev_hours = min(min_hour_diff, 24 - min_hour_diff)
            is_unusual_time = (timing_dev_hours >= 6) and (current_hour in [1, 2, 3, 4, 5])
        else:
            timing_dev_hours = 0
            is_unusual_time = False

        # Location deviation
        curr_loc_norm = (location or "US").strip().lower()
        hist_locs_norm = [l.lower() for l in usual_locations]
        is_unusual_location = (curr_loc_norm not in hist_locs_norm) if (not is_cold_start and hist_locs_norm) else False

        # Device novelty
        effective_device = (device_id or device_type or "web").strip().lower()
        hist_devices_norm = [d.lower() for d in usual_devices]
        is_new_device = (effective_device not in hist_devices_norm) if (not is_cold_start and hist_devices_norm) else False

        # Beneficiary / Merchant novelty
        curr_merchant = (merchant_name or "").strip().lower()
        is_new_beneficiary = (curr_merchant not in merchants_hist) if (not is_cold_start and merchants_hist and curr_merchant) else False

        # Cross-border flag
        curr_country = (transaction_country or "US").strip().upper()
        is_cross_border = (curr_country != home_country.upper())

        # Compute continuous Behaviour Deviation Score (0 - 100)
        score_acc = 0.0
        evidence: List[str] = []

        # 1. Amount Deviation component (0-40 pts)
        if amount_ratio > 5.0:
            score_acc += 40.0
            evidence.append(f"Amount (${amount:,.2f}) is {amount_ratio:.1f}x above customer baseline (${avg_amount:,.2f}).")
        elif amount_ratio > 3.0:
            score_acc += 25.0
            evidence.append(f"Amount (${amount:,.2f}) is {amount_ratio:.1f}x higher than usual average (${avg_amount:,.2f}).")
        elif amount_ratio > 2.0:
            score_acc += 12.0
            evidence.append(f"Moderate amount increase ({amount_ratio:.1f}x of baseline).")

        # 2. Velocity spike component (0-25 pts)
        if vel_5m >= 3:
            score_acc += 25.0
            evidence.append(f"Rapid velocity burst: {vel_5m} transactions attempted in the last 5 minutes.")
        elif vel_1h >= 4:
            score_acc += 18.0
            evidence.append(f"Elevated hourly velocity: {vel_1h} transactions in the last hour.")
        elif vel_24h >= 8:
            score_acc += 10.0
            evidence.append(f"High 24h transaction volume ({vel_24h} attempts).")

        # 3. Device novelty (0-15 pts)
        if is_new_device:
            score_acc += 15.0
            evidence.append(f"Transaction originated from an unrecognized device ('{effective_device}').")

        # 4. Location & International anomaly (0-15 pts)
        if is_cross_border:
            score_acc += 12.0
            evidence.append(f"Cross-border payment origin ({curr_country}) mismatches home account ({home_country}).")
        elif is_unusual_location:
            score_acc += 8.0
            evidence.append(f"Geographic location '{location}' is novel for this customer profile.")

        # 5. Failed authentication velocity (0-15 pts)
        if failed_attempts >= 3:
            score_acc += 15.0
            evidence.append(f"Multiple failed authentication attempts ({failed_attempts}) preceding checkout.")
        elif failed_attempts >= 1:
            score_acc += 6.0
            evidence.append(f"{failed_attempts} failed attempt recorded in current session.")

        # Cold start adjustment
        if is_cold_start:
            # Scale score by cold-start baseline factor so new customers are not falsely hard-blocked
            score_acc = min(55.0, score_acc * 0.75)
            evidence.append("Cold-start profile: Evaluated against population baselines with adjusted confidence.")

        final_dev_score = min(100.0, max(0.0, round(score_acc, 2)))

        if final_dev_score >= 70.0:
            risk_tier = "HIGH"
        elif final_dev_score >= 35.0:
            risk_tier = "MEDIUM"
        else:
            risk_tier = "LOW"

        signal_status = SignalStatusMap(
            amount="AVAILABLE",
            velocity="AVAILABLE",
            location="AVAILABLE",
            device="AVAILABLE" if device_id or device_type else "INFERRED",
            session="AVAILABLE" if failed_attempts > 0 else "INFERRED",
            channel="AVAILABLE",
            beneficiary="AVAILABLE" if merchant_name else "UNAVAILABLE",
            cold_start=is_cold_start,
        )

        return BehaviourIntelligenceReport(
            customer_id=customer_id,
            is_cold_start=is_cold_start,
            confidence_level=confidence_level,
            confidence_score=confidence_score,
            total_historical_transactions=n_history,
            account_age_days=acc_age,
            historical_avg_amount=round(avg_amount, 2),
            historical_median_amount=round(med_amount, 2),
            historical_max_amount=round(max_amount, 2),
            historical_std_amount=round(std_amount, 2),
            usual_transaction_hours=usual_hours,
            usual_locations=usual_locations,
            usual_devices=usual_devices,
            usual_channels=["web", "mobile_app"],
            usual_merchant_categories=usual_categories,
            home_country=home_country,
            amount_deviation=round(amount_dev, 2),
            amount_ratio=round(amount_ratio, 2),
            timing_deviation_hours=timing_dev_hours,
            is_unusual_time=is_unusual_time,
            is_unusual_location=is_unusual_location,
            is_new_device=is_new_device,
            is_new_beneficiary=is_new_beneficiary,
            is_cross_border=is_cross_border,
            velocity_5m=vel_5m,
            velocity_15m=vel_15m,
            velocity_1h=vel_1h,
            velocity_24h=vel_24h,
            failed_attempts_count=failed_attempts,
            behaviour_deviation_score=final_dev_score,
            behaviour_risk_level=risk_tier,
            signals=asdict(signal_status),
            evidence=evidence,
        )
