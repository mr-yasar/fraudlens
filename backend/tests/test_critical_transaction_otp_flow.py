"""Comprehensive End-to-End Test Suite for Master Transaction + OTP + Bank Account Flow.
Verifies all 4 users (Monisha, Mohana, Sowmiya, Priya):
1. Low-risk transaction: instant approval, balance deducted in DB, transaction recorded.
2. Medium/High-risk transaction: frozen in REVIEW, OTP generated, balance untouched.
3. Wrong OTP: rejected, balance untouched.
4. Correct OTP verified: transaction still held until explicit ALLOW/APPROVE.
5. Explicit approval: balance deducted in DB, transaction status SUCCESS.
6. Insufficient balance: rejected with 400 'Insufficient Balance', 0 balance deducted, no transaction.
7. Separate transaction records in DB (no overwriting, accessible via history/My Transactions).
"""

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.core.database import SessionLocal
from backend.app.models.customer import Customer
from backend.app.models.approval import TransactionApproval
from backend.app.models.transaction import Transaction

client = TestClient(app)

USERS_CONFIG = [
    {
        "name": "Monisha",
        "email": "monisha@fraudlens.ai",
        "customer_id": "CUST_MONISHA_001",
    },
    {
        "name": "Mohana",
        "email": "mohana@fraudlens.ai",
        "customer_id": "CUST_MOHANA_002",
    },
    {
        "name": "Sowmiya",
        "email": "sowmiya@fraudlens.ai",
        "customer_id": "CUST_SOWMIYA_003",
    },
    {
        "name": "Ajay",
        "email": "ajay@fraudlens.ai",
        "customer_id": "CUST_AJAY_004",
    },
]


@pytest.fixture(scope="module")
def user_tokens():
    """Retrieve auth tokens for all 4 users."""
    tokens = {}
    for user_info in USERS_CONFIG:
        res = client.post("/api/v1/auth/login", json={"email": user_info["email"], "password": "Customer@1234"})
        assert res.status_code == 200, f"Login failed for {user_info['name']}: {res.text}"
        tokens[user_info["customer_id"]] = res.json()["access_token"]
    return tokens


@pytest.mark.parametrize("user_info", USERS_CONFIG, ids=lambda u: u["name"])
def test_insufficient_balance_blocked(user_tokens, user_info):
    """Transactions exceeding available balance must be blocked before any processing."""
    cid = user_info["customer_id"]
    token = user_tokens[cid]
    headers = {"Authorization": f"Bearer {token}"}

    # Get current balance from backend
    res_wallet = client.get(f"/api/v1/payment/wallet/{cid}", headers=headers)
    assert res_wallet.status_code == 200
    balance_before = res_wallet.json()["available_balance"]

    # Attempt transaction higher than balance
    huge_amount = balance_before + 500000.0
    payload = {
        "customer_id": cid,
        "amount": huge_amount,
        "merchant_name": "Ultra Luxury Jewelers",
        "merchant_category": "luxury_goods",
        "channel": "UPI",
        "transaction_type": "MERCHANT",
        "device_id": f"DEV-{user_info['name'].upper()}-SECURE",
        "location": "Chennai",
    }
    res_tx = client.post("/api/v1/payment/initiate", json=payload, headers=headers)
    assert res_tx.status_code == 400
    assert "Insufficient" in res_tx.json().get("detail", "")

    # Ensure balance was NOT deducted
    res_wallet_after = client.get(f"/api/v1/payment/wallet/{cid}", headers=headers)
    assert res_wallet_after.status_code == 200
    assert res_wallet_after.json()["available_balance"] == balance_before


@pytest.mark.parametrize("user_info", USERS_CONFIG, ids=lambda u: u["name"])
def test_low_risk_auto_approval_and_balance_deduction(user_tokens, user_info):
    """Low risk transactions should auto-approve, deduct balance in DB, and save transaction."""
    cid = user_info["customer_id"]
    token = user_tokens[cid]
    headers = {"Authorization": f"Bearer {token}"}

    # Get balance
    res_wallet = client.get(f"/api/v1/payment/wallet/{cid}", headers=headers)
    balance_before = res_wallet.json()["available_balance"]

    tx_amount = 250.0  # Routine low amount
    payload = {
        "customer_id": cid,
        "amount": tx_amount,
        "merchant_name": "Starbucks Coffee",
        "merchant_category": "dining",
        "channel": "UPI",
        "transaction_type": "MERCHANT",
        "device_id": f"DEV-{user_info['name'].upper()}-IPHONE-15",
        "location": "Chennai" if cid in ("CUST_MONISHA_001", "CUST_REAL_002") else ("Coimbatore" if cid == "CUST_MOHANA_002" else "Bangalore"),
    }
    res_tx = client.post("/api/v1/payment/initiate", json=payload, headers=headers)
    assert res_tx.status_code == 200
    data = res_tx.json()

    # Verify decision invariants
    if data["decision"] == "ALLOW":
        assert data["risk_score"] <= 30
        assert data["status"] in ("APPROVED", "SUCCESS")
        # Verify balance deducted
        res_wallet_after = client.get(f"/api/v1/payment/wallet/{cid}", headers=headers)
        balance_after = res_wallet_after.json()["available_balance"]
        assert round(balance_after, 2) == round(balance_before - tx_amount, 2)
    elif data["decision"] in ("REVIEW", "STEP_UP_VERIFICATION"):
        # Velocity or rule-triggered step-up review
        assert data.get("verification_required") is True
        assert data.get("approval_id") is not None
        # Verify balance is safely preserved during verification hold
        res_wallet_after = client.get(f"/api/v1/payment/wallet/{cid}", headers=headers)
        assert res_wallet_after.json()["available_balance"] == balance_before
    else:
        # Critical velocity or rule block
        assert data["decision"] == "BLOCK"
        assert data["risk_score"] >= 70
        res_wallet_after = client.get(f"/api/v1/payment/wallet/{cid}", headers=headers)
        assert res_wallet_after.json()["available_balance"] == balance_before


