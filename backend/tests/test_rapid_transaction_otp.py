"""Tests for Rapid Transaction OTP Security Flow and Multi-User Isolation."""

import pytest
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from backend.app.core.database import SessionLocal
from backend.app.models.transaction import Transaction
from backend.app.models.approval import TransactionApproval, ApprovalStatus
from backend.app.schemas.payment import (
    PaymentInitiateRequest,
    PaymentDecision,
    RiskLevelEnum,
)
from backend.app.services.risk_decision_orchestrator import RiskDecisionOrchestrator


def test_rapid_transaction_detection_triggers_otp_with_low_base_score():
    """Verify that 3 rapid low-value transactions trigger rapid activity and OTP without inflating base fraud score."""
    db: Session = SessionLocal()
    test_cust = "CUST_TEST_RAPID_001"
    try:
        # Clean up any test records for this customer
        db.query(TransactionApproval).filter(TransactionApproval.customer_id == test_cust).delete()
        db.query(Transaction).filter(Transaction.customer_id == test_cust).delete()
        db.commit()

        # Transaction 1: Low value (₹500) -> Should be ALLOW
        req1 = PaymentInitiateRequest(
            customer_id=test_cust,
            amount=500.0,
            currency="INR",
            merchant_name="Local Groceries",
            merchant_category="retail",
            payment_method="upi",
            device_type="web",
            location="Salem",
            transaction_country="IN",
            transaction_type="online_payment",
        )
        res1 = RiskDecisionOrchestrator.evaluate_and_process_payment(db=db, request=req1)
        assert res1.decision == PaymentDecision.ALLOW
        assert res1.verification_required is False
        assert res1.risk_level == RiskLevelEnum.LOW
        assert res1.rapid_activity_detected is False

        # Transaction 2: Low value (₹300) -> Should still be ALLOW (2nd tx)
        req2 = PaymentInitiateRequest(
            customer_id=test_cust,
            amount=300.0,
            currency="INR",
            merchant_name="Tea Corner",
            merchant_category="retail",
            payment_method="upi",
            device_type="web",
            location="Salem",
            transaction_country="IN",
            transaction_type="online_payment",
        )
        res2 = RiskDecisionOrchestrator.evaluate_and_process_payment(db=db, request=req2)
        assert res2.decision == PaymentDecision.ALLOW
        assert res2.verification_required is False
        assert res2.risk_level == RiskLevelEnum.LOW
        assert res2.rapid_activity_detected is False

        # Transaction 3: Low value (₹500) within 60 mins -> 3rd tx triggers RAPID ACTIVITY!
        req3 = PaymentInitiateRequest(
            customer_id=test_cust,
            amount=500.0,
            currency="INR",
            merchant_name="Stationery Mart",
            merchant_category="retail",
            payment_method="upi",
            device_type="web",
            location="Salem",
            transaction_country="IN",
            transaction_type="online_payment",
        )
        res3 = RiskDecisionOrchestrator.evaluate_and_process_payment(db=db, request=req3)
        assert res3.decision == PaymentDecision.REVIEW
        assert res3.verification_required is True
        # Critical Requirement 4: Core base risk score must remain LOW (not falsely elevated)
        assert res3.risk_level == RiskLevelEnum.LOW
        assert res3.rapid_activity_detected is True
        assert res3.rapid_activity_count >= 3
        assert res3.security_trigger == "RAPID_TRANSACTION_ACTIVITY"
        assert "Multiple transactions were detected" in (res3.why_otp_reason or "")
        assert res3.otp_code is not None
        assert res3.approval_id is not None

        # Verify transaction state in database is PENDING_VERIFICATION (not prematurely SUCCESS)
        tx_rec = db.query(Transaction).filter(Transaction.transaction_id == res3.transaction_id).first()
        assert tx_rec is not None
        assert tx_rec.status == "PENDING_VERIFICATION"

        # Verify OTP verification completes transaction
        appr_res = RiskDecisionOrchestrator.process_approval_action(
            db=db,
            approval_id=res3.approval_id,
            action="APPROVE",
            challenge_response=res3.otp_code,
        )
        assert appr_res["status"] == "APPROVED"
        assert appr_res["lifecycle_status"] == "SUCCEEDED"

        # After approval, transaction is now marked SUCCESS
        db.refresh(tx_rec)
        assert tx_rec.status == "SUCCESS"

    finally:
        # Cleanup
        db.query(TransactionApproval).filter(TransactionApproval.customer_id == test_cust).delete()
        db.query(Transaction).filter(Transaction.customer_id == test_cust).delete()
        db.commit()
        db.close()


