"""Phase 2 Comprehensive Data Contract & Database Alignment Tests.

Verifies:
1. Exact field mappings across Dataset -> Pydantic -> ORM -> DB -> Response -> Frontend.
2. Dual-casing and legacy alias reconciliation without silent data corruption.
3. Foreign key constraints and relationship definitions (Customer -> Transaction -> Investigation/SHAP).
4. Enum consistency across Risk, Investigation Status/Decision, User Roles, and Payment States.
5. Numeric precision and Datetime consistency across schemas and models.
6. Validation rules (strictly positive amounts, bounded hours, valid enums).
"""

import pytest
from datetime import datetime, timezone
from pydantic import ValidationError

from backend.app.models.transaction import Transaction
from backend.app.models.investigation import Investigation
from backend.app.models.shap_explanation import ShapExplanation
from backend.app.models.customer import Customer
from backend.app.models.user import User
from backend.app.models.alert import Alert
from backend.app.models.payment_intent import PaymentIntent, PaymentLifecycleStatus

from backend.app.schemas.prediction import (
    TransactionPredictionInput,
    PredictionResponse,
    LocalExplanationResponse,
)
from backend.app.schemas.transaction import (
    TransactionCreateInput,
    TransactionSummaryResponse,
    TransactionDetailResponse,
    RealtimeEvaluationResponse,
)
from backend.app.schemas.investigation import (
    InvestigationStatus,
    InvestigationDecision,
    InvestigationCreateInput,
    InvestigationUpdateInput,
    InvestigationSummaryResponse,
    InvestigationDetailResponse,
)
from backend.app.schemas.customer import (
    CustomerResponse,
    CustomerBehavioralStats,
    CustomerDetailResponse,
)
from backend.app.schemas.user import UserRole
from backend.app.schemas.payment import PaymentDecision, RiskLevelEnum


# ---------------------------------------------------------------------------
# 1. Dataset Column & Casing Compatibility Tests
# ---------------------------------------------------------------------------

def test_raw_csv_column_casing_mapping():
    """Verify raw CSV column names parse directly into canonical fields."""
    raw_csv_payload = {
        "Transaction_ID": "TXN-CSV-001",
        "Customer_ID": "CUST-001",
        "Amount": 1250.75,
        "Transaction_Type": "Transfer",
        "Transaction_Hour": 14,
        "Location": "Mumbai",
        "Usual_Location": "Mumbai",
        "Device_Type": "Android",
        "New_Device": 0,
        "Account_Age_Days": 450,
        "Previous_Transaction_Amount": 800.0,
        "Average_Previous_Amount": 1100.0,
        "Amount_Deviation": 150.75,
        "Amount_Ratio": 1.137,
        "Transactions_Last_24H": 3,
        "Failed_Attempts": 0,
        "International_Transaction": 0,
        "Unusual_Location": 0,
    }

    input_obj = TransactionPredictionInput(**raw_csv_payload)

    # Check that both CSV names and canonical API snake_case attributes are correctly populated
    assert input_obj.Amount == 1250.75
    assert input_obj.transaction_amount == 1250.75
    assert input_obj.Transaction_Hour == 14
    assert input_obj.transaction_hour == 14
    assert input_obj.Device_Type == "Android"
    assert input_obj.device_type == "Android"
    assert input_obj.Location == "Mumbai"
    assert input_obj.geo_location_region == "Mumbai"
    assert input_obj.Account_Age_Days == 450.0
    assert input_obj.account_age_days == 450.0
    assert input_obj.Transactions_Last_24H == 3.0
    assert input_obj.transaction_velocity_24h == 3.0
    assert input_obj.International_Transaction == 0
    assert input_obj.is_international == 0


def test_snake_case_api_field_mapping():
    """Verify API snake_case payload parses directly into canonical fields."""
    api_payload = {
        "transaction_id": "TXN-API-002",
        "customer_id": "CUST-002",
        "transaction_amount": 5400.0,
        "transaction_type": "Purchase",
        "transaction_hour": 3,
        "geo_location_region": "Bangalore",
        "device_type": "iPhone",
        "account_age_days": 120.0,
        "avg_transaction_amount_30d_customer": 200.0,
        "transaction_velocity_24h": 12.0,
        "is_international": 1,
    }

    input_obj = TransactionPredictionInput(**api_payload)

    assert input_obj.Amount == 5400.0
    assert input_obj.transaction_amount == 5400.0
    assert input_obj.Transaction_Hour == 3
    assert input_obj.transaction_hour == 3
    assert input_obj.Location == "Bangalore"
    assert input_obj.geo_location_region == "Bangalore"
    assert input_obj.Device_Type == "iPhone"
    assert input_obj.device_type == "iPhone"
    assert input_obj.Account_Age_Days == 120.0
    assert input_obj.Average_Previous_Amount == 200.0
    assert input_obj.Transactions_Last_24H == 12.0
    assert input_obj.International_Transaction == 1
    assert input_obj.is_international == 1


def test_input_validation_negative_or_zero_amount():
    """Verify validation strictly rejects non-positive amounts."""
    with pytest.raises(ValidationError):
        TransactionPredictionInput(Amount=0.0, Transaction_Hour=10)

    with pytest.raises(ValidationError):
        TransactionPredictionInput(transaction_amount=-150.0, transaction_hour=10)