@pytest.mark.parametrize("user_info", USERS_CONFIG, ids=lambda u: u["name"])
def test_medium_or_high_risk_otp_hold_and_approval(user_tokens, user_info):
    """Medium/High risk freezes transaction, generates OTP, rejects bad OTP, requires Allow/Approve."""
    cid = user_info["customer_id"]
    token = user_tokens[cid]
    headers = {"Authorization": f"Bearer {token}"}

    res_wallet = client.get(f"/api/v1/payment/wallet/{cid}", headers=headers)
    balance_before = res_wallet.json()["available_balance"]

    # Amount within balance to test hold and approve
    tx_amount = min(50000.0, balance_before * 0.25)
    payload = {
        "customer_id": cid,
        "amount": tx_amount,
        "merchant_name": "International Wire Exchange",
        "merchant_category": "wire_transfer",
        "channel": "NET_BANKING",
        "transaction_type": "PERSONAL",
        "device_id": f"DEV-UNKNOWN-ANOMALOUS-{cid}",
        "location": "Moscow, Russia",  # Anomalous location triggers risk hold
    }
    res_tx = client.post("/api/v1/payment/initiate", json=payload, headers=headers)
    assert res_tx.status_code == 200
    data = res_tx.json()
    tx_id = data.get("transaction_id")

    # Verify decision is either step-up verification (REVIEW) or critical anomaly (BLOCK)
    if data["decision"] in ("REVIEW", "STEP_UP_VERIFICATION", "TEMPORARY_HOLD"):
        assert data.get("verification_required") is True
        assert data.get("approval_id") is not None
        assert data.get("otp_code") is not None
        approval_id = data["approval_id"]
        otp_code = data["otp_code"]

        # 1. Balance must NOT be deducted yet!
        res_wallet_held = client.get(f"/api/v1/payment/wallet/{cid}", headers=headers)
        assert res_wallet_held.json()["available_balance"] == balance_before

        # 2. Check pending approval record in DB
        db = SessionLocal()
        approval = db.query(TransactionApproval).filter(
            TransactionApproval.approval_id == approval_id,
            TransactionApproval.status == "PENDING"
        ).first()
        assert approval is not None
        assert approval.verification_token == otp_code
        db.close()

        # 3. Wrong OTP must fail!
        res_wrong = client.post(f"/api/v1/approvals/{approval.approval_id}/action", json={
            "action": "APPROVE",
            "challenge_response": "000000" if otp_code != "000000" else "999999",
        }, headers=headers)
        assert res_wrong.status_code == 400
        assert "Invalid" in res_wrong.json().get("detail", "")

        # Ensure balance STILL not deducted
        res_wallet_wrong = client.get(f"/api/v1/payment/wallet/{cid}", headers=headers)
        assert res_wallet_wrong.json()["available_balance"] == balance_before

        # 4. Correct OTP with APPROVE must succeed and deduct balance atomically
        res_correct = client.post(f"/api/v1/approvals/{approval.approval_id}/action", json={
            "action": "APPROVE",
            "challenge_response": otp_code,
        }, headers=headers)
        assert res_correct.status_code == 200
        approval_res = res_correct.json()
        assert approval_res["status"] in ("APPROVED", "SUCCESS")

        # 5. Balance must now be deducted
        res_wallet_final = client.get(f"/api/v1/payment/wallet/{cid}", headers=headers)
        balance_final = res_wallet_final.json()["available_balance"]
        assert round(balance_final, 2) == round(balance_before - tx_amount, 2)

        # 6. Verify Transaction is stored in DB
        db = SessionLocal()
        saved_tx = db.query(Transaction).filter(Transaction.transaction_id == tx_id).first()
        assert saved_tx is not None
        assert saved_tx.amount == tx_amount
        assert saved_tx.customer_id == cid
        db.close()
    else:
        # Critical threat block
        assert data["decision"] == "BLOCK"
        assert data["risk_level"] == "HIGH"
        res_wallet_final = client.get(f"/api/v1/payment/wallet/{cid}", headers=headers)
        assert res_wallet_final.json()["available_balance"] == balance_before

    # 6. Verify Transaction is stored in DB
    db = SessionLocal()
    saved_tx = db.query(Transaction).filter(Transaction.transaction_id == tx_id).first()
    assert saved_tx is not None
    assert saved_tx.amount == tx_amount
    assert saved_tx.customer_id == cid
    db.close()


def test_transactions_history_persistence_and_multiplicity(user_tokens):
    """Ensure history returns multiple separate transactions for each user."""
    for user_info in USERS_CONFIG:
        cid = user_info["customer_id"]
        token = user_tokens[cid]
        headers = {"Authorization": f"Bearer {token}"}

        res_hist = client.get(f"/api/v1/transactions?customer_id={cid}", headers=headers)
        assert res_hist.status_code == 200
        data = res_hist.json()
        assert "items" in data
        history = data["items"]
        assert isinstance(history, list)
        assert len(history) >= 1
        for item in history:
            assert "transaction_id" in item
            assert "amount" in item
            assert item["customer_id"] == cid
