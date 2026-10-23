"""UPI Daily Limit and Fallback Policy Service.

Enforces application-specific daily transaction limits:
- Overall UPI daily limit: ₹5,00,000 per user/account.
- UPI merchant daily limit: ₹1,49,000 per user/account.

Tracks usage over a consistent rolling 24-hour accounting window.
Concurrency-safe with thread synchronization and database transactional queries.
Failed, cancelled, and rejected transactions do not count towards usage.
"""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
import logging
import threading
from typing import Any, Dict, Optional, Tuple

from sqlalchemy.orm import Session
from backend.app.models.transaction import Transaction

logger = logging.getLogger(__name__)

# Business Rule Configuration
OVERALL_UPI_DAILY_LIMIT: float = 500000.0   # ₹5,00,000 per user/account
MERCHANT_UPI_DAILY_LIMIT: float = 149000.0  # ₹1,49,000 per user/account
DEFAULT_WINDOW_HOURS: int = 24

# Concurrency mutex per customer to prevent race conditions during simultaneous payment submissions
_customer_locks: Dict[str, threading.RLock] = {}
_lock_registry_mutex = threading.Lock()


def get_customer_lock(customer_id: str) -> threading.RLock:
    """Return an isolated re-entrant lock for the given customer identifier."""
    norm_id = (customer_id or "").strip().upper()
    with _lock_registry_mutex:
        if norm_id not in _customer_locks:
            _customer_locks[norm_id] = threading.RLock()
        return _customer_locks[norm_id]


