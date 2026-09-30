import pytest
from unittest.mock import MagicMock
from backend.app.services.assistant_explainability_service import (
    explain_transaction_risk,
    explain_hold_status,
    RISK_CATEGORY_LOW,
    RISK_CATEGORY_MEDIUM,
    RISK_CATEGORY_HIGH
)

def test_fraud_probability_and_risk_score_separated():
    """
    Verification Gate 4 - Test 1:
    Fraud Probability (ML confidence %) and Risk Score (0-100 composite) must be separate fields,
    not conflated or merged into a single ambiguous number.
    """
    mock_tx = MagicMock()
    mock_tx.id = "TX_TEST_101"
    mock_tx.amount = 12500.0
    mock_tx.merchant = "Electronics MegaStore"
    mock_tx.created_at = "2026-09-30 14:00:00"
    mock_tx.status = "COMPLETED"
    mock_tx.risk_score = 65.0
    mock_tx.fraud_probability = 0.42
    mock_tx.security_flags = '["RAPID_TRANSACTION", "HIGH_AMOUNT"]'
    mock_tx.shap_values = '{"amount_deviation": 1.8, "velocity": 2.1}'

    result = explain_transaction_risk(mock_tx)

    assert "fraud_probability" in result
    assert "risk_score" in result
    assert "risk_level" in result
    
    # Verify values are distinct
    assert result["fraud_probability"] == 42.0  # percentage
    assert result["risk_score"] == 65.0
    assert result["risk_level"] == RISK_CATEGORY_MEDIUM
    assert result["fraud_probability"] != result["risk_score"]

def test_risk_category_thresholds():
    """
    Verification Gate 4 - Test 2:
    Strict adherence to risk categories:
    LOW: <= 30
    MEDIUM: 31-70
    HIGH: >= 71
    """
    mock_tx = MagicMock()
    mock_tx.id = "TX_TEST_102"
    mock_tx.amount = 500.0
    mock_tx.merchant = "Coffee Shop"
    mock_tx.created_at = "2026-09-30 14:00:00"
    mock_tx.status = "COMPLETED"
    mock_tx.security_flags = None
    mock_tx.shap_values = None

    # Test LOW
    mock_tx.risk_score = 30.0
    mock_tx.fraud_probability = 0.10
    low_res = explain_transaction_risk(mock_tx)
    assert low_res["risk_level"] == RISK_CATEGORY_LOW

    # Test MEDIUM lower bound
    mock_tx.risk_score = 31.0
    med_res1 = explain_transaction_risk(mock_tx)
    assert med_res1["risk_level"] == RISK_CATEGORY_MEDIUM

    # Test MEDIUM upper bound
    mock_tx.risk_score = 70.0
    med_res2 = explain_transaction_risk(mock_tx)
    assert med_res2["risk_level"] == RISK_CATEGORY_MEDIUM

    # Test HIGH
    mock_tx.risk_score = 71.0
    mock_tx.fraud_probability = 0.85
    high_res = explain_transaction_risk(mock_tx)
    assert high_res["risk_level"] == RISK_CATEGORY_HIGH

def test_explanation_references_real_evidence_signals():
    """
    Verification Gate 4 - Test 3:
    Explanations must translate real ML/behavioral signals (SHAP / security flags)
    into human-readable evidence sentences without hallucinations.
    """
    mock_tx = MagicMock()
    mock_tx.id = "TX_TEST_103"
    mock_tx.amount = 45000.0
    mock_tx.merchant = "Luxury Jewelry"
    mock_tx.created_at = "2026-09-30 14:05:00"
    mock_tx.status = "FLAGGED"
    mock_tx.risk_score = 85.0
    mock_tx.fraud_probability = 0.88
    mock_tx.security_flags = '["RAPID_TRANSACTION_ACTIVITY", "UNUSUAL_DEVICE"]'
    mock_tx.shap_values = '{"amount_deviation": 3.5, "device_anomaly": 2.0}'

    result = explain_transaction_risk(mock_tx)
    
    assert len(result["signals"]) >= 2
    assert len(result["top_contributing_factors"]) >= 1
    assert "summary_explanation" in result
    
    # Check that explanation mentions signals or risk level
    summary = result["summary_explanation"].lower()
    assert "high" in summary or "signals" in summary

def test_hold_reasons_accurate_and_otp_never_leaked():
    """
    Verification Gate 4 - Test 4:
    Hold status must explain why the hold occurred and guide to security verification modal,
    while NEVER leaking the OTP code or secret bypass tokens.
    """
    mock_tx = MagicMock()
    mock_tx.id = "TX_HELD_104"
    mock_tx.amount = 5000.0
    mock_tx.merchant = "QuickTransfer"
    mock_tx.status = "HOLD"
    mock_tx.hold_reason = "Multiple rapid transactions detected within 60 minutes window"
    # Even if internal mock has an otp attribute, hold explanation must NOT expose it
    mock_tx.otp_code = "889912"
    mock_tx.security_trigger = "RAPID_TRANSACTION_ACTIVITY"

    hold_info = explain_hold_status(mock_tx)

    assert hold_info["is_on_hold"] is True
    assert "rapid transactions" in hold_info["hold_reason"].lower()
    assert "verification modal" in hold_info["resolution_guidance"].lower() or "mobile security" in hold_info["resolution_guidance"].lower()
    
    # Ensure OTP is NEVER exposed anywhere in hold explanation
    assert "889912" not in str(hold_info)
    assert "otp_code" not in hold_info
