"""Prediction and Explainability Service Layer."""

from dataclasses import asdict
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import joblib
import numpy as np
import pandas as pd

from backend.app.schemas.prediction import (
    TransactionPredictionInput,
    PredictionResponse,
    LocalExplanationResponse,
    GlobalExplanationResponse,
)
from backend.app.services.risk_scoring_service import RiskScoringEngine
from ml.preprocessing.pipeline import FullFraudPreprocessor
from ml.explainability.shap_explainer import FraudShapExplainer


class FraudPredictionService:
    """Singleton service for real-time fraud scoring, multi-factor risk evaluation, and SHAP attribution."""

    _instance: Optional["FraudPredictionService"] = None

    def __init__(self, artifact_dir: Union[str, Path] = "ml/artifacts") -> None:
        self.artifact_dir = Path(artifact_dir)
        self.preprocessor: Optional[FullFraudPreprocessor] = None
        self.model: Optional[Any] = None
        self.metadata: Dict[str, Any] = {}
        self.model_name: str = "Unknown"
        self.model_version: str = "v1.0.0"
        self.threshold: float = 0.5
        self.risk_engine = RiskScoringEngine()
        self.shap_explainer: Optional[FraudShapExplainer] = None
        self.is_ready: bool = False

        self._load_artifacts()

    @classmethod
    def get_instance(cls, artifact_dir: Union[str, Path] = "ml/artifacts") -> "FraudPredictionService":
        """Get or initialize singleton prediction service instance."""
        if cls._instance is None:
            cls._instance = cls(artifact_dir=artifact_dir)
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """Reset singleton instance (useful during testing)."""
        cls._instance = None

    def _load_artifacts(self) -> None:
        """Load preprocessor, active model binary, threshold metadata, and initialize SHAP explainer."""
        meta_file = self.artifact_dir / "active_model_metadata.json"
        preprocessor_file = self.artifact_dir / "preprocessor.joblib"

        if not meta_file.exists() or not preprocessor_file.exists():
            self.is_ready = False
            return

        # 1. Load active metadata
        with open(meta_file, "r", encoding="utf-8") as f:
            self.metadata = json.load(f)

        self.model_name = self.metadata.get("model_name", "xgboost")
        self.model_version = self.metadata.get("model_version", "v1.0.0")
        self.threshold = float(self.metadata.get("selected_threshold", 0.5))

        # 2. Load Preprocessor
        self.preprocessor = joblib.load(preprocessor_file)

        # 3. Load Active Model
        model_file = self.artifact_dir / f"{self.model_name}.joblib"
        if not model_file.exists():
            raise FileNotFoundError(f"Active model binary not found at: {model_file}")

        self.model = joblib.load(model_file)

        # 4. Initialize SHAP Explainer
        feature_names = self.preprocessor.get_feature_names_out()
        self.shap_explainer = FraudShapExplainer(
            model=self.model,
            feature_names=feature_names,
            model_name=self.model_name,
            model_version=self.model_version,
            artifact_dir=str(self.artifact_dir),
        )

        self.is_ready = True

    def _prepare_row_df(self, raw_dict: Dict[str, Any]) -> pd.DataFrame:
        """Ensure input payload has all primary dataset features and legacy fields normalized."""
        d = dict(raw_dict)
        amt = float(d.get("Amount", d.get("transaction_amount", 100.0)))
        d["Amount"] = amt
        d["transaction_amount"] = amt

        avg_amt = float(d.get("Average_Previous_Amount", d.get("avg_transaction_amount_30d_customer", amt)))
        d["Average_Previous_Amount"] = avg_amt
        d["avg_transaction_amount_30d_customer"] = avg_amt

        prev_amt = float(d.get("Previous_Transaction_Amount", avg_amt))
        d["Previous_Transaction_Amount"] = prev_amt

        d["Amount_Deviation"] = float(d.get("Amount_Deviation", amt - avg_amt))
        d["Amount_Ratio"] = float(d.get("Amount_Ratio", amt / (avg_amt + 1e-5)))

        tx_type = str(d.get("Transaction_Type", d.get("transaction_type", "Purchase")))
        d["Transaction_Type"] = tx_type
        d["transaction_type"] = tx_type

        tx_hour = int(d.get("Transaction_Hour", d.get("transaction_hour", 12)))
        d["Transaction_Hour"] = tx_hour
        d["transaction_hour"] = tx_hour

        loc = str(d.get("Location", d.get("geo_location_region", "Pune")))
        d["Location"] = loc
        d["geo_location_region"] = loc
        d["Usual_Location"] = str(d.get("Usual_Location", loc))

        dev = str(d.get("Device_Type", d.get("device_type", "Mac")))
        d["Device_Type"] = dev
        d["device_type"] = dev

        d["New_Device"] = int(d.get("New_Device", 0))
        acc_age = float(d.get("Account_Age_Days", d.get("account_age_days", 365.0)))
        d["Account_Age_Days"] = acc_age
        d["account_age_days"] = acc_age

        vel_24 = float(d.get("Transactions_Last_24H", d.get("transaction_velocity_24h", 2.0)))
        d["Transactions_Last_24H"] = vel_24
        d["transaction_velocity_24h"] = vel_24
        d["transaction_velocity_1h"] = float(d.get("transaction_velocity_1h", vel_24 / 4.0))

        d["Failed_Attempts"] = int(d.get("Failed_Attempts", 0))
        intl = int(d.get("International_Transaction", d.get("is_international", 0)))
        d["International_Transaction"] = intl
        d["is_international"] = intl

        d["Unusual_Location"] = int(d.get("Unusual_Location", 1 if d.get("Location") != d.get("Usual_Location") else 0))

        return pd.DataFrame([d])

    def predict_transaction(
        self,
        input_data: TransactionPredictionInput,
        threshold_override: Optional[float] = None,
        include_shap_summary: bool = True,
    ) -> PredictionResponse:
        """Execute end-to-end pipeline: Input -> Preprocessing -> Model -> Risk Engine -> SHAP Summary."""
        if not self.is_ready or self.model is None or self.preprocessor is None:
            self._load_artifacts()
            if not self.is_ready or self.model is None or self.preprocessor is None:
                raise RuntimeError(
                    "FraudPredictionService is not ready. ML model artifacts have not been generated yet. "
                    "Run Phase 6/7 training pipeline first."
                )

        raw_dict = input_data.model_dump()
        df_row = self._prepare_row_df(raw_dict)

        # 1. Preprocess using saved pipeline
        transformed_mat = self.preprocessor.transform(df_row)

        # 2. Compute Model Fraud Probability
        if hasattr(self.model, "predict_proba"):
            probs = self.model.predict_proba(transformed_mat)[:, 1]
            raw_prob = float(probs[0])
        elif hasattr(self.model, "decision_function"):
            decision = self.model.decision_function(transformed_mat)
            raw_prob = float(1.0 / (1.0 + np.exp(-decision[0])))
        else:
            raw_prob = float(self.model.predict(transformed_mat)[0])

        prob = max(0.0, min(1.0, raw_prob))

        # 3. Apply Decision Threshold
        applied_threshold = threshold_override if threshold_override is not None else self.threshold
        prediction_label = "FRAUD" if prob >= applied_threshold else "GENUINE"

        # 4. Compute Holistic Risk Score (0-100) & Risk Level (LOW, MEDIUM, HIGH)
        risk_result = self.risk_engine.compute_risk_score(
            fraud_probability=prob,
            transaction_data=raw_dict,
        )

        # 5. Compute SHAP Top Factors (if requested)
        top_shap_factors: Optional[List[Dict[str, Any]]] = None
        if include_shap_summary and self.shap_explainer is not None:
            try:
                local_exp = self.shap_explainer.explain_local(transformed_mat, fraud_prob=prob, top_k=3)
                top_shap_factors = [
                    {
                        "feature_name": f.feature_name,
                        "shap_value": f.shap_value,
                        "impact": f.impact,
                        "detail": f.detail,
                    }
                    for f in local_exp.top_risk_increasing_factors + local_exp.top_risk_decreasing_factors
                ][:4]
            except Exception:
                top_shap_factors = None

        return PredictionResponse(
            prediction=prediction_label,
            fraud_probability=round(prob, 4),
            risk_score=risk_result.risk_score,
            risk_level=risk_result.risk_level.value,
            model_name=self.model_name,
            model_version=self.model_version,
            threshold_used=round(applied_threshold, 4),
            transaction_id=input_data.transaction_id,
            risk_factors=[
                {
                    "factor": f.factor,
                    "impact_score": round(f.impact_score, 2),
                    "severity": f.severity,
                    "detail": f.detail,
                }
                for f in risk_result.risk_factors
            ],
            top_shap_factors=top_shap_factors,
        )

    def explain_transaction(
        self,
        input_data: TransactionPredictionInput,
        top_k: int = 5,
    ) -> LocalExplanationResponse:
        """Compute full local feature-by-feature SHAP attribution report for a single transaction."""
        if not self.is_ready or self.shap_explainer is None or self.preprocessor is None:
            self._load_artifacts()
            if not self.is_ready or self.shap_explainer is None or self.preprocessor is None:
                raise RuntimeError("FraudPredictionService is not ready. Missing model or SHAP explainer artifacts.")

        raw_dict = input_data.model_dump()
        df_row = self._prepare_row_df(raw_dict)
        transformed_mat = self.preprocessor.transform(df_row)

        # Get probability
        if hasattr(self.model, "predict_proba"):
            probs = self.model.predict_proba(transformed_mat)[:, 1]
            prob = float(probs[0])
        else:
            prob = 0.5

        risk_result = self.risk_engine.compute_risk_score(fraud_probability=prob, transaction_data=raw_dict)
        prediction_label = "FRAUD" if prob >= self.threshold else "GENUINE"

        local_exp = self.shap_explainer.explain_local(transformed_mat, fraud_prob=prob, top_k=top_k)

        return LocalExplanationResponse(
            transaction_id=input_data.transaction_id,
            prediction=prediction_label,
            fraud_probability=round(prob, 4),
            risk_score=risk_result.risk_score,
            risk_level=risk_result.risk_level.value,
            base_value=local_exp.base_value,
            top_risk_increasing_factors=[asdict(f) for f in local_exp.top_risk_increasing_factors],
            top_risk_decreasing_factors=[asdict(f) for f in local_exp.top_risk_decreasing_factors],
            all_attributions=[asdict(f) for f in local_exp.all_attributions],
        )

    def get_global_explanation(self) -> GlobalExplanationResponse:
        """Retrieve precomputed global feature importance rankings."""
        cache_file = self.artifact_dir / "global_shap_explanation.json"
        if cache_file.exists():
            with open(cache_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            return GlobalExplanationResponse(**data)

        # If not cached yet, generate from dummy background baseline
        if self.shap_explainer is not None:
            dummy_matrix = np.random.randn(50, len(self.preprocessor.get_feature_names_out()))
            data = self.shap_explainer.compute_and_cache_global_explanation(dummy_matrix, sample_size=50)
            return GlobalExplanationResponse(**data)

        raise RuntimeError("SHAP explainer not available to generate global explanation.")