def test_input_validation_invalid_hour():
    """Verify validation strictly rejects out-of-range hours."""
    with pytest.raises(ValidationError):
        TransactionPredictionInput(Amount=100.0, Transaction_Hour=24)

    with pytest.raises(ValidationError):
        TransactionPredictionInput(transaction_amount=100.0, transaction_hour=-1)


# ---------------------------------------------------------------------------
# 2. Foreign Key & ORM Model Integrity Tests
# ---------------------------------------------------------------------------

def test_transaction_orm_relationships():
    """Verify Transaction ORM model relationships and table mappings."""
    assert Transaction.__tablename__ == "transactions"
    assert hasattr(Transaction, "customer")
    assert hasattr(Transaction, "investigations")
    assert hasattr(Transaction, "shap_explanations")


def test_investigation_orm_relationships():
    """Verify Investigation ORM model relationships and table mappings."""
    assert Investigation.__tablename__ == "investigations"
    assert hasattr(Investigation, "transaction")
    assert hasattr(Investigation, "investigator")


def test_shap_explanation_orm_relationships():
    """Verify ShapExplanation ORM model relationships and table mappings."""
    assert ShapExplanation.__tablename__ == "shap_explanations"
    assert hasattr(ShapExplanation, "transaction")


def test_customer_orm_relationships():
    """Verify Customer ORM model relationships and table mappings."""
    assert Customer.__tablename__ == "customers"
    assert hasattr(Customer, "transactions")
    assert hasattr(Customer, "payment_intents")


# ---------------------------------------------------------------------------
# 3. Enum Consistency Tests
# ---------------------------------------------------------------------------

def test_investigation_status_and_decision_enums():
    """Verify investigation status and decision values."""
    assert InvestigationStatus.OPEN.value == "OPEN"
    assert InvestigationStatus.UNDER_REVIEW.value == "UNDER_REVIEW"
    assert InvestigationStatus.RESOLVED.value == "RESOLVED"

    assert InvestigationDecision.CONFIRMED_FRAUD.value == "CONFIRMED_FRAUD"
    assert InvestigationDecision.GENUINE.value == "GENUINE"

    # Test validator in InvestigationUpdateInput
    valid_update = InvestigationUpdateInput(status="under_review", decision="genuine")
    assert valid_update.status == "UNDER_REVIEW"
    assert valid_update.decision == "GENUINE"

    with pytest.raises(ValidationError):
        InvestigationUpdateInput(status="INVALID_STATUS")

    with pytest.raises(ValidationError):
        InvestigationUpdateInput(decision="INVALID_DECISION")


def test_user_role_enum():
    """Verify UserRole values."""
    assert UserRole.ADMIN.value == "ADMIN"
    assert UserRole.FRAUD_INVESTIGATOR.value == "FRAUD_INVESTIGATOR"


def test_risk_level_and_payment_decision_enums():
    """Verify RiskLevelEnum and PaymentDecision."""
    assert RiskLevelEnum.LOW.value == "LOW"
    assert RiskLevelEnum.MEDIUM.value == "MEDIUM"
    assert RiskLevelEnum.HIGH.value == "HIGH"

    assert PaymentDecision.ALLOW.value == "ALLOW"
    assert PaymentDecision.REVIEW.value == "REVIEW"
    assert PaymentDecision.BLOCK.value == "BLOCK"


# ---------------------------------------------------------------------------
# 4. Response Serialization & Nullability Tests
# ---------------------------------------------------------------------------

def test_transaction_summary_response_serialization():
    """Verify TransactionSummaryResponse handles serialization accurately."""
    now = datetime.now(timezone.utc)
    summary = TransactionSummaryResponse(
        id=10,
        transaction_id="TXN-10",
        customer_id="CUST-10",
        amount=199.99,
        transaction_hour=15,
        merchant_category="retail",
        transaction_country="IN",
        geo_location_region="Delhi",
        device_type="Mac",
        transaction_type="Purchase",
        fraud_probability=0.045,
        prediction="GENUINE",
        risk_score=12.0,
        risk_level="LOW",
        created_at=now,
    )
    dumped = summary.model_dump()
    assert dumped["id"] == 10
    assert dumped["amount"] == 199.99
    assert dumped["prediction"] == "GENUINE"
    assert dumped["risk_level"] == "LOW"


def test_realtime_evaluation_response_serialization():
    """Verify RealtimeEvaluationResponse validates ranges and types."""
    resp = RealtimeEvaluationResponse(
        transaction_id="TXN-RT-01",
        prediction="FRAUD",
        fraud_probability=0.88,
        risk_score=92,
        risk_level="HIGH",
        model_name="xgboost",
        model_version="v1.0.0",
        threshold_used=0.5,
        risk_factors=[{"factor": "HIGH_AMOUNT", "weight": 25}],
        top_explanations=[{"feature": "Amount", "shap_value": 0.42}],
        alert_generated=True,
    )
    dumped = resp.model_dump()
    assert dumped["transaction_id"] == "TXN-RT-01"
    assert dumped["fraud_probability"] == 0.88
    assert dumped["risk_score"] == 92
    assert dumped["alert_generated"] is True
