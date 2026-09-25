"""Explainable AI Engine using SHAP (SHapley Additive exPlanations)."""

from dataclasses import dataclass, asdict
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import joblib
import numpy as np
import pandas as pd
import shap
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, VotingClassifier
from xgboost import XGBClassifier

from ml.preprocessing.pipeline import FullFraudPreprocessor
from ml.explainability.feature_metadata import (
    get_feature_display_name,
    format_customer_reason,
    format_investigator_reason,
)


@dataclass
class FeatureAttribution:
    """Detailed attribution of an individual feature's contribution to prediction."""

    feature_name: str
    feature_value: float
    shap_value: float
    impact: str  # 'INCREASES_FRAUD_RISK' or 'DECREASES_FRAUD_RISK'
    importance_rank: int
    detail: str
    display_name: Optional[str] = None
    category: Optional[str] = None


@dataclass
class LocalExplanation:
    """Comprehensive local SHAP explanation for a single transaction scoring event."""

    base_value: float
    fraud_probability: float
    top_risk_increasing_factors: List[FeatureAttribution]
    top_risk_decreasing_factors: List[FeatureAttribution]
    all_attributions: List[FeatureAttribution]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "base_value": round(float(self.base_value), 4),
            "fraud_probability": round(float(self.fraud_probability), 4),
            "top_risk_increasing_factors": [asdict(f) for f in self.top_risk_increasing_factors],
            "top_risk_decreasing_factors": [asdict(f) for f in self.top_risk_decreasing_factors],
            "all_attributions": [asdict(f) for f in self.all_attributions],
        }


