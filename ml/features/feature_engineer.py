"""Feature Engineering Transformer for Financial Fraud Detection."""

from typing import List, Optional, Set
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin


class FraudFeatureEngineer(BaseEstimator, TransformerMixin):
    """Scikit-Learn compatible transformer creating behavioural, velocity,
    interaction, and temporal fraud features.

    Excludes target leakage candidates and non-predictive identifiers.
    Supports both the primary dataset (financial_fraud_customer_transactions.csv)
    and legacy schema inputs.
    """

    def __init__(
        self,
        excluded_columns: Optional[List[str]] = None,
        drop_identifiers: bool = True,
    ) -> None:
        self.excluded_columns: Set[str] = set(
            excluded_columns
            or [
                # Primary CSV leakage candidates
                "Fraud_Probability",
                "fraud_probability",
                "Risk_Score",
                "risk_score",
                "Risk_Level",
                "risk_level",
                "Fraud_Label",
                "risk_label",
                # Legacy candidates
                "customer_risk_score",
                "fraud_flag",
            ]
        )
        self.drop_identifiers: bool = drop_identifiers
        self.identifier_columns: Set[str] = {
            "Transaction_ID",
            "Customer_ID",
            "Transaction_Number",
            "transaction_id",
            "customer_id",
            "id",
            "case_id",
        }
        self.engineered_feature_names_: List[str] = []

    def fit(self, X: pd.DataFrame, y: Optional[pd.Series] = None) -> "FraudFeatureEngineer":
        """Fit transformer (records output feature structure)."""
        return self

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        """Derive behavioural ratios, velocity interactions, non-linear scales,
        and cyclical temporal features.
        """
        if not isinstance(X, pd.DataFrame):
            X = pd.DataFrame(X)

        df = X.copy()

        # 1. Drop known target leakage columns if present
        cols_to_drop = [c for c in self.excluded_columns if c in df.columns]
        if cols_to_drop:
            df = df.drop(columns=cols_to_drop)

        # 2. Drop unique row identifiers from model feature matrix
        if self.drop_identifiers:
            id_cols = [c for c in self.identifier_columns if c in df.columns]
            if id_cols:
                df = df.drop(columns=id_cols)

        # Helper: Extract unified amount
        amt_col = "Amount" if "Amount" in df.columns else ("transaction_amount" if "transaction_amount" in df.columns else None)

        # 3. Behavioral Amount Features & Non-linear scaling
        if amt_col is not None:
            amt = df[amt_col].clip(lower=0.0)
            df["log_amount"] = np.log1p(amt)

            # Ratio & deviation vs historical average
            avg_hist = df["Average_Previous_Amount"].clip(lower=1.0) if "Average_Previous_Amount" in df.columns else (
                df["avg_transaction_amount_30d_customer"].clip(lower=1.0) if "avg_transaction_amount_30d_customer" in df.columns else (amt + 1.0)
            )
            df["amount_to_average_ratio"] = amt / (avg_hist + 1e-5)
            df["Amount_Ratio"] = df["amount_to_average_ratio"]

            if "Average_Previous_Amount" in df.columns:
                df["Amount_Deviation"] = amt - df["Average_Previous_Amount"]
            else:
                df["Amount_Deviation"] = amt - avg_hist
            df["amount_deviation_strength"] = df["Amount_Deviation"] / (avg_hist + 1e-5)

            # Ratio vs immediate previous transaction
            if "Previous_Transaction_Amount" in df.columns:
                prev_amt = df["Previous_Transaction_Amount"].clip(lower=1.0)
                df["amount_to_prev_ratio"] = amt / (prev_amt + 1e-5)
                df["amount_diff_prev_abs"] = np.abs(amt - prev_amt)

            # High amount multiplier flag (Transactions > 2.5x normal baseline)
            df["is_extreme_amount_surge"] = (df["amount_to_average_ratio"] > 2.5).astype(float)

            # Account age vulnerability (New account high transaction surge)
            if "Account_Age_Days" in df.columns:
                df["amount_to_account_age_ratio"] = amt / (df["Account_Age_Days"].clip(lower=1.0) + 1.0)
            elif "account_age_days" in df.columns:
                df["amount_to_account_age_ratio"] = amt / (df["account_age_days"].clip(lower=1.0) + 1.0)

            # Velocity interaction: Transaction volume surge in 24h
            if "Transactions_Last_24H" in df.columns:
                df["amount_velocity_24h_surge"] = amt * (df["Transactions_Last_24H"] + 1.0)
                df["velocity_intensity"] = df["Transactions_Last_24H"].astype(float) / 24.0
                df["recent_transaction_activity"] = df["Transactions_Last_24H"].astype(float)
            elif "transaction_velocity_24h" in df.columns:
                df["amount_velocity_24h_surge"] = amt * (df["transaction_velocity_24h"] + 1.0)
                df["velocity_intensity"] = df["transaction_velocity_24h"].astype(float) / 24.0
                df["recent_transaction_activity"] = df["transaction_velocity_24h"].astype(float)

        # 4. Behavioral Amount Features (Legacy Schema)
        if "transaction_amount" in df.columns:
            if "avg_transaction_amount_30d_customer" in df.columns:
                df["amount_to_avg_ratio"] = df["transaction_amount"] / (
                    df["avg_transaction_amount_30d_customer"].clip(lower=1.0) + 1e-5
                )
            if "transaction_velocity_1h" in df.columns:
                df["amount_to_velocity_1h_ratio"] = df["transaction_amount"] / (
                    df["transaction_velocity_1h"] + 1.0
                )

        # 5. Location Mismatch Feature (Primary CSV)
        if "Location" in df.columns and "Usual_Location" in df.columns:
            df["location_change_signal"] = (
                df["Location"].astype(str) != df["Usual_Location"].astype(str)
            ).astype(float)
            df["is_location_mismatch"] = df["location_change_signal"]

        # 6. High-Risk Multi-Factor Fraud Interactions
        new_dev = df["New_Device"] if "New_Device" in df.columns else (df.get("new_device", pd.Series(0, index=df.index)))
        intl_tx = df["International_Transaction"] if "International_Transaction" in df.columns else (df.get("is_international", pd.Series(0, index=df.index)))
        unusual_loc = df["Unusual_Location"] if "Unusual_Location" in df.columns else (df.get("location_change_signal", df.get("is_location_mismatch", pd.Series(0, index=df.index))))
        failed_att = df["Failed_Attempts"] if "Failed_Attempts" in df.columns else (df.get("failed_attempts", pd.Series(0, index=df.index)))
        tx_24h = df["Transactions_Last_24H"] if "Transactions_Last_24H" in df.columns else (df.get("transaction_velocity_24h", pd.Series(1, index=df.index)))
        amt_ratio_sig = df.get("amount_to_average_ratio", df.get("Amount_Ratio", pd.Series(1.0, index=df.index)))

        df["device_change_signal"] = new_dev.astype(float)
        df["failed_attempt_intensity"] = failed_att.astype(float) / (tx_24h.astype(float) + 1.0)
        df["international_risk_signal"] = intl_tx.astype(float) * (unusual_loc.astype(float) + new_dev.astype(float) + 0.5)

        # Account Takeover Signal: New Device + Unusual Location
        df["account_takeover_risk"] = (new_dev.astype(float) * unusual_loc.astype(float))

        # International New Device Signal
        df["intl_new_device_risk"] = (intl_tx.astype(float) * new_dev.astype(float))

        # International Unusual Location Signal
        df["intl_unusual_loc_risk"] = (intl_tx.astype(float) * unusual_loc.astype(float))

        # Amount surge combined with unusual location / new device (Classic Fraud Pattern)
        df["surge_on_unusual_loc"] = amt_ratio_sig.astype(float) * unusual_loc.astype(float)
        df["surge_on_new_device"] = amt_ratio_sig.astype(float) * new_dev.astype(float)
        df["surge_on_intl"] = amt_ratio_sig.astype(float) * intl_tx.astype(float)

        # Credential Stuffing / Brute Force Surge
        df["failed_attempts_velocity_surge"] = failed_att.astype(float) * (tx_24h.astype(float) + 1.0)
        df["failed_attempts_new_device"] = failed_att.astype(float) * (new_dev.astype(float) + 1.0)
        df["failed_attempts_amount_risk"] = failed_att.astype(float) * amt_ratio_sig.astype(float)

        # 7. Velocity Interactions (Legacy schema support)
        if "transaction_velocity_1h" in df.columns and "transaction_velocity_24h" in df.columns:
            df["velocity_ratio_1h_24h"] = df["transaction_velocity_1h"] / (
                df["transaction_velocity_24h"] + 1.0
            )

        if "previous_chargebacks" in df.columns and "customer_total_transactions_30d" in df.columns:
            df["chargeback_rate_30d"] = df["previous_chargebacks"] / (
                df["customer_total_transactions_30d"] + 1.0
            )

        # 8. Temporal & Cyclical Features (Primary & Legacy)
        hour_col = None
        if "Transaction_Hour" in df.columns:
            hour_col = "Transaction_Hour"
        elif "transaction_hour" in df.columns:
            hour_col = "transaction_hour"

        if hour_col is not None:
            # Night-time fraud vulnerability window (00:00 - 05:59)
            df["is_night_transaction"] = df[hour_col].isin([0, 1, 2, 3, 4, 5]).astype(float)
            df["temporal_risk_signal"] = df["is_night_transaction"]
            # Night-time + unusual location interaction
            df["night_unusual_loc_risk"] = df["is_night_transaction"] * unusual_loc.astype(float)
            df["night_surge_risk"] = df["is_night_transaction"] * amt_ratio_sig.astype(float)
            # Cyclical trigonometric projection for 24-hour daily cycle
            df["sin_hour"] = np.sin(2 * np.pi * df[hour_col] / 24.0)
            df["cos_hour"] = np.cos(2 * np.pi * df[hour_col] / 24.0)

        if "transaction_day_of_week" in df.columns:
            # Cyclical trigonometric projection for 7-day weekly cycle
            df["sin_day_of_week"] = np.sin(2 * np.pi * df["transaction_day_of_week"] / 7.0)
            df["cos_day_of_week"] = np.cos(2 * np.pi * df["transaction_day_of_week"] / 7.0)

        # 9. Composite Fraud Risk Flag Index & Customer Behavior Deviation
        night_sig = df.get("is_night_transaction", pd.Series(0, index=df.index))
        extreme_surge = df.get("is_extreme_amount_surge", pd.Series(0, index=df.index))
        failed_flag = (failed_att > 0).astype(float)
        dev_strength = df.get("amount_deviation_strength", pd.Series(0.0, index=df.index)).clip(lower=0.0)

        df["composite_risk_flag_count"] = (
            new_dev.astype(float)
            + unusual_loc.astype(float)
            + intl_tx.astype(float)
            + night_sig.astype(float)
            + extreme_surge.astype(float)
            + failed_flag
        )

        df["customer_behaviour_deviation"] = (
            dev_strength.astype(float) * 0.4
            + new_dev.astype(float) * 0.2
            + unusual_loc.astype(float) * 0.2
            + (failed_att.astype(float) > 0).astype(float) * 0.2
        )

        # Replace any potential infinite values caused by divisions with zero/near-zero
        df = df.replace([np.inf, -np.inf], np.nan)

        self.engineered_feature_names_ = list(df.columns)
        return df

    def get_feature_names_out(self, input_features: Optional[List[str]] = None) -> List[str]:
        """Return names of output features."""
        return self.engineered_feature_names_

