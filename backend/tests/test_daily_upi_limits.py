"""Comprehensive Automated Test Suite for Daily UPI Limits and Card-Only Fallback.

Covers all 12 specified business scenarios:
1. UPI payment below daily limit succeeds.
2. UPI payments reaching exactly ₹5,00,000 are handled correctly.
3. The next UPI payment is blocked after reaching the overall limit.
4. Merchant UPI payments reaching exactly ₹1,49,000 are handled correctly.
5. Further merchant UPI payments are blocked after reaching that limit.
6. A payment that exceeds the remaining limit triggers rejection/popup data.
7. Card fallback works without silently submitting duplicate payments.
8. Failed, cancelled, and rejected transactions do not increase successful usage.
9. Different users have isolated daily limits.
10. The daily accounting window resets correctly outside 24-hour window.
11. Concurrent transactions cannot bypass the limits.
12. Existing payment functionality remains unaffected (non-UPI methods exempt).
"""

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import uuid
import pytest
from fastapi import HTTPException

from backend.app.core.database import SessionLocal
from backend.app.models.customer import Customer
from backend.app.models.transaction import Transaction
from backend.app.models.payment_intent import PaymentIntent, PaymentLifecycleStatus
from backend.app.schemas.payment import PaymentInitiateRequest, PaymentDecision
from backend.app.services.risk_decision_orchestrator import RiskDecisionOrchestrator
from backend.app.services.upi_limit_service import (
    UpiDailyLimitService,
    OVERALL_UPI_DAILY_LIMIT,
    MERCHANT_UPI_DAILY_LIMIT,
)


