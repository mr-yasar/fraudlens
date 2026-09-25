"""Prediction and Explainability Service Layer."""

from dataclasses import asdict
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
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
from ml.anomaly.isolation_forest_service import AnomalyIntelligenceService
from ml.evaluation.uncertainty_service import UncertaintyEstimationService
from ml.explainability.counterfactual_engine import CounterfactualEngine
from backend.app.services.explanation_composer import ExplanationComposer


class FraudPredictionService:
    """Singleton service for real-time fraud scoring, multi-factor risk evaluation, and SHAP attribution."""

    _instance: Optional["FraudPredictionService"] = None

    def __init__(self, artifact_dir: Union[str, Path] = "ml/artifacts") -> None:
        self.artifact_dir = Path(artifact_dir)
        self.preprocessor: Optional[FullFraudPreprocessor] = None
        self.model: Optional[Any] = None
        self.candidate_models: Dict[str, Any] = {}
        self.metadata: Dict[str, Any] = {}
        self.registry: Dict[str, Any] = {}
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
        """Load preprocessor, active model binary, candidate models, threshold metadata, and initialize SHAP explainer."""
        meta_file = self.artifact_dir / "active_model_metadata.json"
        preprocessor_file = self.artifact_dir / "preprocessor.joblib"
        registry_file = self.artifact_dir / "model_registry.json"

        if not meta_file.exists() or not preprocessor_file.exists():
            self.is_ready = False
            return

        # 1. Load active metadata & registry
        with open(meta_file, "r", encoding="utf-8") as f:
            self.metadata = json.load(f)

        if registry_file.exists():
            try:
                with open(registry_file, "r", encoding="utf-8") as f:
                    self.registry = json.load(f)
            except Exception:
                self.registry = {}

        self.model_name = self.metadata.get("model_name", "xgboost")
        self.model_version = self.metadata.get("model_version", "v1.0.0")
        self.threshold = float(self.metadata.get("selected_threshold", 0.5))

        # 2. Load Preprocessor
        self.preprocessor = joblib.load(preprocessor_file)

        # 3. Load Active Model & Candidate Models
        model_file = self.artifact_dir / f"{self.model_name}.joblib"
        if not model_file.exists():
            raise FileNotFoundError(f"Active model binary not found at: {model_file}")

        self.model = joblib.load(model_file)
        self.candidate_models[self.model_name] = self.model

        # Pre-cache other candidates if available on disk (logistic_regression, random_forest, xgboost, ensemble_stacking)
        for cand_name in ["logistic_regression", "random_forest", "xgboost", "ensemble_stacking"]:
            if cand_name not in self.candidate_models:
                cand_path = self.artifact_dir / f"{cand_name}.joblib"
                if cand_path.exists():
                    try:
                        self.candidate_models[cand_name] = joblib.load(cand_path)
                    except Exception:
                        pass

        # 4. Initialize SHAP Explainer
        feature_names = self.preprocessor.get_feature_names_out()
        try:
            self.shap_explainer = FraudShapExplainer(
                model=self.model,
                feature_names=feature_names,
                model_name=self.model_name,
                model_version=self.model_version,
                artifact_dir=str(self.artifact_dir),
            )
        except Exception:
            self.shap_explainer = None

        self.is_ready = True

    def get_candidate_model(self, name: str) -> Optional[Any]:
        """Retrieve candidate model from cache or load from artifact directory."""
        clean_name = name.lower().strip()
        if clean_name in self.candidate_models:
            return self.candidate_models[clean_name]
        cand_path = self.artifact_dir / f"{clean_name}.joblib"
        if cand_path.exists():
            try:
                mod = joblib.load(cand_path)
                self.candidate_models[clean_name] = mod
                return mod
            except Exception:
                return None
        return None

    def _prepare_row_df(self, raw_dict: Dict[str, Any]) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """Ensure input payload has all primary dataset features and canonical fields normalized."""
        d = dict(raw_dict)
        amt_val = d.get("amount") if d.get("amount") is not None else (d.get("Amount") if d.get("Amount") is not None else d.get("transaction_amount"))
        amt = float(amt_val if amt_val is not None else 100.0)
        d["amount"] = amt
        d["Amount"] = amt
        d["transaction_amount"] = amt

        # Determine realistic baseline average amount (DO NOT default to current transaction amt!)
        merch_avg = float(d.get("merchant_average_ticket") or 1500.0)
        baseline = (
            d.get("customer_historical_avg_amount")
            or d.get("Average_Previous_Amount")
            or d.get("avg_transaction_amount_30d_customer")
            or merch_avg
        )
        try:
            avg_amt = float(baseline)
            if avg_amt <= 0:
                avg_amt = merch_avg
        except Exception:
            avg_amt = merch_avg

        d["customer_historical_avg_amount"] = avg_amt
        d["Average_Previous_Amount"] = avg_amt
        d["avg_transaction_amount_30d_customer"] = avg_amt

        max_amt_val = d.get("customer_historical_max_amount")
        max_amt = float(max_amt_val if max_amt_val is not None else (avg_amt * 2.5))
        d["customer_historical_max_amount"] = max_amt

        prior_tx_val = d.get("customer_total_transactions_prior")
        prior_tx = int(prior_tx_val if prior_tx_val is not None else 25)
        d["customer_total_transactions_prior"] = prior_tx

        prev_amt_val = d.get("Previous_Transaction_Amount")
        prev_amt = float(prev_amt_val if prev_amt_val is not None else avg_amt)
        d["Previous_Transaction_Amount"] = prev_amt

        amt_ratio = float(amt / (avg_amt + 1e-5))
        d["amount_to_avg_ratio"] = amt_ratio
        d["Amount_Ratio"] = amt_ratio
        d["Amount_Deviation"] = float(amt - avg_amt)
        d["amount_deviation_zscore"] = float((amt - avg_amt) / (avg_amt * 0.4 + 1e-5))

        tx_type = str(d.get("transaction_type") or d.get("Transaction_Type") or "Purchase")
        d["transaction_type"] = tx_type
        d["Transaction_Type"] = tx_type

        tx_hour_val = d.get("transaction_hour") if d.get("transaction_hour") is not None else d.get("Transaction_Hour")
        tx_hour = int(tx_hour_val if tx_hour_val is not None else 12)
        d["transaction_hour"] = tx_hour
        d["Transaction_Hour"] = tx_hour
        d["is_night_transaction"] = int(1 if (tx_hour >= 23 or tx_hour <= 5) else 0)

        dow_val = d.get("day_of_week") if d.get("day_of_week") is not None else d.get("transaction_day_of_week")
        dow = int(dow_val if dow_val is not None else 2)
        d["day_of_week"] = dow
        d["transaction_day_of_week"] = dow
        d["is_weekend"] = int(d.get("is_weekend") if d.get("is_weekend") is not None else (1 if dow >= 5 else 0))

        loc = str(d.get("location") or d.get("Location") or d.get("geo_location_region") or "Chennai")
        d["location"] = loc
        d["Location"] = loc
        d["geo_location_region"] = loc
        d["Usual_Location"] = str(d.get("Usual_Location") or loc)

        loc_dist_val = d.get("location_distance_km") if d.get("location_distance_km") is not None else d.get("location_distance")
        loc_dist = float(loc_dist_val if loc_dist_val is not None else 0.0)
        is_loc_changed = int(1 if (d.get("is_location_changed") is True or d.get("is_location_changed") == 1 or loc_dist > 50) else 0)
        d["location_distance_km"] = loc_dist
        d["is_location_changed"] = is_loc_changed
        d["Unusual_Location"] = is_loc_changed

        dev = str(d.get("device_type") or d.get("Device_Type") or "mobile_android")
        d["device_type"] = dev
        d["Device_Type"] = dev

        new_dev = int(1 if (d.get("is_new_device") is True or d.get("is_new_device") == 1 or d.get("New_Device") == 1) else 0)
        d["is_new_device"] = new_dev
        d["New_Device"] = new_dev
        d["is_trusted_device"] = int(1 if new_dev == 0 else 0)

        new_ben = int(1 if (d.get("is_new_beneficiary") is True or d.get("is_new_beneficiary") == 1) else 0)
        d["is_new_beneficiary"] = new_ben
        d["beneficiary_prior_tx_count"] = int(d.get("beneficiary_prior_tx_count") if d.get("beneficiary_prior_tx_count") is not None else (0 if new_ben else 5))

        acc_val = d.get("customer_account_age_days") if d.get("customer_account_age_days") is not None else (d.get("Account_Age_Days") if d.get("Account_Age_Days") is not None else (d.get("account_age_days") or 365.0))
        acc_age = float(acc_val)
        d["customer_account_age_days"] = acc_age
        d["Account_Age_Days"] = acc_age
        d["account_age_days"] = acc_age

        vel_1 = int(float(d.get("transactions_last_1h") if d.get("transactions_last_1h") is not None else (d.get("transaction_velocity_1h") or 0)))
        vel_24 = int(float(d.get("transactions_last_24h") if d.get("transactions_last_24h") is not None else (d.get("Transactions_Last_24H") if d.get("Transactions_Last_24H") is not None else (d.get("transaction_velocity_24h") or max(vel_1, 2)))))
        vel_7 = int(d.get("transactions_last_7d") or (vel_24 * 4))
        d["transactions_last_1h"] = vel_1
        d["transactions_last_24h"] = vel_24
        d["transactions_last_7d"] = vel_7
        d["Transactions_Last_24H"] = vel_24
        d["Velocity_1h"] = vel_1
        d["Velocity_24h"] = vel_24
        d["transaction_velocity_1h"] = vel_1
        d["transaction_velocity_24h"] = vel_24
        d["customer_total_transactions_30d"] = int(d.get("customer_total_transactions_30d") or (vel_7 * 4) or 30)

        prev_cb = int(d.get("previous_chargebacks") if d.get("previous_chargebacks") is not None else (d.get("Previous_Chargebacks") or 0))
        d["previous_chargebacks"] = prev_cb
        d["Previous_Chargebacks"] = prev_cb
        cb_rate = float(d.get("chargeback_rate_30d") if d.get("chargeback_rate_30d") is not None else (prev_cb / max(1, d["customer_total_transactions_30d"])))
        d["chargeback_rate_30d"] = cb_rate

        tx_country = str(d.get("transaction_country") or d.get("Transaction_Country") or "IN")
        d["transaction_country"] = tx_country
        d["Transaction_Country"] = tx_country

        is_intl = int(1 if (d.get("is_international") is True or d.get("is_international") == 1 or d.get("Is_International") == 1 or d.get("International_Transaction") == 1 or tx_country.upper() not in ["IN", "INDIA"]) else 0)
        d["is_international"] = is_intl
        d["Is_International"] = is_intl
        d["International_Transaction"] = is_intl

        fails = int(d.get("failed_transaction_attempts_24h") if d.get("failed_transaction_attempts_24h") is not None else (d.get("failed_login_attempts_24h") if d.get("failed_login_attempts_24h") is not None else (d.get("Failed_Attempts") if d.get("Failed_Attempts") is not None else 0)))
        d["failed_login_attempts_24h"] = fails
        d["failed_transaction_attempts_24h"] = fails
        d["Failed_Attempts"] = fails
        d["recent_password_change"] = int(d.get("recent_password_change") or 0)

        # Merchant characteristics
        merch_cat = str(d.get("merchant_category") or "retail")
        d["merchant_category"] = merch_cat
        is_hr_cat = int(1 if (d.get("is_high_risk_merchant_category") is True or d.get("is_high_risk_merchant_category") == 1 or merch_cat.lower() in ["crypto", "gambling", "electronics", "money_transfer", "jewelry", "liquor"]) else 0)
        d["is_high_risk_merchant_category"] = is_hr_cat

        d["merchant_average_ticket"] = merch_avg
        d["merchant_business_age_years"] = int(d.get("merchant_business_age_years") or 5)
        d["merchant_payment_channels"] = str(d.get("merchant_payment_channels") or "UPI,CARD,POS")
        d["merchant_historical_fraud_rate"] = float(d.get("merchant_historical_fraud_rate") if d.get("merchant_historical_fraud_rate") is not None else 0.02)

        return pd.DataFrame([d]), d

    def predict_transaction(
        self,
        input_data: TransactionPredictionInput,
        model_override: Optional[str] = None,
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

        # Select model to use
        effective_model_name = (model_override or self.model_name).lower().strip()
        effective_model = self.get_candidate_model(effective_model_name) or self.model
        if effective_model is None:
            effective_model = self.model
            effective_model_name = self.model_name

        raw_dict = input_data.model_dump()
        df_row, enriched_dict = self._prepare_row_df(raw_dict)

        # 1. Preprocess using saved pipeline
        transformed_mat = self.preprocessor.transform(df_row)

        # 2. Compute Model Fraud Probability
        if hasattr(effective_model, "predict_proba"):
            probs = effective_model.predict_proba(transformed_mat)[:, 1]
            raw_prob = float(probs[0])
        elif hasattr(effective_model, "decision_function"):
            decision = effective_model.decision_function(transformed_mat)
            raw_prob = float(1.0 / (1.0 + np.exp(-decision[0])))
        else:
            raw_prob = float(effective_model.predict(transformed_mat)[0])
        prob = max(0.0, min(1.0, raw_prob))

        # 3. Compute Holistic Risk Score (0-100) & Risk Level (LOW, MEDIUM, HIGH)
        risk_result = self.risk_engine.compute_risk_score(
            fraud_probability=prob,
            transaction_data=enriched_dict,
        )

        # 4. Calibrate reported probability with multi-factor risk consensus
        if risk_result.risk_level.value == "HIGH":
            prob = max(prob, min(0.965, float(risk_result.risk_score) / 100.0))
        elif risk_result.risk_level.value == "LOW":
            prob = min(prob, max(0.015, float(risk_result.risk_score) / 100.0))

        # 5. Apply Decision Threshold
        applied_threshold = threshold_override if threshold_override is not None else self.threshold
        prediction_label = "FRAUD" if (prob >= applied_threshold or risk_result.risk_level.value == "HIGH") else "GENUINE"

        # 5. Compute SHAP Top Factors (if requested)
        top_shap_factors: Optional[List[Dict[str, Any]]] = None
        top_factors: Optional[List[Dict[str, Any]]] = None
        if include_shap_summary and self.shap_explainer is not None:
            try:
                local_exp = self.shap_explainer.explain_local(transformed_mat, fraud_prob=prob, top_k=3)
                top_shap_factors = [
                    {
                        "factor": f.feature_name.replace("_", " ").title(),
                        "feature_name": f.feature_name,
                        "shap_value": f.shap_value,
                        "contribution": f.shap_value,
                        "impact": f.impact,
                        "direction": "RISK_INCREASING" if f.shap_value > 0 else "RISK_REDUCING",
                        "detail": f.detail,
                    }
                    for f in local_exp.top_risk_increasing_factors + local_exp.top_risk_decreasing_factors
                ][:5]
                top_factors = top_shap_factors
            except Exception:
                top_shap_factors = None

        if not top_factors and risk_result.risk_factors:
            top_factors = [
                {
                    "factor": rf.factor,
                    "feature_name": rf.factor,
                    "contribution": rf.impact_score / 100.0,
                    "direction": "RISK_INCREASING" if rf.impact_score > 0 else "RISK_REDUCING",
                    "impact": "INCREASE_RISK" if rf.impact_score > 0 else "DECREASE_RISK",
                    "detail": rf.detail,
                }
                for rf in risk_result.risk_factors[:5]
            ]

        # Operational recommended action based on risk level
        rec_action = (
            "BLOCK / INVESTIGATE"
            if risk_result.risk_level.value == "HIGH"
            else ("REVIEW / STEP-UP VERIFICATION" if risk_result.risk_level.value == "MEDIUM" else "ALLOW / PROCEED")
        )

        # 6. Unsupervised Anomaly Scoring (Isolation Forest)
        anomaly_score = None
        anomaly_status = "UNAVAILABLE"
        anomaly_res = None
        try:
            anom_service = AnomalyIntelligenceService.get_instance(artifact_dir=str(self.artifact_dir))
            if anom_service.is_ready:
                anomaly_res = anom_service.score_vector(transformed_mat[0])
                anomaly_score = anomaly_res.anomaly_score
                anomaly_status = anomaly_res.anomaly_status
        except Exception:
            anomaly_status = "UNAVAILABLE"

        # 7. Model Prediction Uncertainty Estimation
        uncertainty_score = None
        uncertainty_level = "LOW"
        uncertainty_res = None
        try:
            uncertainty_res = UncertaintyEstimationService.evaluate_uncertainty(
                probabilities={effective_model_name: prob},
                active_probability=prob,
                threshold=applied_threshold,
            )
            uncertainty_score = uncertainty_res.uncertainty_score
            uncertainty_level = uncertainty_res.uncertainty_level
        except Exception:
            uncertainty_score = None

        # 8. Counterfactual Scenario Perturbation
        counterfactual_dict = None
        cf_res = None
        try:
            decision_tier = "BLOCK" if risk_result.risk_level.value == "HIGH" else ("REVIEW" if risk_result.risk_level.value == "MEDIUM" else "ALLOW")
            cf_res = CounterfactualEngine.generate_counterfactual(
                raw_payload=enriched_dict,
                preprocessor=self.preprocessor,
                model=effective_model,
                risk_engine=self.risk_engine,
                original_prob=prob,
                original_risk=float(risk_result.risk_score),
                original_decision=decision_tier,
                threshold=applied_threshold,
            )
            counterfactual_dict = cf_res.to_dict()
        except Exception:
            counterfactual_dict = None

        # 9. Evidence-Grounded Explanation Narrative
        composed_explanation_dict = None
        try:
            composed = ExplanationComposer.compose_explanation(
                decision="FRAUD (BLOCK)" if prediction_label == "FRAUD" else "GENUINE (ALLOW)",
                risk_score=float(risk_result.risk_score),
                fraud_probability=prob,
                model_version=f"{effective_model_name} {self.model_version}",
                shap_factors=None,
                counterfactual=cf_res,
                anomaly=anomaly_res,
                uncertainty=uncertainty_res,
                behavior_deviation=float(enriched_dict.get("Amount_Deviation", 0.0)),
            )
            composed_explanation_dict = composed.to_dict()
        except Exception:
            composed_explanation_dict = None

        return PredictionResponse(
            prediction=prediction_label,
            fraud_probability=round(prob, 4),
            risk_score=risk_result.risk_score,
            risk_level=risk_result.risk_level.value,
            recommended_action=rec_action,
            model_name=effective_model_name,
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
            top_factors=top_factors,
            anomaly_score=anomaly_score,
            anomaly_status=anomaly_status,
            uncertainty_score=uncertainty_score,
            uncertainty_level=uncertainty_level,
            counterfactual=counterfactual_dict,
            composed_explanation=composed_explanation_dict,
        )

    def explain_transaction(
        self,
        input_data: TransactionPredictionInput,
        top_k: int = 5,
        model_override: Optional[str] = None,
    ) -> LocalExplanationResponse:
        """Compute full local feature-by-feature SHAP attribution report for a single transaction with multi-model intelligence."""
        if not self.is_ready or self.shap_explainer is None or self.preprocessor is None:
            self._load_artifacts()
            if not self.is_ready or self.shap_explainer is None or self.preprocessor is None:
                raise RuntimeError("FraudPredictionService is not ready. Missing model or SHAP explainer artifacts.")

        effective_model_name = (model_override or self.model_name).lower().strip()
        effective_model = self.get_candidate_model(effective_model_name) or self.model
        if effective_model is None:
            effective_model = self.model
            effective_model_name = self.model_name

        raw_dict = input_data.model_dump()
        df_row, enriched_dict = self._prepare_row_df(raw_dict)
        transformed_mat = self.preprocessor.transform(df_row)

        # Get probability from effective model
        if hasattr(effective_model, "predict_proba"):
            probs = effective_model.predict_proba(transformed_mat)[:, 1]
            prob = float(probs[0])
        elif hasattr(effective_model, "decision_function"):
            decision = effective_model.decision_function(transformed_mat)
            prob = float(1.0 / (1.0 + np.exp(-decision[0])))
        else:
            prob = 0.5
        prob = max(0.0, min(1.0, prob))

        risk_result = self.risk_engine.compute_risk_score(fraud_probability=prob, transaction_data=enriched_dict)
        prediction_label = "FRAUD" if prob >= self.threshold else "GENUINE"

        # Explain with model-specific explainer if available, else active explainer
        explainer_to_use = self.shap_explainer
        if effective_model != self.model:
            try:
                feature_names = self.preprocessor.get_feature_names_out()
                explainer_to_use = FraudShapExplainer(
                    model=effective_model,
                    feature_names=feature_names,
                    model_name=effective_model_name,
                    model_version=self.model_version,
                    artifact_dir=str(self.artifact_dir),
                )
            except Exception:
                explainer_to_use = self.shap_explainer

        local_exp = explainer_to_use.explain_local(transformed_mat, fraud_prob=prob, top_k=top_k)

        # Multi-model inference comparison across all 4 models
        model_comparison = None
        try:
            model_comparison = self.compare_all_models(input_data)
        except Exception:
            model_comparison = None

        # Counterfactual scenario perturbation
        counterfactual_dict = None
        cf_res = None
        try:
            decision_tier = "BLOCK" if risk_result.risk_level.value == "HIGH" else ("REVIEW" if risk_result.risk_level.value == "MEDIUM" else "ALLOW")
            cf_res = CounterfactualEngine.generate_counterfactual(
                raw_payload=enriched_dict,
                preprocessor=self.preprocessor,
                model=effective_model,
                risk_engine=self.risk_engine,
                original_prob=prob,
                original_risk=float(risk_result.risk_score),
                original_decision=decision_tier,
                threshold=self.threshold,
            )
            counterfactual_dict = cf_res.to_dict()
        except Exception:
            counterfactual_dict = None

        # Unsupervised Anomaly Scoring (Isolation Forest)
        anomaly_score = None
        anomaly_status = "UNAVAILABLE"
        anomaly_res = None
        try:
            anom_service = AnomalyIntelligenceService.get_instance(artifact_dir=str(self.artifact_dir))
            if anom_service.is_ready:
                anomaly_res = anom_service.score_vector(transformed_mat[0])
                anomaly_score = anomaly_res.anomaly_score
                anomaly_status = anomaly_res.anomaly_status
        except Exception:
            anomaly_status = "UNAVAILABLE"

        # Model Prediction Uncertainty
        uncertainty_score = None
        uncertainty_level = "LOW"
        uncertainty_res = None
        try:
            uncertainty_res = UncertaintyEstimationService.evaluate_uncertainty(
                probabilities={effective_model_name: prob},
                active_probability=prob,
                threshold=self.threshold,
            )
            uncertainty_score = uncertainty_res.uncertainty_score
            uncertainty_level = uncertainty_res.uncertainty_level
        except Exception:
            uncertainty_score = None

        # Composed Forensic Narrative
        composed_explanation_dict = None
        try:
            composed = ExplanationComposer.compose_explanation(
                decision="FRAUD (BLOCK)" if prediction_label == "FRAUD" else "GENUINE (ALLOW)",
                risk_score=float(risk_result.risk_score),
                fraud_probability=prob,
                model_version=f"{effective_model_name} {self.model_version}",
                shap_factors=None,
                counterfactual=cf_res,
                anomaly=anomaly_res,
                uncertainty=uncertainty_res,
                behavior_deviation=float(enriched_dict.get("Amount_Deviation", 0.0)),
            )
            composed_explanation_dict = composed.to_dict()
        except Exception:
            composed_explanation_dict = None

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
            model_name=effective_model_name,
            model_version=self.model_version,
            model_comparison=model_comparison,
            composed_explanation=composed_explanation_dict,
            counterfactual=counterfactual_dict,
            anomaly_score=anomaly_score,
            anomaly_status=anomaly_status,
            uncertainty_score=uncertainty_score,
            uncertainty_level=uncertainty_level,
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

    def compare_all_models(
        self,
        input_data: TransactionPredictionInput,
    ) -> Dict[str, Any]:
        """Execute inference simultaneously across all loaded candidate models for comparison."""
        results: Dict[str, Any] = {}
        for name in ["logistic_regression", "random_forest", "xgboost", "ensemble_stacking"]:
            try:
                cand_model = self.get_candidate_model(name)
                if cand_model is not None:
                    pred_res = self.predict_transaction(
                        input_data=input_data,
                        model_override=name,
                        include_shap_summary=False,
                    )
                    results[name] = {
                        "model_name": name,
                        "fraud_probability": pred_res.fraud_probability,
                        "prediction": pred_res.prediction,
                        "risk_score": pred_res.risk_score,
                        "risk_level": pred_res.risk_level,
                        "is_active": (name == self.model_name),
                    }
            except Exception as e:
                results[name] = {
                    "model_name": name,
                    "error": str(e),
                    "is_active": (name == self.model_name),
                }

        return {
            "active_model": self.model_name,
            "active_version": self.model_version,
            "threshold": self.threshold,
            "model_predictions": results,
        }

    def get_model_status(self) -> Dict[str, Any]:
        """Retrieve runtime health and active metadata status."""
        return {
            "is_ready": self.is_ready,
            "active_model": self.model_name,
            "active_version": self.model_version,
            "threshold": self.threshold,
            "loaded_candidate_models": list(self.candidate_models.keys()),
            "preprocessor_fitted": hasattr(self.preprocessor, "transformers_") if self.preprocessor else False,
            "shap_available": self.shap_explainer is not None,
            "output_features_count": len(self.preprocessor.get_feature_names_out()) if (self.preprocessor and hasattr(self.preprocessor, "transformers_")) else 0,
        }

