"""Feature Metadata, Human-Readable Translations, and Customer/Investigator Narrative Mappings."""

from typing import Any, Dict, Optional


FEATURE_METADATA: Dict[str, Dict[str, Any]] = {
    "Amount": {
        "display_name": "Transaction Amount",
        "category": "amount",
        "customer_reason_high": "Transaction amount is unusually large.",
        "customer_reason_low": "Transaction amount is within normal spending limits.",
        "investigator_template": "Transaction monetary value of ${val:.2f}.",
    },
    "Average_Previous_Amount": {
        "display_name": "Historical Average Amount",
        "category": "amount",
        "customer_reason_high": "Differs from your typical average spending.",
        "customer_reason_low": "Consistent with your typical average spending baseline.",
        "investigator_template": "Customer 30-day baseline average is ${val:.2f}.",
    },
    "Amount_to_Average_Ratio": {
        "display_name": "Amount Baseline Multiplier",
        "category": "amount",
        "customer_reason_high": "Amount is significantly higher than your typical transactions.",
        "customer_reason_low": "Amount ratio matches historical spending habits.",
        "investigator_template": "Transaction is {val:.1f}x the customer's historical average amount.",
    },
    "Amount_Ratio": {
        "display_name": "Amount Baseline Multiplier",
        "category": "amount",
        "customer_reason_high": "Amount is significantly higher than your typical transactions.",
        "customer_reason_low": "Amount ratio matches historical spending habits.",
        "investigator_template": "Transaction is {val:.1f}x the customer's historical average amount.",
    },
    "Amount_Deviation": {
        "display_name": "Amount Deviation Strength",
        "category": "amount",
        "customer_reason_high": "Spending amount diverges from normal baseline.",
        "customer_reason_low": "Amount is consistent with your recent transactions.",
        "investigator_template": "Amount deviates by ${val:.2f} from historical mean.",
    },
    "Transaction_Hour": {
        "display_name": "Transaction Hour",
        "category": "time",
        "customer_reason_high": "Transaction initiated during unusual night hours.",
        "customer_reason_low": "Standard operating daytime transaction.",
        "investigator_template": "Transaction initiated at {val:02d}:00 hours local/UTC.",
    },
    "Account_Age_Days": {
        "display_name": "Account Tenure",
        "category": "customer",
        "customer_reason_high": "New account with limited historical activity.",
        "customer_reason_low": "Established account with long-standing positive history.",
        "investigator_template": "Customer account age is {val:.0f} days.",
    },
    "Velocity_1h": {
        "display_name": "1-Hour Transaction Velocity",
        "category": "velocity",
        "customer_reason_high": "Rapid frequency of transactions within the past hour.",
        "customer_reason_low": "Normal transaction frequency.",
        "investigator_template": "Detected {val:.0f} transactions in the trailing 1-hour window.",
    },
    "Velocity_24h": {
        "display_name": "24-Hour Transaction Velocity",
        "category": "velocity",
        "customer_reason_high": "Elevated number of transactions over the past 24 hours.",
        "customer_reason_low": "Routine daily transaction volume.",
        "investigator_template": "Observed {val:.0f} transactions in the trailing 24-hour window.",
    },
    "Transactions_Last_24H": {
        "display_name": "24-Hour Transaction Velocity",
        "category": "velocity",
        "customer_reason_high": "Elevated number of transactions over the past 24 hours.",
        "customer_reason_low": "Routine daily transaction volume.",
        "investigator_template": "Observed {val:.0f} transactions in the trailing 24-hour window.",
    },
    "Velocity_7d": {
        "display_name": "7-Day Transaction Volume",
        "category": "velocity",
        "customer_reason_high": "Spike in weekly transaction volume.",
        "customer_reason_low": "Expected weekly transaction volume.",
        "investigator_template": "Recorded {val:.0f} transactions in the trailing 7-day window.",
    },
    "Failed_Attempts": {
        "display_name": "Prior Failed Auth Attempts",
        "category": "security",
        "customer_reason_high": "Multiple failed login or authentication attempts preceded this request.",
        "customer_reason_low": "Seamless authentication without prior failures.",
        "investigator_template": "{val:.0f} preceding authentication/OTP failures recorded in session.",
    },
    "Failed_Attempts_Count": {
        "display_name": "Prior Failed Auth Attempts",
        "category": "security",
        "customer_reason_high": "Multiple failed login or authentication attempts preceded this request.",
        "customer_reason_low": "Seamless authentication without prior failures.",
        "investigator_template": "{val:.0f} preceding authentication/OTP failures recorded in session.",
    },
    "New_Device": {
        "display_name": "New Device Hardware",
        "category": "device",
        "customer_reason_high": "Payment attempted from an unrecognized new device.",
        "customer_reason_low": "Recognized and trusted device.",
        "investigator_template": "Hardware signature is new/untrusted for customer account.",
    },
    "Is_New_Device": {
        "display_name": "New Device Hardware",
        "category": "device",
        "customer_reason_high": "Payment attempted from an unrecognized new device.",
        "customer_reason_low": "Recognized and trusted device.",
        "investigator_template": "Hardware signature is new/untrusted for customer account.",
    },
    "Is_New_Beneficiary": {
        "display_name": "New Recipient Beneficiary",
        "category": "beneficiary",
        "customer_reason_high": "First-time transfer to a new recipient beneficiary.",
        "customer_reason_low": "Transfer to an established, frequently used recipient.",
        "investigator_template": "Recipient beneficiary has no prior successful transfer record.",
    },
    "Unusual_Location": {
        "display_name": "Unusual Location",
        "category": "location",
        "customer_reason_high": "Transaction originated from an unfamiliar location.",
        "customer_reason_low": "Originated from your usual location.",
        "investigator_template": "Geographic location differs from customer historical operating zone.",
    },
    "Is_Unusual_Location": {
        "display_name": "Unusual Location",
        "category": "location",
        "customer_reason_high": "Transaction originated from an unfamiliar location.",
        "customer_reason_low": "Originated from your usual location.",
        "investigator_template": "Geographic location differs from customer historical operating zone.",
    },
    "International_Transaction": {
        "display_name": "Cross-Border Payment",
        "category": "location",
        "customer_reason_high": "International cross-border transaction.",
        "customer_reason_low": "Domestic local payment.",
        "investigator_template": "Cross-border payment rail routing.",
    },
    "Is_International": {
        "display_name": "Cross-Border Payment",
        "category": "location",
        "customer_reason_high": "International cross-border transaction.",
        "customer_reason_low": "Domestic local payment.",
        "investigator_template": "Cross-border payment rail routing.",
    },
    "Is_Night_Transaction": {
        "display_name": "Off-Hours Night Operation",
        "category": "time",
        "customer_reason_high": "Authorized during unusual early morning hours.",
        "customer_reason_low": "Authorized during standard daylight hours.",
        "investigator_template": "Transaction executed during off-peak night window (00:00 - 05:59).",
    },
}