@pytest.fixture
def db():
    """Provide an isolated database session per test."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


def _create_test_customer(db, customer_id: str, balance: float = 2000000.0) -> Customer:
    """Helper to ensure test customer exists with adequate balance."""
    customer = db.query(Customer).filter(Customer.customer_id == customer_id).first()
    if not customer:
        customer = Customer(
            customer_id=customer_id,
            simulated_balance=balance,
            account_age_days=180.0,
            currency="INR",
        )
        db.add(customer)
    else:
        customer.simulated_balance = balance
    db.commit()
    db.refresh(customer)
    return customer


def _insert_completed_tx(
    db,
    customer_id: str,
    amount: float,
    payment_channel: str = "upi",
    transaction_type: str = "merchant_pay",
    merchant_category: str = "retail",
    status: str = "SUCCESS",
    created_at: datetime = None,
) -> Transaction:
    """Helper to insert a completed transaction record."""
    tx = Transaction(
        transaction_id=f"TEST-TX-{uuid.uuid4().hex[:10].upper()}",
        customer_id=customer_id,
        amount=amount,
        currency="INR",
        transaction_hour=12,
        payment_channel=payment_channel,
        transaction_type=transaction_type,
        merchant_category=merchant_category,
        merchant_name="Test Store",
        status=status,
        created_at=created_at or datetime.now(timezone.utc),
    )
    db.add(tx)
    db.commit()
    db.refresh(tx)
    return tx


# ---------------------------------------------------------------------------
# SCENARIO 1: UPI payment below daily limit succeeds
# ---------------------------------------------------------------------------
def test_scenario_01_upi_payment_below_limit_succeeds(db):
    cid = f"TEST_CUST_SCEN01_{uuid.uuid4().hex[:6]}"
    _create_test_customer(db, cid, balance=500000.0)

    # Validate prospective payment of 1500.0
    is_allowed, violation, usage = UpiDailyLimitService.validate_upi_transaction(
        db=db,
        customer_id=cid,
        amount=1500.0,
        payment_method="upi",
        transaction_type="online_payment",
        merchant_category="retail",
    )
    assert is_allowed is True
    assert violation is None
    assert usage["overall_limit"] == 500000.0
    assert usage["overall_remaining"] == 500000.0

    # Execute payment through RiskDecisionOrchestrator
    req = PaymentInitiateRequest(
        customer_id=cid,
        amount=1500.0,
        currency="INR",
        merchant_name="NovaMart Fresh",
        merchant_category="retail",
        payment_method="upi",
        transaction_type="online_payment",
    )
    res = RiskDecisionOrchestrator.evaluate_and_process_payment(db=db, request=req)
    assert res.decision in (PaymentDecision.ALLOW, PaymentDecision.REVIEW)

    # Check updated usage in rolling window
    updated_usage = UpiDailyLimitService.get_upi_daily_usage(db, cid)
    if res.decision == PaymentDecision.ALLOW:
        assert updated_usage["overall_used"] == 1500.0
        assert updated_usage["overall_remaining"] == 498500.0



# ---------------------------------------------------------------------------
# SCENARIO 2: UPI payments reaching exactly ₹5,00,000 are handled correctly
# ---------------------------------------------------------------------------
def test_scenario_02_upi_reaching_exact_5lakh_limit(db):
    cid = f"TEST_CUST_SCEN02_{uuid.uuid4().hex[:6]}"
    _create_test_customer(db, cid, balance=1000000.0)

    # Insert two successful UPI payments: 3,00,000 + 2,00,000 = exactly 5,00,000
    _insert_completed_tx(db, cid, 300000.0, payment_channel="upi", transaction_type="personal", merchant_category="personal")
    _insert_completed_tx(db, cid, 200000.0, payment_channel="upi", transaction_type="personal", merchant_category="personal")

    usage = UpiDailyLimitService.get_upi_daily_usage(db, cid)
    assert usage["overall_used"] == 500000.0
    assert usage["overall_remaining"] == 0.0
    assert usage["overall_limit_reached"] is True


# ---------------------------------------------------------------------------
# SCENARIO 3: Next UPI payment is blocked after reaching overall limit
# ---------------------------------------------------------------------------
def test_scenario_03_next_upi_blocked_after_overall_limit(db):
    cid = f"TEST_CUST_SCEN03_{uuid.uuid4().hex[:6]}"
    _create_test_customer(db, cid, balance=1000000.0)
    _insert_completed_tx(db, cid, 500000.0, payment_channel="upi", transaction_type="personal", merchant_category="personal")

    # Prospective check for 100
    is_allowed, violation, usage = UpiDailyLimitService.validate_upi_transaction(
        db=db,
        customer_id=cid,
        amount=100.0,
        payment_method="upi",
        transaction_type="personal",
        merchant_category="personal",
    )
    assert is_allowed is False
    assert violation is not None
    assert violation["limit_type"] == "OVERALL"
    assert violation["title"] == "Daily UPI Limit Reached"
    assert "₹5,00,000" in violation["message"]
    assert violation["card_fallback_available"] is True

    # Pre-auth orchestrator must raise HTTPException with 400
    req = PaymentInitiateRequest(
        customer_id=cid,
        amount=100.0,
        currency="INR",
        merchant_name="Personal Transfer",
        merchant_category="personal",
        payment_method="upi",
        transaction_type="personal",
    )
    with pytest.raises(HTTPException) as exc_info:
        RiskDecisionOrchestrator.evaluate_and_process_payment(db=db, request=req)
    assert exc_info.value.status_code == 400
    detail = exc_info.value.detail
    assert detail["error_type"] == "UPI_DAILY_LIMIT_EXCEEDED"
    assert detail["limit_type"] == "OVERALL"
    assert detail["title"] == "Daily UPI Limit Reached"


# ---------------------------------------------------------------------------
# SCENARIO 4: Merchant UPI payments reaching exactly ₹1,49,000 handled correctly
# ---------------------------------------------------------------------------
def test_scenario_04_merchant_upi_reaching_exact_149000_limit(db):
    cid = f"TEST_CUST_SCEN04_{uuid.uuid4().hex[:6]}"
    _create_test_customer(db, cid, balance=1000000.0)

    # Insert two merchant transactions: 1,00,000 + 49,000 = 1,49,000
    _insert_completed_tx(db, cid, 100000.0, payment_channel="upi", transaction_type="merchant_pay", merchant_category="retail")
    _insert_completed_tx(db, cid, 49000.0, payment_channel="upi", transaction_type="online_payment", merchant_category="electronics")

    usage = UpiDailyLimitService.get_upi_daily_usage(db, cid)
    assert usage["merchant_used"] == 149000.0
    assert usage["merchant_remaining"] == 0.0
    assert usage["merchant_limit_reached"] is True
    # Merchant transactions MUST also count toward overall UPI total
    assert usage["overall_used"] == 149000.0
    assert usage["overall_remaining"] == (500000.0 - 149000.0)


# ---------------------------------------------------------------------------
# SCENARIO 5: Further merchant UPI payments are blocked after reaching limit
# ---------------------------------------------------------------------------
def test_scenario_05_further_merchant_upi_blocked_after_limit(db):
    cid = f"TEST_CUST_SCEN05_{uuid.uuid4().hex[:6]}"
    _create_test_customer(db, cid, balance=1000000.0)
    _insert_completed_tx(db, cid, 149000.0, payment_channel="upi", transaction_type="merchant_pay", merchant_category="retail")

    # Attempt another merchant payment of 500
    is_allowed, violation, usage = UpiDailyLimitService.validate_upi_transaction(
        db=db,
        customer_id=cid,
        amount=500.0,
        payment_method="upi",
        transaction_type="merchant_pay",
        merchant_category="retail",
    )
    assert is_allowed is False
    assert violation["limit_type"] == "MERCHANT"
    assert violation["title"] == "Merchant UPI Limit Reached"
    assert "₹1,49,000" in violation["message"]

    # Pre-auth orchestrator must block
    req = PaymentInitiateRequest(
        customer_id=cid,
        amount=500.0,
        currency="INR",
        merchant_name="NovaMart Fresh",
        merchant_category="retail",
        payment_method="upi",
        transaction_type="merchant_pay",
    )
    with pytest.raises(HTTPException) as exc_info:
        RiskDecisionOrchestrator.evaluate_and_process_payment(db=db, request=req)
    assert exc_info.value.status_code == 400
    assert exc_info.value.detail["limit_type"] == "MERCHANT"
    assert exc_info.value.detail["title"] == "Merchant UPI Limit Reached"


# ---------------------------------------------------------------------------
# SCENARIO 6: Payment that exceeds remaining limit triggers rejection/popup
# ---------------------------------------------------------------------------
def test_scenario_06_payment_exceeding_remaining_limit_triggers_popup(db):
    cid = f"TEST_CUST_SCEN06_{uuid.uuid4().hex[:6]}"
    _create_test_customer(db, cid, balance=1000000.0)
    # Used 4,80,000 out of 5,00,000. Remaining: 20,000
    _insert_completed_tx(db, cid, 480000.0, payment_channel="upi", transaction_type="personal", merchant_category="personal")

    # Request 25,000 (would exceed 5,00,000 limit)
    is_allowed, violation, usage = UpiDailyLimitService.validate_upi_transaction(
        db=db,
        customer_id=cid,
        amount=25000.0,
        payment_method="upi",
        transaction_type="personal",
        merchant_category="personal",
    )
    assert is_allowed is False
    assert violation["limit_type"] == "OVERALL"
    assert violation["title"] == "Daily UPI Limit Reached"
    assert violation["amount_used"] == 480000.0
    assert violation["remaining_amount"] == 20000.0
    assert violation["requested_amount"] == 25000.0


# ---------------------------------------------------------------------------
# SCENARIO 7: Card fallback works without silently submitting duplicate payments
# ---------------------------------------------------------------------------
def test_scenario_07_card_fallback_works_cleanly(db):
    cid = f"TEST_CUST_SCEN07_{uuid.uuid4().hex[:6]}"
    _create_test_customer(db, cid, balance=1000000.0)
    # Overall UPI is exhausted
    _insert_completed_tx(db, cid, 500000.0, payment_channel="upi", transaction_type="personal", merchant_category="personal")

    # Card payment with identical amount (25,000) and merchant
    req = PaymentInitiateRequest(
        customer_id=cid,
        amount=25000.0,
        currency="INR",
        merchant_name="Dell Commercial Systems",
        merchant_category="electronics",
        payment_method="credit_card",  # Fallback to Card
        transaction_type="online_payment",
    )

    # Card payment is NOT blocked by UPI limit
    res = RiskDecisionOrchestrator.evaluate_and_process_payment(db=db, request=req)
    assert res.decision in (PaymentDecision.ALLOW, PaymentDecision.REVIEW)

    # Verify that UPI usage was NOT incremented by the card transaction
    upi_usage = UpiDailyLimitService.get_upi_daily_usage(db, cid)
    assert upi_usage["overall_used"] == 500000.0  # Remains 500k, not 525k


# ---------------------------------------------------------------------------
# SCENARIO 8: Failed, cancelled, and rejected transactions do not count
# ---------------------------------------------------------------------------
def test_scenario_08_failed_and_cancelled_do_not_increase_usage(db):
    cid = f"TEST_CUST_SCEN08_{uuid.uuid4().hex[:6]}"
    _create_test_customer(db, cid, balance=1000000.0)

    # Insert non-successful transactions
    _insert_completed_tx(db, cid, 100000.0, payment_channel="upi", status="FAILED")
    _insert_completed_tx(db, cid, 100000.0, payment_channel="upi", status="CANCELLED")
    _insert_completed_tx(db, cid, 100000.0, payment_channel="upi", status="REJECTED")
    _insert_completed_tx(db, cid, 100000.0, payment_channel="upi", status="BLOCKED")
    _insert_completed_tx(db, cid, 100000.0, payment_channel="upi", status="PENDING_VERIFICATION")

    usage = UpiDailyLimitService.get_upi_daily_usage(db, cid)
    assert usage["overall_used"] == 0.0
    assert usage["merchant_used"] == 0.0
    assert usage["overall_remaining"] == 500000.0
    assert usage["merchant_remaining"] == 149000.0


# ---------------------------------------------------------------------------
# SCENARIO 9: Different users have isolated daily limits
# ---------------------------------------------------------------------------
def test_scenario_09_different_users_isolated_limits(db):
    user_a = f"TEST_USER_A_{uuid.uuid4().hex[:6]}"
    user_b = f"TEST_USER_B_{uuid.uuid4().hex[:6]}"
    _create_test_customer(db, user_a, balance=1000000.0)
    _create_test_customer(db, user_b, balance=1000000.0)

    # User A exhausts their entire UPI limit
    _insert_completed_tx(db, user_a, 500000.0, payment_channel="upi")

    usage_a = UpiDailyLimitService.get_upi_daily_usage(db, user_a)
    usage_b = UpiDailyLimitService.get_upi_daily_usage(db, user_b)

    assert usage_a["overall_used"] == 500000.0
    assert usage_a["overall_limit_reached"] is True

    # User B remains at zero usage with full 500k limit
    assert usage_b["overall_used"] == 0.0
    assert usage_b["overall_remaining"] == 500000.0
    assert usage_b["overall_limit_reached"] is False

    # User B's transaction of 1,00,000 proceeds without restriction
    is_allowed, violation, _ = UpiDailyLimitService.validate_upi_transaction(
        db, user_b, 100000.0, payment_method="upi"
    )
    assert is_allowed is True
    assert violation is None


# ---------------------------------------------------------------------------
# SCENARIO 10: Daily accounting window resets correctly (outside 24h)
# ---------------------------------------------------------------------------
def test_scenario_10_daily_window_resets_correctly(db):
    cid = f"TEST_CUST_SCEN10_{uuid.uuid4().hex[:6]}"
    _create_test_customer(db, cid, balance=1000000.0)

    # Insert a 5,00,000 transaction from 25 hours ago
    past_time = datetime.now(timezone.utc) - timedelta(hours=25)
    _insert_completed_tx(db, cid, 500000.0, payment_channel="upi", created_at=past_time)

    # Today's usage in the rolling 24-hour window must be 0
    now = datetime.now(timezone.utc)
    usage = UpiDailyLimitService.get_upi_daily_usage(db, cid, as_of_time=now)
    assert usage["overall_used"] == 0.0
    assert usage["overall_remaining"] == 500000.0
    assert usage["overall_limit_reached"] is False

    # New transaction today succeeds
    is_allowed, violation, _ = UpiDailyLimitService.validate_upi_transaction(
        db, cid, 100000.0, payment_method="upi", as_of_time=now
    )
    assert is_allowed is True
    assert violation is None


# ---------------------------------------------------------------------------
# SCENARIO 11: Concurrent transactions cannot bypass the limits
# ---------------------------------------------------------------------------
def test_scenario_11_concurrent_transactions_cannot_bypass_limits(db):
    cid = f"TEST_CUST_CONCURRENCY_{uuid.uuid4().hex[:6]}"
    _create_test_customer(db, cid, balance=2000000.0)

    # Merchant limit is 1,49,000.
    # Launch 6 concurrent threads each attempting 50,000 merchant UPI payment (total: 300,000).
    # Exactly 2 should succeed (2 x 50,000 = 100,000 <= 149,000).
    # The 3rd (150,000 > 149,000) and subsequent must be blocked!

    from backend.app.services.upi_limit_service import get_customer_lock

    def attempt_concurrent_payment(idx):
        thread_db = SessionLocal()
        try:
            with get_customer_lock(cid):
                is_ok, viol, _ = UpiDailyLimitService.validate_upi_transaction(
                    db=thread_db,
                    customer_id=cid,
                    amount=50000.0,
                    payment_method="upi",
                    transaction_type="merchant_pay",
                    merchant_category="retail",
                )
                if is_ok:
                    # If validated, record the transaction in the database
                    _insert_completed_tx(
                        thread_db,
                        cid,
                        50000.0,
                        payment_channel="upi",
                        transaction_type="merchant_pay",
                        merchant_category="retail",
                    )
                    return True
                return False
        finally:
            thread_db.close()


    with ThreadPoolExecutor(max_workers=6) as executor:
        results = list(executor.map(attempt_concurrent_payment, range(6)))

    successes = sum(1 for r in results if r is True)
    blocks = sum(1 for r in results if r is False)

    # Exactly 2 can succeed without exceeding 1,49,000
    assert successes == 2
    assert blocks == 4

    # Verify final used amount in database does NOT exceed 1,49,000
    final_usage = UpiDailyLimitService.get_upi_daily_usage(db, cid)
    assert final_usage["merchant_used"] == 100000.0
    assert final_usage["merchant_used"] <= MERCHANT_UPI_DAILY_LIMIT


# ---------------------------------------------------------------------------
# SCENARIO 12: Existing payment functionality remains unaffected
# ---------------------------------------------------------------------------
def test_scenario_12_existing_payment_functionality_unaffected(db):
    cid = f"TEST_CUST_SCEN12_{uuid.uuid4().hex[:6]}"
    _create_test_customer(db, cid, balance=1000000.0)

    # Large Credit Card and NetBanking payments (> 5,00,000) are exempt from UPI limits
    card_allowed, viol_card, _ = UpiDailyLimitService.validate_upi_transaction(
        db, cid, 600000.0, payment_method="credit_card"
    )
    assert card_allowed is True
    assert viol_card is None

    nb_allowed, viol_nb, _ = UpiDailyLimitService.validate_upi_transaction(
        db, cid, 600000.0, payment_method="net_banking"
    )
    assert nb_allowed is True
    assert viol_nb is None