def test_multi_user_isolation_for_rapid_transactions():
    """Verify Monisha and Ajay have completely isolated rapid activity counters."""
    db: Session = SessionLocal()
    monisha_id = "CUST_MONISHA_TEST"
    ajay_id = "CUST_AJAY_TEST"

    try:
        # Clean test records
        for cid in [monisha_id, ajay_id]:
            db.query(TransactionApproval).filter(TransactionApproval.customer_id == cid).delete()
            db.query(Transaction).filter(Transaction.customer_id == cid).delete()
        db.commit()

        # Monisha makes 2 transactions
        for amt in [500.0, 300.0]:
            req = PaymentInitiateRequest(
                customer_id=monisha_id,
                amount=amt,
                currency="INR",
                merchant_name="Store M",
                merchant_category="retail",
                payment_method="upi",
                device_type="web",
                location="Salem",
                transaction_country="IN",
                transaction_type="online_payment",
            )
            RiskDecisionOrchestrator.evaluate_and_process_payment(db=db, request=req)

        # Monisha makes 3rd transaction -> Should trigger rapid activity
        req_m3 = PaymentInitiateRequest(
            customer_id=monisha_id,
            amount=500.0,
            currency="INR",
            merchant_name="Store M",
            merchant_category="retail",
            payment_method="upi",
            device_type="web",
            location="Salem",
            transaction_country="IN",
            transaction_type="online_payment",
        )
        res_m3 = RiskDecisionOrchestrator.evaluate_and_process_payment(db=db, request=req_m3)
        assert res_m3.rapid_activity_detected is True
        assert res_m3.decision == PaymentDecision.REVIEW

        # Ajay makes his 1st transaction -> Must NOT inherit Monisha's activity
        req_a1 = PaymentInitiateRequest(
            customer_id=ajay_id,
            amount=500.0,
            currency="INR",
            merchant_name="Store A",
            merchant_category="retail",
            payment_method="upi",
            device_type="web",
            location="Salem",
            transaction_country="IN",
            transaction_type="online_payment",
        )
        res_a1 = RiskDecisionOrchestrator.evaluate_and_process_payment(db=db, request=req_a1)
        assert res_a1.rapid_activity_detected is False
        assert res_a1.decision == PaymentDecision.ALLOW

    finally:
        for cid in [monisha_id, ajay_id]:
            db.query(TransactionApproval).filter(TransactionApproval.customer_id == cid).delete()
            db.query(Transaction).filter(Transaction.customer_id == cid).delete()
        db.commit()
        db.close()


def test_invalid_otp_fails_and_does_not_complete_transaction():
    """Verify that an incorrect OTP fails verification and leaves transaction in pending verification."""
    db: Session = SessionLocal()
    test_cust = "CUST_TEST_FAIL_001"
    try:
        db.query(TransactionApproval).filter(TransactionApproval.customer_id == test_cust).delete()
        db.query(Transaction).filter(Transaction.customer_id == test_cust).delete()
        db.commit()

        # Seed 2 transactions
        for amt in [200.0, 200.0]:
            req = PaymentInitiateRequest(
                customer_id=test_cust,
                amount=amt,
                currency="INR",
                merchant_name="Shop",
                merchant_category="retail",
                payment_method="upi",
                device_type="web",
                location="Salem",
                transaction_country="IN",
                transaction_type="online_payment",
            )
            RiskDecisionOrchestrator.evaluate_and_process_payment(db=db, request=req)

        # 3rd transaction triggers OTP
        req3 = PaymentInitiateRequest(
            customer_id=test_cust,
            amount=200.0,
            currency="INR",
            merchant_name="Shop",
            merchant_category="retail",
            payment_method="upi",
            device_type="web",
            location="Salem",
            transaction_country="IN",
            transaction_type="online_payment",
        )
        res3 = RiskDecisionOrchestrator.evaluate_and_process_payment(db=db, request=req3)
        assert res3.decision == PaymentDecision.REVIEW

        # Attempt verification with WRONG OTP "000000"
        with pytest.raises(Exception) as excinfo:
            RiskDecisionOrchestrator.process_approval_action(
                db=db,
                approval_id=res3.approval_id,
                action="APPROVE",
                challenge_response="000000",
            )
        assert "Invalid OTP code" in str(excinfo.value.detail)

        # Transaction MUST still be PENDING_VERIFICATION
        tx = db.query(Transaction).filter(Transaction.transaction_id == res3.transaction_id).first()
        assert tx.status == "PENDING_VERIFICATION"

    finally:
        db.query(TransactionApproval).filter(TransactionApproval.customer_id == test_cust).delete()
        db.query(Transaction).filter(Transaction.customer_id == test_cust).delete()
        db.commit()
        db.close()


def test_all_four_users_evaluated_independently():
    """Verify that all 4 named users (Monisha, Mogana, Sowmiya, Ajay) have independent rapid transaction states."""
    db: Session = SessionLocal()
    users = ["CUST_MONISHA_001", "CUST_MOHANA_002", "CUST_SOWMIYA_003", "CUST_AJAY_004"]
    try:
        # Check that querying each user returns customer-isolated results
        for u in users:
            req = PaymentInitiateRequest(
                customer_id=u,
                amount=500.0,
                currency="INR",
                merchant_name="Safe Grocery",
                merchant_category="retail",
                payment_method="upi",
                device_type="web",
                location="Salem",
                transaction_country="IN",
                transaction_type="online_payment",
            )
            res = RiskDecisionOrchestrator.evaluate_and_process_payment(db=db, request=req)
            assert res.customer_id == u
            if res.verification_required:
                assert res.otp_code is not None
                assert res.approval_id is not None
                assert res.why_otp_reason is not None
    finally:
        db.close()

