"""Dataset Integration and Validation Engine for Financial Fraud Detection."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union
import numpy as np
import pandas as pd


@dataclass
class DatasetSchema:
    """Specification of expected schema for fraud detection datasets."""

    target_column: str = "risk_label"
    expected_target_values: Set[int] = field(default_factory=lambda: {0, 1})

    # Expected feature definitions (default schema for /schema endpoint & legacy datasets)
    expected_columns: Dict[str, Dict[str, Any]] = field(
        default_factory=lambda: {
            "transaction_id": {"types": ["string", "object", "str"], "required": True},
            "customer_id": {"types": ["string", "object", "str"], "required": True},
            "transaction_hour": {"types": ["integer", "int64", "int32"], "required": True},
            "transaction_day_of_week": {"types": ["integer", "int64", "int32"], "required": True},
            "account_age_days": {"types": ["integer", "float", "number"], "required": True},
            "previous_chargebacks": {"types": ["integer", "int64", "int32"], "required": True},
            "merchant_category": {"types": ["string", "object", "str"], "required": True},
            "transaction_country": {"types": ["string", "object", "str"], "required": True},
            "device_type": {"types": ["string", "object", "str"], "required": True},
            "transaction_type": {"types": ["string", "object", "str"], "required": True},
            "geo_location_region": {"types": ["string", "object", "str"], "required": True},
            "is_international": {"types": ["integer", "boolean", "int64", "bool"], "required": True},
            "is_high_risk_merchant_category": {"types": ["integer", "boolean", "int64", "bool"], "required": True},
            "is_weekend": {"types": ["integer", "boolean", "int64", "bool"], "required": True},
            "customer_total_transactions_30d": {"types": ["integer", "float", "number"], "required": True},
            "customer_risk_score": {"types": ["float", "number", "integer"], "required": False},
            "transaction_amount": {"types": ["float", "number", "integer"], "required": True},
            "avg_transaction_amount_30d_customer": {"types": ["float", "number", "integer"], "required": True},
            "transaction_velocity_1h": {"types": ["integer", "float", "number"], "required": True},
            "transaction_velocity_24h": {"types": ["integer", "float", "number"], "required": True},
            "risk_label": {"types": ["integer", "int64", "int32"], "required": True},
        }
    )

    # Primary CSV dataset schema (financial_fraud_customer_transactions.csv)
    primary_csv_columns: Dict[str, Dict[str, Any]] = field(
        default_factory=lambda: {
            "Transaction_ID": {"types": ["string", "object", "str"], "required": True},
            "Customer_ID": {"types": ["string", "object", "str"], "required": True},
            "Transaction_Number": {"types": ["integer", "int64", "int32"], "required": True},
            "Amount": {"types": ["float", "number", "integer"], "required": True},
            "Transaction_Type": {"types": ["string", "object", "str"], "required": True},
            "Transaction_Hour": {"types": ["integer", "int64", "int32"], "required": True},
            "Location": {"types": ["string", "object", "str"], "required": True},
            "Usual_Location": {"types": ["string", "object", "str"], "required": True},
            "Device_Type": {"types": ["string", "object", "str"], "required": True},
            "New_Device": {"types": ["integer", "boolean", "int64", "bool"], "required": True},
            "Account_Age_Days": {"types": ["integer", "float", "number"], "required": True},
            "Previous_Transaction_Amount": {"types": ["float", "number", "integer"], "required": True},
            "Average_Previous_Amount": {"types": ["float", "number", "integer"], "required": True},
            "Amount_Deviation": {"types": ["float", "number", "integer"], "required": True},
            "Amount_Ratio": {"types": ["float", "number", "integer"], "required": True},
            "Transactions_Last_24H": {"types": ["integer", "float", "number"], "required": True},
            "Failed_Attempts": {"types": ["integer", "int64", "int32"], "required": True},
            "International_Transaction": {"types": ["integer", "boolean", "int64", "bool"], "required": True},
            "Unusual_Location": {"types": ["integer", "boolean", "int64", "bool"], "required": True},
            "Fraud_Probability": {"types": ["float", "number", "integer"], "required": False},
            "Fraud_Label": {"types": ["integer", "int64", "int32"], "required": True},
            "Risk_Score": {"types": ["integer", "float", "number"], "required": False},
            "Risk_Level": {"types": ["string", "object", "str"], "required": False},
        }
    )

    # Valid value ranges for sanity checking
    value_constraints: Dict[str, Dict[str, Any]] = field(
        default_factory=lambda: {
            "Transaction_Hour": {"min": 0, "max": 23},
            "transaction_hour": {"min": 0, "max": 23},
            "transaction_day_of_week": {"min": 0, "max": 7},
            "Amount": {"min": 0.01},
            "transaction_amount": {"min": 0.01},
            "Account_Age_Days": {"min": 0},
            "account_age_days": {"min": 0},
            "Failed_Attempts": {"min": 0},
            "previous_chargebacks": {"min": 0},
            "Transactions_Last_24H": {"min": 0},
            "transaction_velocity_24h": {"min": 0},
            "customer_total_transactions_30d": {"min": 0},
            "transaction_velocity_1h": {"min": 0},
        }
    )

    # Known high-risk leakage candidates
    leakage_candidates: Dict[str, str] = field(
        default_factory=lambda: {
            "Fraud_Probability": "Pre-computed or reference fraud probability; direct model output / target proxy.",
            "fraud_probability": "Pre-computed or reference fraud probability; direct model output / target proxy.",
            "Risk_Score": "Direct synthetic derivation or reference score from previous model output.",
            "risk_score": "Direct synthetic derivation or reference score from previous model output.",
            "Risk_Level": "Categorical risk output from reference scoring; post-prediction classification.",
            "risk_level": "Categorical risk output from reference scoring; post-prediction classification.",
            "Fraud_Label": "Ground truth target column; must strictly be target label and never an input feature.",
            "customer_risk_score": (
                "High probability of target contamination if computed using future chargeback / fraud outcomes "
                "or post-transaction labeling rules."
            ),
            "fraud_flag": "Direct synonym for ground truth target label.",
            "post_transaction_chargeback": "Post-event settlement outcome occurring days after authorization.",
        }
    )


@dataclass
class ValidationResult:
    """Comprehensive validation output report object."""

    is_valid: bool
    file_format: Dict[str, Any]
    schema_check: Dict[str, Any]
    data_types_check: Dict[str, Any]
    missing_values: Dict[str, Any]
    duplicates: Dict[str, Any]
    target_analysis: Dict[str, Any]
    suspicious_values: Dict[str, Any]
    summary_statistics: Dict[str, Any]
    leakage_audit: Dict[str, Any]
    errors: List[str]
    warnings: List[str]
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        # Expose total_rows and total_columns at top level for frontend convenience
        total_rows = self.file_format.get("total_rows", 0)
        total_columns = self.file_format.get("total_columns", 0)
        ta = self.target_analysis or {}
        return {
            "is_valid": self.is_valid,
            "total_rows": total_rows,
            "total_columns": total_columns,
            "file_format": self.file_format,
            "schema_check": self.schema_check,
            "data_types_check": self.data_types_check,
            "missing_values": self.missing_values,
            "duplicates": self.duplicates,
            "target_analysis": ta,
            # Convenience top-level target distribution
            "target_distribution": {
                "fraud_count": ta.get("fraud_count", 0),
                "normal_count": ta.get("normal_count", 0),
                "fraud_percentage": ta.get("fraud_rate_percentage", 0.0),
            },
            "suspicious_values": self.suspicious_values,
            "summary_statistics": self.summary_statistics,
            "leakage_audit": self.leakage_audit,
            "errors": self.errors,
            "warnings": self.warnings,
            "timestamp": self.timestamp,
        }


class DatasetValidator:
    """Reusable validation suite enforcing 11-step audit for financial fraud datasets."""

    def __init__(self, schema: Optional[DatasetSchema] = None) -> None:
        self.schema = schema or DatasetSchema()

    def validate_file(self, file_path: Union[str, Path]) -> ValidationResult:
        """Validate dataset file from filesystem (supports .csv, .parquet, .json)."""
        path = Path(file_path)
        errors: List[str] = []
        warnings: List[str] = []

        # 1. File format validation
        if not path.exists():
            return ValidationResult(
                is_valid=False,
                file_format={"exists": False, "path": str(path)},
                schema_check={},
                data_types_check={},
                missing_values={},
                duplicates={},
                target_analysis={},
                suspicious_values={},
                summary_statistics={},
                leakage_audit={},
                errors=[f"Dataset file not found at path: {path}"],
                warnings=[],
            )

        suffix = path.suffix.lower()
        if suffix not in [".csv", ".parquet", ".json"]:
            errors.append(f"Unsupported file format '{suffix}'. Expected .csv, .parquet, or .json")
            return ValidationResult(
                is_valid=False,
                file_format={"exists": True, "suffix": suffix, "path": str(path)},
                schema_check={},
                data_types_check={},
                missing_values={},
                duplicates={},
                target_analysis={},
                suspicious_values={},
                summary_statistics={},
                leakage_audit={},
                errors=errors,
                warnings=warnings,
            )

        try:
            if suffix == ".csv":
                df = pd.read_csv(path)
            elif suffix == ".parquet":
                df = pd.read_parquet(path)
            else:
                df = pd.read_json(path)
        except Exception as e:
            return ValidationResult(
                is_valid=False,
                file_format={"exists": True, "suffix": suffix, "path": str(path)},
                schema_check={},
                data_types_check={},
                missing_values={},
                duplicates={},
                target_analysis={},
                suspicious_values={},
                summary_statistics={},
                leakage_audit={},
                errors=[f"Failed to parse dataset file: {str(e)}"],
                warnings=[],
            )

        return self.validate_dataframe(df, file_type=suffix)

    def validate_dataframe(self, df: pd.DataFrame, file_type: str = "DataFrame") -> ValidationResult:
        """Perform comprehensive 11-step audit on loaded pandas DataFrame."""
        errors: List[str] = []
        warnings: List[str] = []

        total_rows, total_cols = df.shape
        file_format_info = {
            "file_type": file_type,
            "total_rows": total_rows,
            "total_columns": total_cols,
            "memory_usage_mb": round(df.memory_usage(deep=True).sum() / (1024 * 1024), 2),
        }

        if total_rows == 0:
            errors.append("Dataset contains 0 rows (empty dataset).")
            return self._build_empty_result(file_format_info, errors)

        # 2 & 3. Schema & Required Columns
        actual_columns = set(df.columns)
        # Select appropriate schema definition
        if "Fraud_Label" in df.columns or "Amount" in df.columns:
            expected_cols_def = self.schema.primary_csv_columns
            target_col = "Fraud_Label"
        elif "is_fraud" in df.columns:
            schema_cols = dict(self.schema.expected_columns)
            schema_cols.pop("risk_label", None)
            schema_cols["is_fraud"] = {"types": ["integer", "int64", "int32"], "required": True}
            expected_cols_def = schema_cols
            target_col = "is_fraud"
        elif "risk_label" in df.columns or "transaction_amount" in df.columns:
            expected_cols_def = self.schema.expected_columns
            target_col = "risk_label"
        else:
            expected_cols_def = self.schema.expected_columns
            target_col = self.schema.target_column

        required_columns = {k for k, v in expected_cols_def.items() if v.get("required", False)}
        missing_required = required_columns - actual_columns
        extra_columns = list(actual_columns - set(expected_cols_def.keys()))
        matched_columns = list(actual_columns.intersection(set(expected_cols_def.keys())))

        if missing_required:
            errors.append(f"Missing required columns: {sorted(list(missing_required))}")

        if extra_columns:
            warnings.append(f"Discovered extra/unrecognized columns: {extra_columns}")

        schema_check = {
            "passed": len(missing_required) == 0,
            "required_columns_count": len(required_columns),
            "matched_columns_count": len(matched_columns),
            "missing_required_columns": sorted(list(missing_required)),
            "extra_columns": sorted(extra_columns),
        }

        # 4. Data-Type Validation
        type_mismatches: Dict[str, Dict[str, str]] = {}
        for col in matched_columns:
            dtype_str = str(df[col].dtype).lower()
            expected_type_list = expected_cols_def[col]["types"]
            # Type matching heuristics
            is_match = False
            if "integer" in expected_type_list or "int64" in expected_type_list or "int32" in expected_type_list:
                if "int" in dtype_str or (df[col].dropna().apply(lambda x: float(x).is_integer()).all() if len(df[col].dropna()) > 0 and pd.api.types.is_numeric_dtype(df[col]) else False):
                    is_match = True
            if "float" in expected_type_list or "number" in expected_type_list:
                if pd.api.types.is_numeric_dtype(df[col]):
                    is_match = True
            if "string" in expected_type_list or "object" in expected_type_list or "str" in expected_type_list:
                if dtype_str in ["object", "string", "category", "str"]:
                    is_match = True
            if "boolean" in expected_type_list or "bool" in expected_type_list:
                if dtype_str == "bool" or set(df[col].dropna().unique()).issubset({0, 1, True, False, "0", "1"}):
                    is_match = True

            if not is_match:
                type_mismatches[col] = {
                    "actual_dtype": dtype_str,
                    "expected_types": expected_type_list,
                }
                warnings.append(f"Column '{col}' has actual dtype '{dtype_str}' which may not match {expected_type_list}")

        data_types_check = {
            "passed": len(type_mismatches) == 0,
            "type_mismatches": type_mismatches,
            "column_dtypes": {col: str(df[col].dtype) for col in df.columns},
        }

        # 5. Missing-Value Analysis
        missing_counts = df.isnull().sum().to_dict()
        missing_pcts = (df.isnull().sum() / total_rows * 100).round(2).to_dict()
        columns_with_nulls = {k: v for k, v in missing_counts.items() if v > 0}

        if columns_with_nulls:
            for col, count in columns_with_nulls.items():
                pct = missing_pcts[col]
                if pct > 30.0:
                    warnings.append(f"Column '{col}' has severe missing rate: {pct}% ({count}/{total_rows})")
                else:
                    warnings.append(f"Column '{col}' has missing values: {pct}% ({count}/{total_rows})")

        missing_values = {
            "has_missing_values": len(columns_with_nulls) > 0,
            "total_null_entries": int(df.isnull().sum().sum()),
            "columns_with_missing_count": len(columns_with_nulls),
            "missing_counts": missing_counts,
            "missing_percentages": missing_pcts,
        }

        # 6. Duplicate Analysis
        duplicate_rows = int(df.duplicated().sum())
        duplicate_tx_ids = 0
        tx_col_name = "Transaction_ID" if "Transaction_ID" in df.columns else ("transaction_id" if "transaction_id" in df.columns else None)
        if tx_col_name:
            duplicate_tx_ids = int(df[tx_col_name].duplicated().sum())
            if duplicate_tx_ids > 0:
                errors.append(f"Found {duplicate_tx_ids} duplicate {tx_col_name} values (primary key violation)")

        if duplicate_rows > 0:
            warnings.append(f"Found {duplicate_rows} duplicate rows across all features")

        duplicates = {
            "duplicate_rows": duplicate_rows,
            "duplicate_transaction_ids": duplicate_tx_ids,
        }

        # 7 & 8. Target-Value Validation & Class Distribution
        target_analysis: Dict[str, Any] = {"has_target": False}
        if target_col in df.columns:
            unique_targets = set(df[target_col].dropna().unique())
            is_valid_binary = unique_targets.issubset(self.schema.expected_target_values)
            if not is_valid_binary:
                errors.append(
                    f"Target '{target_col}' contains invalid values: {unique_targets}. "
                    f"Expected subset of {self.schema.expected_target_values} (0 = normal, 1 = fraud)"
                )

            counts = df[target_col].value_counts().to_dict()
            norm_counts = df[target_col].value_counts(normalize=True).to_dict()

            fraud_count = int(counts.get(1, 0))
            normal_count = int(counts.get(0, 0))
            fraud_rate = round(float(norm_counts.get(1, 0.0)) * 100, 3)

            target_analysis = {
                "has_target": True,
                "target_name": target_col,
                "unique_values": [int(x) if isinstance(x, (int, np.integer)) else x for x in unique_targets],
                "is_binary": is_valid_binary,
                "class_counts": {str(k): int(v) for k, v in counts.items()},
                "class_percentages": {str(k): round(float(v) * 100, 3) for k, v in norm_counts.items()},
                "normal_count": normal_count,
                "fraud_count": fraud_count,
                "fraud_rate_percentage": fraud_rate,
                "imbalance_ratio": f"1:{round(normal_count / fraud_count, 1)}" if fraud_count > 0 else "N/A",
            }
        else:
            warnings.append(f"Target column '{target_col}' is absent in dataset")

        # 9. Suspicious & Out-of-Bounds Values
        suspicious_records: Dict[str, Any] = {}
        for col, constraints in self.schema.value_constraints.items():
            if col in df.columns and pd.api.types.is_numeric_dtype(df[col]):
                if "min" in constraints:
                    below_min = int((df[col] < constraints["min"]).sum())
                    if below_min > 0:
                        suspicious_records[f"{col}_below_min_{constraints['min']}"] = below_min
                        warnings.append(f"Column '{col}' has {below_min} values below minimum threshold {constraints['min']}")
                if "max" in constraints:
                    above_max = int((df[col] > constraints["max"]).sum())
                    if above_max > 0:
                        suspicious_records[f"{col}_above_max_{constraints['max']}"] = above_max
                        warnings.append(f"Column '{col}' has {above_max} values above maximum threshold {constraints['max']}")

        suspicious_values = {
            "has_suspicious_values": len(suspicious_records) > 0,
            "suspicious_counts": suspicious_records,
        }

        # 10. Basic Statistical Summary
        num_cols = df.select_dtypes(include=[np.number]).columns
        cat_cols = df.select_dtypes(include=["object", "string", "category"]).columns

        stat_summary: Dict[str, Any] = {"numerical": {}, "categorical": {}}
        for col in num_cols:
            s = df[col].dropna()
            if len(s) > 0:
                stat_summary["numerical"][col] = {
                    "mean": round(float(s.mean()), 4),
                    "std": round(float(s.std()), 4) if len(s) > 1 else 0.0,
                    "min": round(float(s.min()), 4),
                    "25%": round(float(s.quantile(0.25)), 4),
                    "50%": round(float(s.median()), 4),
                    "75%": round(float(s.quantile(0.75)), 4),
                    "max": round(float(s.max()), 4),
                }

        for col in cat_cols:
            s = df[col].dropna()
            stat_summary["categorical"][col] = {
                "unique_count": int(s.nunique()),
                "top_categories": s.value_counts().head(5).to_dict(),
            }

        # 11. Target Leakage & Feature Leakage Audit
        leakage_audit = self.audit_leakage(df, target_col=target_col)

        is_valid = len(errors) == 0

        return ValidationResult(
            is_valid=is_valid,
            file_format=file_format_info,
            schema_check=schema_check,
            data_types_check=data_types_check,
            missing_values=missing_values,
            duplicates=duplicates,
            target_analysis=target_analysis,
            suspicious_values=suspicious_values,
            summary_statistics=stat_summary,
            leakage_audit=leakage_audit,
            errors=errors,
            warnings=warnings,
        )

    def audit_leakage(self, df: pd.DataFrame, target_col: Optional[str] = None) -> Dict[str, Any]:
        """Deep audit of feature leakage, target proxy contamination, and post-event aggregates."""
        if target_col is None:
            target_col = "Fraud_Label" if "Fraud_Label" in df.columns else ("risk_label" if "risk_label" in df.columns else self.schema.target_column)

        safe_features: List[Dict[str, str]] = []
        risky_features: List[Dict[str, Any]] = []
        excluded_features: List[Dict[str, Any]] = []

        all_cols = [c for c in df.columns if c != target_col]
        has_target = target_col in df.columns and pd.api.types.is_numeric_dtype(df[target_col])

        for col in all_cols:
            # Check 1: Known leakage candidates by name / engineering pattern
            if col in self.schema.leakage_candidates:
                reason = self.schema.leakage_candidates[col]
                excluded_features.append({
                    "feature": col,
                    "reason": reason,
                    "leakage_type": "Direct / Engineered Risk Contamination",
                    "status": "EXCLUDED",
                })
                continue

            # Check 2: Identifier columns (not predictive features, leak row identifiers)
            if col in ["transaction_id", "id", "case_id", "Transaction_ID", "Customer_ID", "Transaction_Number", "customer_id"]:
                excluded_features.append({
                    "feature": col,
                    "reason": "Unique identifier / sequence column; must not be passed to ML models.",
                    "leakage_type": "Identifier Leakage",
                    "status": "EXCLUDED",
                })
                continue

            # Check 3: Mathematical correlation / perfect separability with target
            if has_target and pd.api.types.is_numeric_dtype(df[col]):
                valid_mask = df[col].notnull() & df[target_col].notnull()
                if valid_mask.sum() > 10:
                    corr = float(np.corrcoef(df.loc[valid_mask, col], df.loc[valid_mask, target_col])[0, 1])
                    abs_corr = abs(corr) if not np.isnan(corr) else 0.0

                    if abs_corr > 0.95:
                        excluded_features.append({
                            "feature": col,
                            "reason": f"Extreme correlation (|r| = {round(abs_corr, 4)}) indicating exact proxy or synthetic leakage.",
                            "leakage_type": "Target Proxy Leakage",
                            "correlation": round(corr, 4),
                            "status": "EXCLUDED",
                        })
                        continue
                    elif abs_corr > 0.70:
                        risky_features.append({
                            "feature": col,
                            "reason": f"High correlation (|r| = {round(abs_corr, 4)}); requires SHAP / attribution verification before training.",
                            "risk_level": "POTENTIALLY_RISKY",
                            "correlation": round(corr, 4),
                        })
                        continue

            # Feature passed leakage audit safely
            safe_features.append({
                "feature": col,
                "status": "SAFE",
                "description": "Pre-transaction authorization feature suitable for baseline model training.",
            })

        return {
            "safe_features": safe_features,
            "safe_features_count": len(safe_features),
            "risky_features": risky_features,
            "risky_features_count": len(risky_features),
            "excluded_features": excluded_features,
            "excluded_features_count": len(excluded_features),
            "summary": (
                f"Leakage audit completed: {len(safe_features)} safe features, "
                f"{len(risky_features)} potentially risky features, "
                f"{len(excluded_features)} excluded features due to target leakage / identifier constraints."
            ),
        }

    def _build_empty_result(self, file_format_info: Dict[str, Any], errors: List[str]) -> ValidationResult:
        return ValidationResult(
            is_valid=False,
            file_format=file_format_info,
            schema_check={"passed": False},
            data_types_check={"passed": False},
            missing_values={},
            duplicates={},
            target_analysis={},
            suspicious_values={},
            summary_statistics={},
            leakage_audit={},
            errors=errors,
            warnings=[],
        )
