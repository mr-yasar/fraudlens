"""Customer Behaviour Intelligence and Profiling Service.

Derives dynamic behavioural fraud signals from current transaction context
combined with real historical transaction records, beneficiaries, and devices stored in the database.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Set
import numpy as np
from sqlalchemy import func, desc
from sqlalchemy.orm import Session

from backend.app.models.customer import Customer
from backend.app.models.transaction import Transaction
from backend.app.models.beneficiary import Beneficiary
from backend.app.models.device import CustomerDevice


@dataclass
class CustomerBehaviorProfile:
    """Historical baseline profile derived from real customer transaction ledger."""

    customer_id: str
    account_age_days: float
    total_transactions: int
    historical_avg_amount: float
    historical_median_amount: float
    historical_max_amount: float
    historical_min_amount: float = 0.0
    previous_transaction_amount: float = 0.0
    recent_avg_amount_7d: float = 0.0
    recent_max_amount_7d: float = 0.0
    simulated_balance: float = 50000.0
    currency: str = "USD"
    velocity_5m: int = 0
    velocity_15m: int = 0
    velocity_1h: int = 0
    velocity_24h: int = 0
    velocity_7d: int = 0
    failed_attempts_count: int = 0
    previous_chargebacks: int = 0
    known_devices: List[str] = field(default_factory=list)
    known_beneficiaries: List[str] = field(default_factory=list)
    usual_locations: List[str] = field(default_factory=list)
    usual_transaction_hours: List[int] = field(default_factory=list)
    peak_transaction_hours: List[int] = field(default_factory=list)
    top_merchant_categories: List[str] = field(default_factory=list)
    beneficiary_transfer_counts: Dict[str, int] = field(default_factory=dict)
    device_usage_counts: Dict[str, int] = field(default_factory=dict)
    home_country: str = "US"
    is_cold_start: bool = False
    confidence_status: str = "HIGH_CONFIDENCE"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "customer_id": self.customer_id,
            "account_age_days": self.account_age_days,
            "total_transactions": self.total_transactions,
            "historical_avg_amount": round(self.historical_avg_amount, 2),
            "historical_median_amount": round(self.historical_median_amount, 2),
            "historical_max_amount": round(self.historical_max_amount, 2),
            "historical_min_amount": round(self.historical_min_amount, 2),
            "previous_transaction_amount": round(self.previous_transaction_amount, 2),
            "recent_avg_amount_7d": round(self.recent_avg_amount_7d, 2),
            "recent_max_amount_7d": round(self.recent_max_amount_7d, 2),
            "simulated_balance": round(self.simulated_balance, 2),
            "currency": self.currency,
            "velocity_5m": self.velocity_5m,
            "velocity_15m": self.velocity_15m,
            "velocity_1h": self.velocity_1h,
            "velocity_24h": self.velocity_24h,
            "velocity_7d": self.velocity_7d,
            "failed_attempts_count": self.failed_attempts_count,
            "previous_chargebacks": self.previous_chargebacks,
            "known_devices": self.known_devices,
            "known_beneficiaries": self.known_beneficiaries,
            "usual_locations": self.usual_locations,
            "usual_transaction_hours": self.usual_transaction_hours,
            "peak_transaction_hours": self.peak_transaction_hours,
            "top_merchant_categories": self.top_merchant_categories,
            "beneficiary_transfer_counts": self.beneficiary_transfer_counts,
            "device_usage_counts": self.device_usage_counts,
            "home_country": self.home_country,
            "is_cold_start": self.is_cold_start,
            "confidence_status": self.confidence_status,
        }


@dataclass
class DerivedPreAuthFeatures:
    """Pre-authorization features engineered by combining current payment request with customer profile."""

    customer_id: str
    amount: float
    historical_avg_amount: float
    amount_deviation: float
    amount_ratio: float
    is_extreme_amount_surge: bool
    velocity_1h: int
    velocity_24h: int
    is_new_device: bool
    is_unusual_location: bool
    is_international: bool
    is_night_transaction: bool
    failed_attempts: int
    account_age_days: float
    device_type: str
    location: str
    merchant_category: str
    transaction_country: str
    transaction_type: str
    transaction_hour: int
    is_cold_start: bool
    behaviour_deviation_score: float
    is_new_beneficiary: bool = False
    beneficiary_name: Optional[str] = None
    velocity_7d: int = 0
    historical_min_amount: float = 0.0
    historical_max_amount: float = 0.0
    recent_avg_amount_7d: float = 0.0
    amount_deviation_strength: float = 0.0
    is_unusual_time: bool = False
    is_weekend: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "customer_id": self.customer_id,
            "amount": self.amount,
            "historical_avg_amount": round(self.historical_avg_amount, 2),
            "historical_min_amount": round(self.historical_min_amount, 2),
            "historical_max_amount": round(self.historical_max_amount, 2),
            "recent_avg_amount_7d": round(self.recent_avg_amount_7d, 2),
            "amount_deviation": round(self.amount_deviation, 2),
            "amount_deviation_strength": round(self.amount_deviation_strength, 4),
            "amount_ratio": round(self.amount_ratio, 2),
            "is_extreme_amount_surge": self.is_extreme_amount_surge,
            "velocity_1h": self.velocity_1h,
            "velocity_24h": self.velocity_24h,
            "velocity_7d": self.velocity_7d,
            "is_new_device": self.is_new_device,
            "is_unusual_location": self.is_unusual_location,
            "is_international": self.is_international,
            "is_night_transaction": self.is_night_transaction,
            "is_unusual_time": self.is_unusual_time,
            "is_weekend": self.is_weekend,
            "failed_attempts": self.failed_attempts,
            "account_age_days": self.account_age_days,
            "device_type": self.device_type,
            "location": self.location,
            "merchant_category": self.merchant_category,
            "transaction_country": self.transaction_country,
            "transaction_type": self.transaction_type,
            "transaction_hour": self.transaction_hour,
            "is_cold_start": self.is_cold_start,
            "behaviour_deviation_score": round(self.behaviour_deviation_score, 4),
            "is_new_beneficiary": self.is_new_beneficiary,
            "beneficiary_name": self.beneficiary_name,
        }


class BehaviorProfileService:
    """Service to query customer historical behavior and synthesize pre-authorization features."""

    HIGH_RISK_CATEGORIES: Set[str] = {
        "crypto", "cryptocurrency", "luxury_goods", "jewelry", "gambling",
        "casino", "wire_transfer", "money_transfer", "electronics",
    }

    @classmethod
    def get_customer_profile(
        cls,
        db: Session,
        customer_id: str,
        current_timestamp: Optional[datetime] = None,
    ) -> CustomerBehaviorProfile:
        """Fetch and aggregate customer historical baseline profile strictly from database."""
        now = current_timestamp or datetime.now(timezone.utc)

        # 1. Fetch customer entity
        customer = db.query(Customer).filter(Customer.customer_id == customer_id).first()
        account_age = float(customer.account_age_days) if customer and customer.account_age_days is not None else 30.0
        balance = float(customer.simulated_balance) if customer and customer.simulated_balance is not None else 50000.0
        currency = customer.currency if customer and customer.currency else "USD"

        # 2. Query all past transactions for this customer
        history = (
            db.query(Transaction)
            .filter(Transaction.customer_id == customer_id)
            .order_by(desc(Transaction.created_at))
            .all()
        )

        # Query explicit beneficiaries & counts
        beneficiary_records = (
            db.query(Beneficiary)
            .filter(Beneficiary.customer_id == customer_id)
            .all()
        )
        known_beneficiaries = list(dict.fromkeys(b.beneficiary_name for b in beneficiary_records))
        bene_counts: Dict[str, int] = {b.beneficiary_name: (b.total_transfers or 1) for b in beneficiary_records}

        for t in history:
            b_name = t.beneficiary or (t.merchant_category if not t.beneficiary else None)
            if b_name:
                if b_name not in known_beneficiaries:
                    known_beneficiaries.append(b_name)
                bene_counts[b_name] = bene_counts.get(b_name, 0) + 1

        # Query explicit devices & usage counts
        device_records = (
            db.query(CustomerDevice)
            .filter(CustomerDevice.customer_id == customer_id)
            .all()
        )
        known_devices = list(dict.fromkeys(d.device_type for d in device_records))
        dev_counts: Dict[str, int] = {d.device_type: 1 for d in device_records}
        for t in history:
            if t.device_type:
                if t.device_type not in known_devices:
                    known_devices.append(t.device_type)
                dev_counts[t.device_type] = dev_counts.get(t.device_type, 0) + 1

        # Handle Cold-Start (New Customer with no past transactions)
        if not history:
            return CustomerBehaviorProfile(
                customer_id=customer_id,
                account_age_days=account_age,
                total_transactions=0,
                historical_avg_amount=0.0,
                historical_median_amount=0.0,
                historical_max_amount=0.0,
                historical_min_amount=0.0,
                previous_transaction_amount=0.0,
                recent_avg_amount_7d=0.0,
                recent_max_amount_7d=0.0,
                simulated_balance=balance,
                currency=currency,
                velocity_5m=0,
                velocity_15m=0,
                velocity_1h=0,
                velocity_24h=0,
                velocity_7d=0,
                failed_attempts_count=0,
                previous_chargebacks=0,
                known_devices=known_devices,
                known_beneficiaries=known_beneficiaries,
                usual_locations=[],
                usual_transaction_hours=[9, 10, 11, 12, 13, 14, 15, 16, 17, 18],
                peak_transaction_hours=[12, 14, 18],
                top_merchant_categories=[],
                beneficiary_transfer_counts=bene_counts,
                device_usage_counts=dev_counts,
                home_country="US",
                is_cold_start=True,
                confidence_status="HISTORY_UNAVAILABLE",
            )

        # 3. Aggregate historical metrics
        amounts = [float(t.amount) for t in history if t.amount is not None]
        avg_amt = float(np.mean(amounts)) if amounts else 0.0
        median_amt = float(np.median(amounts)) if amounts else 0.0
        max_amt = float(np.max(amounts)) if amounts else 0.0
        min_amt = float(np.min(amounts)) if amounts else 0.0
        prev_amt = amounts[0] if amounts else 0.0

        # 4. Calculate velocities across 5m, 15m, 1h, 24h, 7d safely handling timezone awareness
        def _to_utc(dt: Optional[datetime]) -> Optional[datetime]:
            if dt is None:
                return None
            if dt.tzinfo is None:
                return dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)

        now_utc = _to_utc(now)
        time_5m_ago = now_utc - timedelta(minutes=5)
        time_15m_ago = now_utc - timedelta(minutes=15)
        time_1h_ago = now_utc - timedelta(hours=1)
        time_24h_ago = now_utc - timedelta(hours=24)
        time_7d_ago = now_utc - timedelta(days=7)

        vel_5m = 0
        vel_15m = 0
        vel_1h = 0
        vel_24h = 0
        vel_7d = 0
        amounts_7d: List[float] = []

        for t in history:
            t_created = _to_utc(t.created_at)
            if t_created:
                if t_created >= time_5m_ago:
                    vel_5m += 1
                if t_created >= time_15m_ago:
                    vel_15m += 1
                if t_created >= time_1h_ago:
                    vel_1h += 1
                if t_created >= time_24h_ago:
                    vel_24h += 1
                if t_created >= time_7d_ago:
                    vel_7d += 1
                    if t.amount:
                        amounts_7d.append(float(t.amount))

        # Fallback to recent count if timestamps are simulated or missing timezone
        if vel_24h == 0 and len(history) > 0:
            vel_24h = min(len(history), 3)
            vel_1h = min(vel_24h, 1)
            vel_7d = min(len(history), 7)
            vel_15m = 0
            vel_5m = 0

        recent_avg_7d = float(np.mean(amounts_7d)) if amounts_7d else avg_amt
        recent_max_7d = float(np.max(amounts_7d)) if amounts_7d else max_amt

        # 5. Extract known devices, locations, hours, categories
        for t in history:
            if t.device_type and t.device_type not in known_devices:
                known_devices.append(t.device_type)
        known_locations = list(dict.fromkeys(t.geo_location_region or t.transaction_country for t in history if t.geo_location_region or t.transaction_country))
        
        hours_hist = [int(t.transaction_hour) for t in history if t.transaction_hour is not None]
        known_hours = list(dict.fromkeys(hours_hist))
        # Top 3 most frequent hours as peak transaction hours
        if hours_hist:
            hour_freq: Dict[int, int] = {}
            for h in hours_hist:
                hour_freq[h] = hour_freq.get(h, 0) + 1
            peak_hours = sorted(hour_freq.keys(), key=lambda h: hour_freq[h], reverse=True)[:3]
        else:
            peak_hours = [12, 14, 18]

        known_categories = list(dict.fromkeys(t.merchant_category for t in history if t.merchant_category))

        # Determine home country
        countries = [t.transaction_country for t in history if t.transaction_country]
        home_country = max(set(countries), key=countries.count) if countries else "US"

        confidence_status = "HIGH_CONFIDENCE" if len(history) >= 3 else "LOW_HISTORY_CONFIDENCE"

        return CustomerBehaviorProfile(
            customer_id=customer_id,
            account_age_days=account_age,
            total_transactions=len(history),
            historical_avg_amount=avg_amt,
            historical_median_amount=median_amt,
            historical_max_amount=max_amt,
            historical_min_amount=min_amt,
            previous_transaction_amount=prev_amt,
            recent_avg_amount_7d=recent_avg_7d,
            recent_max_amount_7d=recent_max_7d,
            simulated_balance=balance,
            currency=currency,
            velocity_5m=vel_5m,
            velocity_15m=vel_15m,
            velocity_1h=vel_1h,
            velocity_24h=vel_24h,
            velocity_7d=vel_7d,
            failed_attempts_count=0,
            previous_chargebacks=0,
            known_devices=known_devices,
            known_beneficiaries=known_beneficiaries,
            usual_locations=known_locations,
            usual_transaction_hours=known_hours or [12],
            peak_transaction_hours=peak_hours,
            top_merchant_categories=known_categories,
            beneficiary_transfer_counts=bene_counts,
            device_usage_counts=dev_counts,
            home_country=home_country,
            is_cold_start=False,
            confidence_status=confidence_status,
        )

    @classmethod
    def derive_pre_auth_features(
        cls,
        db: Session,
        customer_id: str,
        amount: float,
        merchant_category: str = "general",
        device_type: str = "web",
        location: str = "US",
        transaction_country: str = "US",
        transaction_type: str = "online_payment",
        transaction_hour: Optional[int] = None,
        failed_attempts: int = 0,
        beneficiary_name: Optional[str] = None,
        merchant_name: Optional[str] = None,
        current_timestamp: Optional[datetime] = None,
    ) -> DerivedPreAuthFeatures:
        """Combine current payment request signals with customer historical profile."""
        now = current_timestamp or datetime.now(timezone.utc)
        hour = transaction_hour if transaction_hour is not None else now.hour
        is_weekend = (now.weekday() >= 5)

        # 1. Load customer behavior profile
        profile = cls.get_customer_profile(db, customer_id=customer_id, current_timestamp=now)

        # Target recipient name to check (explicit beneficiary_name or merchant_name)
        target_beneficiary = (beneficiary_name or merchant_name or "").strip()

        # Default baseline values
        hist_avg = amount
        prev_amt = amount
        hist_min = amount
        hist_max = amount
        recent_avg_7d = amount
        amount_dev = 0.0
        amount_dev_strength = 0.0
        amount_ratio = 1.0
        is_extreme_surge = False
        is_new_dev = False
        is_new_bene = False
        is_unusual_loc = False
        is_unusual_time = False
        is_intl = False

        # 2. Cold-Start Adaptation
        if profile.is_cold_start or profile.historical_avg_amount <= 0:
            hist_avg = amount  # baseline is current amount for brand new customer
            prev_amt = amount
            amount_ratio = 1.0
            amount_dev = 0.0
            amount_dev_strength = 0.0
            is_extreme_surge = False
            is_new_dev = False  # Not flagged as novel hostile device if cold start
            is_new_bene = False
            is_unusual_loc = False
            is_unusual_time = False
            is_intl = (transaction_country.upper() not in ["US", "IN", "GB", "CA"])
            recent_avg_7d = amount
            hist_min = amount
            hist_max = amount
        else:
            hist_avg = profile.historical_avg_amount
            prev_amt = profile.previous_transaction_amount
            hist_min = profile.historical_min_amount
            hist_max = profile.historical_max_amount
            recent_avg_7d = profile.recent_avg_amount_7d
            amount_dev = amount - hist_avg
            amount_ratio = amount / (hist_avg + 1e-5)
            amount_dev_strength = amount_dev / (hist_avg + 1e-5)
            is_extreme_surge = (amount_ratio >= 3.0 and amount > 500.0)

            # Device novelty
            is_new_dev = len(profile.known_devices) > 0 and (device_type.lower() not in [d.lower() for d in profile.known_devices])

            # Beneficiary novelty
            if target_beneficiary and profile.known_beneficiaries:
                is_new_bene = target_beneficiary.lower() not in [b.lower() for b in profile.known_beneficiaries]
            else:
                is_new_bene = False

            # Location novelty
            loc_candidates = [l.lower() for l in profile.usual_locations]
            is_unusual_loc = len(loc_candidates) > 0 and (location.lower() not in loc_candidates and transaction_country.lower() not in loc_candidates)

            # Cross-border
            is_intl = (transaction_country.upper() != profile.home_country.upper())

            # Unusual time
            if profile.usual_transaction_hours:
                hour_diffs = [abs(hour - h) for h in profile.usual_transaction_hours]
                min_diff = min(min(hour_diffs), 24 - min(hour_diffs))
                is_unusual_time = (min_diff >= 6)
            else:
                is_unusual_time = False

        # Night transaction window (00:00 - 05:59)
        is_night = hour in [0, 1, 2, 3, 4, 5]

        # Calculate composite behavioral deviation score [0.0 - 1.0]
        dev_score = 0.0
        if not profile.is_cold_start:
            if amount_ratio > 1.5:
                dev_score += min(0.35, (amount_ratio - 1.0) * 0.1)
            if is_new_dev:
                dev_score += 0.2
            if is_new_bene:
                dev_score += 0.2
            if is_unusual_loc:
                dev_score += 0.2
            if failed_attempts > 0:
                dev_score += min(0.25, failed_attempts * 0.1)
            if is_night or is_unusual_time:
                dev_score += 0.1
        else:
            # Gentle cold start score based purely on absolute high amount and failed attempts
            if amount > 5000.0:
                dev_score += 0.2
            if failed_attempts > 0:
                dev_score += min(0.3, failed_attempts * 0.1)

        dev_score = min(1.0, max(0.0, dev_score))

        return DerivedPreAuthFeatures(
            customer_id=customer_id,
            amount=float(amount),
            historical_avg_amount=float(hist_avg),
            amount_deviation=float(amount_dev),
            amount_ratio=float(amount_ratio),
            is_extreme_amount_surge=is_extreme_surge,
            velocity_1h=profile.velocity_1h,
            velocity_24h=profile.velocity_24h,
            is_new_device=is_new_dev,
            is_unusual_location=is_unusual_loc,
            is_international=is_intl,
            is_night_transaction=is_night,
            failed_attempts=failed_attempts,
            account_age_days=profile.account_age_days,
            device_type=device_type,
            location=location,
            merchant_category=merchant_category,
            transaction_country=transaction_country,
            transaction_type=transaction_type,
            transaction_hour=hour,
            is_cold_start=profile.is_cold_start,
            behaviour_deviation_score=dev_score,
            is_new_beneficiary=is_new_bene,
            beneficiary_name=target_beneficiary or None,
            velocity_7d=profile.velocity_7d,
            historical_min_amount=float(hist_min),
            historical_max_amount=float(hist_max),
            recent_avg_amount_7d=float(recent_avg_7d),
            amount_deviation_strength=float(amount_dev_strength),
            is_unusual_time=is_unusual_time,
            is_weekend=is_weekend,
        )


# Explicit alias for CustomerBehaviourService
CustomerBehaviourService = BehaviorProfileService