def get_feature_display_name(feature_name: str) -> str:
    """Return user-friendly label for any model or risk feature name."""
    clean = feature_name.strip()
    if clean in FEATURE_METADATA:
        return str(FEATURE_METADATA[clean]["display_name"])
    for prefix in ["num__", "cat__", "remainder__"]:
        if clean.startswith(prefix):
            clean = clean[len(prefix):]
    if clean in FEATURE_METADATA:
        return str(FEATURE_METADATA[clean]["display_name"])
    return clean.replace("_", " ").title()


def format_customer_reason(feature_name: str, is_risk_increasing: bool = True) -> str:
    """Generate concise, reassuring plain-language explanation for end customers."""
    clean = feature_name.strip()
    for prefix in ["num__", "cat__", "remainder__"]:
        if clean.startswith(prefix):
            clean = clean[len(prefix):]

    meta = FEATURE_METADATA.get(clean)
    if meta:
        return str(meta["customer_reason_high"] if is_risk_increasing else meta["customer_reason_low"])
    display = get_feature_display_name(clean)
    if is_risk_increasing:
        return f"Unusual pattern detected in {display}."
    return f"Normal activity observed in {display}."


def format_investigator_reason(feature_name: str, value: Any, shap_value: float) -> str:
    """Generate detailed audit-grade technical narrative for fraud investigators."""
    clean = feature_name.strip()
    for prefix in ["num__", "cat__", "remainder__"]:
        if clean.startswith(prefix):
            clean = clean[len(prefix):]

    meta = FEATURE_METADATA.get(clean)
    display = get_feature_display_name(clean)
    direction_str = "increased" if shap_value > 0 else "decreased"
    pct = abs(shap_value) * 100.0

    if meta and "investigator_template" in meta:
        try:
            num_val = float(value) if value is not None and value != "N/A" else 0.0
            tmpl = meta["investigator_template"].format(val=num_val)
            return f"{tmpl} ({direction_str.capitalize()} risk by {pct:.1f}%)."
        except Exception:
            pass

    return f"Feature '{display}' (value: {value}) {direction_str} model fraud attribution by {pct:.1f}% (SHAP: {shap_value:+.4f})."