class FraudShapExplainer:
    """SHAP explanation engine supporting TreeExplainer and Linear/Kernel explainers."""

    def __init__(
        self,
        model: Any,
        feature_names: List[str],
        background_data: Optional[np.ndarray] = None,
        model_name: str = "active_model",
        model_version: str = "v1.0.0",
        artifact_dir: str = "ml/artifacts",
    ) -> None:
        self.model = model
        self.feature_names = feature_names
        self.background_data = background_data
        self.model_name = model_name
        self.model_version = model_version
        self.artifact_dir = Path(artifact_dir)

        self.explainer: Any = None
        self._init_explainer()

    def _init_explainer(self) -> None:
        """Initialize the model-specific SHAP explainer."""
        # 1. Voting / Stacking Ensemble Models
        if isinstance(self.model, VotingClassifier) or hasattr(self.model, "estimators_"):
            # Use TreeExplainer on the champion tree sub-estimator (XGBoost) for instantaneous TreeSHAP
            sub_estimator = None
            if hasattr(self.model, "named_estimators_") and "xgb" in self.model.named_estimators_:
                sub_estimator = self.model.named_estimators_["xgb"]
            elif hasattr(self.model, "estimators_") and len(self.model.estimators_) > 0:
                sub_estimator = self.model.estimators_[0]

            if sub_estimator is not None and (isinstance(sub_estimator, (XGBClassifier, RandomForestClassifier)) or hasattr(sub_estimator, "tree_")):
                try:
                    self.explainer = shap.TreeExplainer(sub_estimator)
                except Exception:
                    self.explainer = shap.Explainer(self.model.predict_proba, self.background_data[:50] if self.background_data is not None and len(self.background_data) > 0 else None)
            else:
                self.explainer = shap.Explainer(self.model.predict_proba, self.background_data[:50] if self.background_data is not None and len(self.background_data) > 0 else None)

        # 2. Tree-based Models (XGBoost, Random Forest)
        elif isinstance(self.model, (XGBClassifier, RandomForestClassifier)) or hasattr(self.model, "tree_"):
            try:
                self.explainer = shap.TreeExplainer(self.model)
            except Exception:
                # Fallback to general explainer if tree structure has edge cases
                if self.background_data is not None and len(self.background_data) > 0:
                    bg_sample = shap.sample(self.background_data, min(50, len(self.background_data)))
                    self.explainer = shap.Explainer(self.model.predict_proba, bg_sample)
                else:
                    self.explainer = shap.Explainer(self.model)

        # 3. Linear Models (Logistic Regression)
        elif isinstance(self.model, LogisticRegression):
            if self.background_data is not None and len(self.background_data) > 0:
                bg_sample = shap.sample(self.background_data, min(50, len(self.background_data)))
                self.explainer = shap.LinearExplainer(self.model, bg_sample)
            else:
                dummy_bg = np.zeros((1, len(self.feature_names)))
                self.explainer = shap.LinearExplainer(self.model, dummy_bg)

        # 4. Universal Model Explainer Fallback
        else:
            if self.background_data is not None and len(self.background_data) > 0:
                bg_sample = shap.sample(self.background_data, min(50, len(self.background_data)))
                self.explainer = shap.Explainer(self.model.predict_proba, bg_sample)
            else:
                self.explainer = shap.Explainer(self.model)

    def explain_local(
        self,
        X_matrix: np.ndarray,
        fraud_prob: float,
        top_k: int = 5,
    ) -> LocalExplanation:
        """Compute exact SHAP feature attributions for a single transaction vector."""
        if X_matrix.ndim == 1:
            X_matrix = X_matrix.reshape(1, -1)

        # Calculate SHAP values
        raw_shap = self.explainer(X_matrix)
        if hasattr(raw_shap, "values"):
            shap_vals = raw_shap.values[0]
            # If multi-output (probabilities for [0, 1]), pick class 1 (fraud)
            if shap_vals.ndim == 2 and shap_vals.shape[1] == 2:
                shap_vals = shap_vals[:, 1]
            elif shap_vals.ndim == 2:
                shap_vals = shap_vals[0]
        else:
            shap_vals = np.array(raw_shap)[0]

        # Extract base expected value
        base_val = 0.5
        if hasattr(raw_shap, "base_values"):
            bv = raw_shap.base_values[0]
            if isinstance(bv, (np.ndarray, list)) and len(bv) == 2:
                base_val = float(bv[1])
            else:
                base_val = float(bv)
        elif hasattr(self.explainer, "expected_value"):
            ev = self.explainer.expected_value
            if isinstance(ev, (np.ndarray, list)) and len(ev) == 2:
                base_val = float(ev[1])
            else:
                base_val = float(ev)

        # Map each feature to its attribution
        feature_vals = X_matrix[0]
        attributions: List[FeatureAttribution] = []

        for idx, s_val in enumerate(shap_vals):
            feat_name = self.feature_names[idx] if idx < len(self.feature_names) else f"feature_{idx}"
            feat_val = float(feature_vals[idx]) if idx < len(feature_vals) else 0.0
            s_float = float(s_val)

            impact = "INCREASES_FRAUD_RISK" if s_float > 0 else "DECREASES_FRAUD_RISK"
            disp_name = get_feature_display_name(feat_name)
            detail = (
                f"{feat_name} (value: {feat_val:.2f}) increased fraud risk by +{s_float:.4f}"
                if s_float > 0
                else f"{feat_name} (value: {feat_val:.2f}) decreased fraud risk by {s_float:.4f}"
            )

            attributions.append(
                FeatureAttribution(
                    feature_name=feat_name,
                    feature_value=round(feat_val, 4),
                    shap_value=round(s_float, 4),
                    impact=impact,
                    importance_rank=0,  # Assigned after sorting
                    detail=detail,
                    display_name=disp_name,
                )
            )

        # Rank all attributions by absolute magnitude |SHAP|
        attributions.sort(key=lambda x: abs(x.shap_value), reverse=True)
        for rank, attr in enumerate(attributions, 1):
            attr.importance_rank = rank

        # Extract top risk increasing and decreasing factors
        increasing = [a for a in attributions if a.shap_value > 0][:top_k]
        decreasing = [a for a in attributions if a.shap_value < 0][:top_k]

        return LocalExplanation(
            base_value=base_val,
            fraud_probability=fraud_prob,
            top_risk_increasing_factors=increasing,
            top_risk_decreasing_factors=decreasing,
            all_attributions=attributions,
        )

    def compute_and_cache_global_explanation(
        self,
        sample_matrix: np.ndarray,
        sample_size: int = 100,
    ) -> Dict[str, Any]:
        """Compute and persist mean absolute SHAP importance rankings across a background sample."""
        if len(sample_matrix) > sample_size:
            sample_matrix = shap.sample(sample_matrix, sample_size)

        raw_shap = self.explainer(sample_matrix)
        if hasattr(raw_shap, "values"):
            shap_matrix = raw_shap.values
            if shap_matrix.ndim == 3 and shap_matrix.shape[2] == 2:
                shap_matrix = shap_matrix[:, :, 1]
        else:
            shap_matrix = np.array(raw_shap)

        # Calculate mean absolute SHAP for each feature
        mean_abs_shap = np.mean(np.abs(shap_matrix), axis=0)
        mean_shap = np.mean(shap_matrix, axis=0)

        rankings: List[Dict[str, Any]] = []
        for idx, score in enumerate(mean_abs_shap):
            feat_name = self.feature_names[idx] if idx < len(self.feature_names) else f"feature_{idx}"
            rankings.append({
                "feature_name": feat_name,
                "mean_abs_shap": round(float(score), 4),
                "mean_shap": round(float(mean_shap[idx]), 4),
            })

        rankings.sort(key=lambda x: x["mean_abs_shap"], reverse=True)
        for rank, item in enumerate(rankings, 1):
            item["rank"] = rank

        global_report = {
            "model_name": self.model_name,
            "model_version": self.model_version,
            "sample_size": len(sample_matrix),
            "feature_importance_ranking": rankings,
        }

        # Cache to disk
        self.artifact_dir.mkdir(parents=True, exist_ok=True)
        with open(self.artifact_dir / "global_shap_explanation.json", "w", encoding="utf-8") as f:
            json.dump(global_report, f, indent=2)

        return global_report
