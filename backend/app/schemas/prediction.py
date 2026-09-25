"""Pydantic schemas for Fraud Prediction and SHAP Explainable AI API."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict


class TransactionPredictionInput(BaseModel):
    """Input payload for scoring a financial transaction.

    Supports both the primary dataset schema (financial_fraud_customer_transactions.csv)
    and legacy fields with seamless bi-directional mapping.
    """
    model_config = ConfigDict(extra="allow")

    # Primary Identifiers
    transaction_id: Optional[str] = Field(None, description="Optional unique transaction reference identifier")
    customer_id: Optional[str] = Field(None, description="Customer account identifier")

    # Primary Actual CSV Features
    Amount: Optional[float] = Field(None, gt=0.0, description="Transaction monetary value")
    Transaction_Type: Optional[str] = Field(None, description="Transaction type (Transfer, Purchase, etc.)")
    Transaction_Hour: Optional[int] = Field(None, ge=0, le=23, description="Transaction authorization hour [0-23]")
    Location: Optional[str] = Field(None, description="Transaction city location")
    Usual_Location: Optional[str] = Field(None, description="Customer's usual residential/business location")
    Device_Type: Optional[str] = Field(None, description="Device channel (Mac, iPhone, Android, Windows)")
    New_Device: Optional[int] = Field(0, ge=0, le=1, description="Flag indicating unrecognized new device (0 or 1)")
    Account_Age_Days: Optional[float] = Field(None, ge=0.0, description="Account age in days")
    Previous_Transaction_Amount: Optional[float] = Field(None, ge=0.0, description="Preceding transaction amount")
    Average_Previous_Amount: Optional[float] = Field(None, ge=0.0, description="Historical average transaction amount")
    Amount_Deviation: Optional[float] = Field(None, description="Difference from historical average amount")
    Amount_Ratio: Optional[float] = Field(None, description="Ratio of amount to historical average")
    Transactions_Last_24H: Optional[float] = Field(None, ge=0.0, description="Transaction velocity in last 24 hours")
    Failed_Attempts: Optional[int] = Field(0, ge=0, description="Failed authentication attempts count")
    International_Transaction: Optional[int] = Field(0, ge=0, le=1, description="Cross-border payment indicator (0 or 1)")
    Unusual_Location: Optional[int] = Field(0, ge=0, le=1, description="Unusual location indicator (0 or 1)")

    # Frontend Analyzer & Master Profile Fields
    amount: Optional[float] = Field(None, gt=0.0, description="Transaction monetary value in INR")
    merchant_id: Optional[str] = Field(None, description="Target Merchant Master Profile ID")
    merchant_name: Optional[str] = Field(None, description="Target Merchant Name")
    merchant_category: Optional[str] = Field("general", description="Merchant industry category")
    merchant_average_ticket: Optional[float] = Field(None, description="Merchant average ticket amount")
    merchant_historical_fraud_rate: Optional[float] = Field(None, description="Merchant historical fraud rate")
    customer_historical_avg_amount: Optional[float] = Field(None, description="Customer historical average amount")
    is_new_device: Optional[bool] = Field(None, description="New device indicator")
    is_new_beneficiary: Optional[bool] = Field(None, description="New beneficiary indicator")
    is_location_changed: Optional[bool] = Field(None, description="Location jump indicator")
    location_distance_km: Optional[float] = Field(0.0, description="Geographic distance deviation in km")
    transactions_last_1h: Optional[float] = Field(None, description="Transactions in past 1 hour")
    transactions_last_24h: Optional[float] = Field(None, description="Transactions in past 24 hours")
    failed_transaction_attempts_24h: Optional[int] = Field(None, description="Failed attempts count in 24h")

    # Legacy Compatibility Fields
    transaction_amount: Optional[float] = Field(None, gt=0.0, description="Legacy alias for Amount")
    transaction_hour: Optional[int] = Field(None, ge=0, le=23, description="Legacy alias for Transaction_Hour")
    transaction_type: Optional[str] = Field(None, description="Legacy alias for Transaction_Type")
    device_type: Optional[str] = Field(None, description="Legacy alias for Device_Type")
    geo_location_region: Optional[str] = Field(None, description="Legacy alias for Location")
    account_age_days: Optional[float] = Field(None, ge=0.0, description="Legacy alias for Account_Age_Days")
    avg_transaction_amount_30d_customer: Optional[float] = Field(None, ge=0.0, description="Legacy alias for Average_Previous_Amount")
    transaction_velocity_24h: Optional[float] = Field(None, ge=0.0, description="Legacy alias for Transactions_Last_24H")
    transaction_velocity_1h: Optional[float] = Field(None, ge=0.0, description="Transactions in preceding 1 hour")
    is_international: Optional[int] = Field(None, ge=0, le=1, description="Legacy alias for International_Transaction")
    transaction_day_of_week: Optional[int] = Field(None, ge=0, le=7, description="Day of week [0-7]")
    previous_chargebacks: Optional[int] = Field(0, ge=0, description="Historical chargeback count")
    transaction_country: Optional[str] = Field("IN", description="Country code")
    is_high_risk_merchant_category: Optional[int] = Field(0, ge=0, le=1, description="High-risk category indicator")
    is_weekend: Optional[int] = Field(0, ge=0, le=1, description="Weekend indicator")
    customer_total_transactions_30d: Optional[float] = Field(10.0, ge=0.0, description="Total 30-day transaction volume")

    @model_validator(mode="before")
    @classmethod
    def reconcile_fields(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data

        d = dict(data)

        # Reconcile & Validate Amount / transaction_amount / amount
        amt = d.get("Amount") if d.get("Amount") is not None else (d.get("transaction_amount") if d.get("transaction_amount") is not None else d.get("amount"))
        if amt is None:
            raise ValueError("Field 'transaction_amount' or 'Amount' is required.")
        try:
            amt_val = float(amt)
            if amt_val <= 0.0:
                raise ValueError("Transaction amount must be strictly positive (> 0.0).")
        except (TypeError, ValueError) as e:
            raise ValueError(f"Invalid transaction amount: {e}")
        d["Amount"] = amt_val
        d["transaction_amount"] = amt_val

        # Reconcile & Validate Transaction_Hour / transaction_hour
        hour = d.get("Transaction_Hour", d.get("transaction_hour"))
        if hour is None:
            raise ValueError("Field 'transaction_hour' or 'Transaction_Hour' is required.")
        try:
            hour_val = int(hour)
            if not (0 <= hour_val <= 23):
                raise ValueError("Transaction hour must be between 0 and 23.")
        except (TypeError, ValueError) as e:
            raise ValueError(f"Invalid transaction hour: {e}")
        d["Transaction_Hour"] = hour_val
        d["transaction_hour"] = hour_val

        # Reconcile Transaction_Type / transaction_type
        tx_type = d.get("Transaction_Type", d.get("transaction_type", "Purchase"))
        d["Transaction_Type"] = str(tx_type)
        d["transaction_type"] = str(tx_type)

        # Reconcile Location / geo_location_region / Usual_Location
        loc = d.get("Location", d.get("geo_location_region", "Pune"))
        d["Location"] = str(loc)
        d["geo_location_region"] = str(loc)
        if "Usual_Location" not in d or d["Usual_Location"] is None:
            d["Usual_Location"] = str(loc)

        # Reconcile Device_Type / device_type
        dev = d.get("Device_Type", d.get("device_type", "Mac"))
        d["Device_Type"] = str(dev)
        d["device_type"] = str(dev)

        # Reconcile Account_Age_Days / account_age_days
        acc_age = d.get("Account_Age_Days", d.get("account_age_days", 365.0))
        d["Account_Age_Days"] = float(acc_age)
        d["account_age_days"] = float(acc_age)

        # Reconcile Average_Previous_Amount / customer_historical_avg_amount
        # Crucial: NEVER default baseline to current amt!
        baseline = d.get("customer_historical_avg_amount")
        if baseline is None:
            baseline = d.get("Average_Previous_Amount")
        if baseline is None:
            baseline = d.get("avg_transaction_amount_30d_customer")
        if baseline is None:
            baseline = d.get("merchant_average_ticket")
        if baseline is None:
            baseline = 2000.0
        try:
            baseline_amt = float(baseline)
            if baseline_amt <= 0:
                baseline_amt = 2000.0
        except Exception:
            baseline_amt = 2000.0

        d["Average_Previous_Amount"] = baseline_amt
        d["avg_transaction_amount_30d_customer"] = baseline_amt
        d["customer_historical_avg_amount"] = baseline_amt

        if "Previous_Transaction_Amount" not in d or d["Previous_Transaction_Amount"] is None:
            d["Previous_Transaction_Amount"] = baseline_amt

        # Reconcile Amount_Deviation & Amount_Ratio
        d["Amount_Deviation"] = amt_val - baseline_amt
        d["Amount_Ratio"] = amt_val / (baseline_amt + 1e-5)

        # Reconcile New_Device & is_new_device
        new_dev = 1 if (d.get("is_new_device") is True or d.get("New_Device") == 1 or d.get("is_new_device") == 1) else 0
        d["New_Device"] = new_dev
        d["is_new_device"] = bool(new_dev)

        # Reconcile is_new_beneficiary
        new_bene = 1 if (d.get("is_new_beneficiary") is True or d.get("is_new_beneficiary") == 1) else 0
        d["is_new_beneficiary"] = bool(new_bene)

        # Reconcile Unusual_Location & is_location_changed
        unusual_loc = 1 if (
            d.get("is_location_changed") is True
            or d.get("Unusual_Location") == 1
            or d.get("is_location_changed") == 1
            or float(d.get("location_distance_km", 0) or 0) > 50
        ) else 0
        d["Unusual_Location"] = unusual_loc
        d["is_location_changed"] = bool(unusual_loc)

        # Reconcile Velocity
        vel_1 = float(d.get("transactions_last_1h") if d.get("transactions_last_1h") is not None else d.get("transaction_velocity_1h", 1.0))
        d["transactions_last_1h"] = vel_1
        d["transaction_velocity_1h"] = vel_1

        vel_24 = float(d.get("transactions_last_24h") if d.get("transactions_last_24h") is not None else d.get("Transactions_Last_24H", d.get("transaction_velocity_24h", max(vel_1, 2.0))))
        d["transactions_last_24h"] = vel_24
        d["Transactions_Last_24H"] = vel_24
        d["transaction_velocity_24h"] = vel_24

        # Reconcile Failed Attempts
        fails = int(d.get("failed_transaction_attempts_24h") if d.get("failed_transaction_attempts_24h") is not None else d.get("Failed_Attempts", 0))
        d["failed_transaction_attempts_24h"] = fails
        d["Failed_Attempts"] = fails

        # Reconcile International_Transaction / is_international
        intl = d.get("International_Transaction", d.get("is_international", 0))
        d["International_Transaction"] = int(intl)
        d["is_international"] = int(intl)

        # Ensure transaction_day_of_week
        if "transaction_day_of_week" not in d or d["transaction_day_of_week"] is None:
            d["transaction_day_of_week"] = 1

        return d


class PredictionResponse(BaseModel):
    """Holistic fraud prediction response combining ML model inference and multi-factor risk scoring."""

    prediction: str = Field(..., description="Classification result: 'FRAUD' or 'GENUINE'")
    fraud_probability: float = Field(..., ge=0.0, le=1.0, description="ML fraud probability [0.0 - 1.0]")
    risk_score: int = Field(..., ge=0, le=100, description="Holistic risk score [0 - 100]")
    risk_level: str = Field(..., description="Risk level classification: 'LOW', 'MEDIUM', 'HIGH'")
    model_name: str = Field(..., description="Name of the active ML model used for inference")
    model_version: str = Field(..., description="Version of the active ML model")
    threshold_used: float = Field(..., ge=0.0, le=1.0, description="Decision threshold applied")
    transaction_id: Optional[str] = Field(None, description="Echoed transaction identifier")
    risk_factors: List[Dict[str, Any]] = Field(default_factory=list, description="Contributing risk signals breakdown")
    top_shap_factors: Optional[List[Dict[str, Any]]] = Field(None, description="Summary of top SHAP attributions")
    top_factors: Optional[List[Dict[str, Any]]] = Field(None, description="Unified top contributing risk and SHAP factors")
    recommended_action: Optional[str] = Field(None, description="Recommended operational action: BLOCK, REVIEW, or ALLOW")
    anomaly_score: Optional[float] = Field(None, description="Unsupervised Isolation Forest anomaly score")
    anomaly_status: Optional[str] = Field(None, description="Anomaly service status: 'AVAILABLE' | 'UNAVAILABLE'")
    uncertainty_score: Optional[float] = Field(None, description="Model prediction uncertainty score [0.0 - 1.0]")
    uncertainty_level: Optional[str] = Field(None, description="Uncertainty level: 'LOW' | 'MODERATE' | 'HIGH'")
    counterfactual: Optional[Dict[str, Any]] = Field(None, description="Verified counterfactual perturbation scenario")
    composed_explanation: Optional[Dict[str, Any]] = Field(None, description="Evidence-grounded investigator narrative")


class LocalExplanationResponse(BaseModel):
    """Detailed local SHAP attribution response for a transaction."""

    transaction_id: Optional[str] = None
    prediction: str
    fraud_probability: float
    risk_score: int
    risk_level: str
    base_value: float
    top_risk_increasing_factors: List[Dict[str, Any]]
    top_risk_decreasing_factors: List[Dict[str, Any]]
    all_attributions: List[Dict[str, Any]]

    # Enhanced Multi-Model AI and Explainability Intelligence
    model_name: Optional[str] = "xgboost"
    model_version: Optional[str] = "v1.1.0"
    model_comparison: Optional[Dict[str, Any]] = None
    composed_explanation: Optional[Dict[str, Any]] = None
    counterfactual: Optional[Dict[str, Any]] = None
    anomaly_score: Optional[float] = None
    anomaly_status: Optional[str] = None
    uncertainty_score: Optional[float] = None
    uncertainty_level: Optional[str] = None


class GlobalExplanationResponse(BaseModel):
    """Global feature importance ranking response across the model population."""

    model_name: str
    model_version: str
    sample_size: int
    feature_importance_ranking: List[Dict[str, Any]]