class UpiDailyLimitService:
    """Centralized service for managing and validating daily UPI limits and card fallback."""

    OVERALL_LIMIT = OVERALL_UPI_DAILY_LIMIT
    MERCHANT_LIMIT = MERCHANT_UPI_DAILY_LIMIT
    WINDOW_HOURS = DEFAULT_WINDOW_HOURS

    # Qualifying transaction statuses that represent successful payments
    SUCCESS_STATUSES = ("SUCCESS", "COMPLETED", "APPROVED", "SUCCEEDED")

    @classmethod
    def is_upi_channel(cls, payment_channel_or_method: Optional[str]) -> bool:
        """Check whether the payment channel represents a UPI transaction."""
        if not payment_channel_or_method:
            return False
        val = str(payment_channel_or_method).strip().lower()
        return val in (
            "upi",
            "vpa",
            "upi_transfer",
            "bhim_upi",
            "googlepay",
            "phonepe",
            "paytm_upi",
        )

    @classmethod
    def is_merchant_transaction(
        cls,
        transaction_type: Optional[str] = None,
        merchant_category: Optional[str] = None,
    ) -> bool:
        """Determine whether a transaction qualifies as a merchant payment.

        Merchant UPI transactions count toward both overall UPI and merchant limit.
        Personal transfers (P2P, peer_to_peer, self_transfer) count only toward overall UPI.
        """
        tt = (transaction_type or "").strip().lower()
        mc = (merchant_category or "").strip().lower()

        # Non-merchant / personal transfers
        if tt in ("personal", "p2p", "peer_to_peer", "self_transfer", "family_transfer", "friend_transfer"):
            return False
        if mc in ("personal", "p2p", "peer_to_peer", "self_transfer"):
            return False

        # Any commercial/merchant category or transaction type is considered a merchant payment
        return True

    @classmethod
    def get_upi_daily_usage(
        cls,
        db: Session,
        customer_id: str,
        window_hours: int = DEFAULT_WINDOW_HOURS,
        as_of_time: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Compute the current UPI usage and remaining limits for a customer within the rolling 24-hour window.

        Only successful transactions count toward the limit.
        """
        now_utc = as_of_time or datetime.now(timezone.utc)
        if now_utc.tzinfo is None:
            now_utc = now_utc.replace(tzinfo=timezone.utc)

        cutoff_time = now_utc - timedelta(hours=window_hours)

        # Query all transactions for this customer within the window
        # Querying by customer_id
        txs = (
            db.query(Transaction)
            .filter(
                Transaction.customer_id == customer_id,
            )
            .all()
        )

        overall_used = Decimal("0.00")
        merchant_used = Decimal("0.00")
        oldest_tx_time: Optional[datetime] = None

        for tx in txs:
            # Check status: failed, cancelled, rejected, blocked must not count
            tx_status = (tx.status or "").upper()
            if tx_status not in cls.SUCCESS_STATUSES:
                continue

            # Check timestamp against rolling window
            created_at = tx.created_at
            if created_at is None:
                continue
            if created_at.tzinfo is None:
                created_at = created_at.replace(tzinfo=timezone.utc)

            if created_at < cutoff_time or created_at > now_utc:
                continue

            # Check if this transaction is UPI
            if not cls.is_upi_channel(tx.payment_channel):
                continue

            amount = Decimal(str(tx.amount or 0))
            overall_used += amount

            # Track earliest qualifying UPI transaction for dynamic reset calculation
            if oldest_tx_time is None or created_at < oldest_tx_time:
                oldest_tx_time = created_at

            # Check if merchant
            if cls.is_merchant_transaction(tx.transaction_type, tx.merchant_category):
                merchant_used += amount

        overall_used_float = float(round(overall_used, 2))
        merchant_used_float = float(round(merchant_used, 2))

        overall_remaining_float = float(max(Decimal("0.00"), Decimal(str(cls.OVERALL_LIMIT)) - overall_used))
        merchant_remaining_float = float(max(Decimal("0.00"), Decimal(str(cls.MERCHANT_LIMIT)) - merchant_used))

        # Reset time: When oldest qualifying transaction rolls out of 24h window
        if oldest_tx_time:
            reset_time = oldest_tx_time + timedelta(hours=window_hours)
            if reset_time <= now_utc:
                reset_time = now_utc + timedelta(hours=window_hours)
        else:
            reset_time = now_utc + timedelta(hours=window_hours)

        reset_time_iso = reset_time.isoformat()
        reset_time_human = reset_time.strftime("%d %b %Y, %I:%M %p UTC")

        return {
            "customer_id": customer_id,
            "window_hours": window_hours,
            "overall_limit": cls.OVERALL_LIMIT,
            "overall_used": overall_used_float,
            "overall_remaining": overall_remaining_float,
            "overall_limit_reached": overall_used_float >= cls.OVERALL_LIMIT,
            "merchant_limit": cls.MERCHANT_LIMIT,
            "merchant_used": merchant_used_float,
            "merchant_remaining": merchant_remaining_float,
            "merchant_limit_reached": merchant_used_float >= cls.MERCHANT_LIMIT,
            "reset_time": reset_time_iso,
            "reset_time_human": reset_time_human,
            "card_fallback_available": True,
        }

    @classmethod
    def validate_upi_transaction(
        cls,
        db: Session,
        customer_id: str,
        amount: float,
        payment_method: Optional[str] = "upi",
        transaction_type: Optional[str] = None,
        merchant_category: Optional[str] = None,
        as_of_time: Optional[datetime] = None,
    ) -> Tuple[bool, Optional[Dict[str, Any]], Dict[str, Any]]:
        """Validate whether a prospective transaction satisfies UPI daily limits.

        Returns:
            Tuple of:
            - is_allowed (bool): True if payment can proceed, False if blocked by daily limit.
            - violation_detail (Optional[Dict]): Details of the breached limit with exact modal titles and text.
            - current_usage (Dict): Current usage statistics.
        """
        # Non-UPI payments (e.g., credit card, debit card, net banking) are exempt from UPI limits
        if not cls.is_upi_channel(payment_method):
            usage = cls.get_upi_daily_usage(db, customer_id, as_of_time=as_of_time)
            return True, None, usage

        amt_decimal = Decimal(str(amount))
        if amt_decimal <= 0:
            usage = cls.get_upi_daily_usage(db, customer_id, as_of_time=as_of_time)
            return True, None, usage

        is_merchant = cls.is_merchant_transaction(transaction_type, merchant_category)

        # Thread-safe lock per customer to prevent concurrent requests from bypassing limits
        lock = get_customer_lock(customer_id)
        with lock:
            usage = cls.get_upi_daily_usage(db, customer_id, as_of_time=as_of_time)

            curr_overall_used = Decimal(str(usage["overall_used"]))
            curr_merchant_used = Decimal(str(usage["merchant_used"]))

            overall_limit_dec = Decimal(str(cls.OVERALL_LIMIT))
            merchant_limit_dec = Decimal(str(cls.MERCHANT_LIMIT))

            new_overall = curr_overall_used + amt_decimal
            new_merchant = curr_merchant_used + amt_decimal if is_merchant else curr_merchant_used

            # 1. Check Overall UPI Daily Limit (₹5,00,000)
            if new_overall > overall_limit_dec or usage["overall_limit_reached"]:
                violation = {
                    "limit_type": "OVERALL",
                    "title": "Daily UPI Limit Reached",
                    "message": (
                        "You have reached your daily UPI payment limit of ₹5,00,000.\n\n"
                        "UPI payments are unavailable for the remainder of the applicable limit period. "
                        "To continue with this transaction, please select Card Payment."
                    ),
                    "applicable_limit": cls.OVERALL_LIMIT,
                    "amount_used": usage["overall_used"],
                    "remaining_amount": usage["overall_remaining"],
                    "requested_amount": float(amt_decimal),
                    "reset_time": usage["reset_time"],
                    "reset_time_human": usage["reset_time_human"],
                    "card_fallback_available": True,
                }
                return False, violation, usage

            # 2. Check Merchant UPI Daily Limit (₹1,49,000) for merchant transactions
            if is_merchant and (new_merchant > merchant_limit_dec or usage["merchant_limit_reached"]):
                violation = {
                    "limit_type": "MERCHANT",
                    "title": "Merchant UPI Limit Reached",
                    "message": (
                        "Your daily merchant UPI limit of ₹1,49,000 has been reached.\n\n"
                        "Please use Card Payment to continue with this merchant transaction."
                    ),
                    "applicable_limit": cls.MERCHANT_LIMIT,
                    "amount_used": usage["merchant_used"],
                    "remaining_amount": usage["merchant_remaining"],
                    "requested_amount": float(amt_decimal),
                    "reset_time": usage["reset_time"],
                    "reset_time_human": usage["reset_time_human"],
                    "card_fallback_available": True,
                }
                return False, violation, usage

            return True, None, usage
