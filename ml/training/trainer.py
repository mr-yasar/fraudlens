"""Fraud Detection Model Training, Ensemble Stacking, and Imbalance-Aware Engine."""

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import joblib
import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import RandomForestClassifier, VotingClassifier, HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    average_precision_score,
    confusion_matrix,
)
from sklearn.model_selection import train_test_split
from xgboost import XGBClassifier

from ml.preprocessing.pipeline import FullFraudPreprocessor


@dataclass
class TrainingConfig:
    """Training hyperparameter and split configuration."""

    target_column: str = "Fraud_Label"
    test_size: float = 0.15
    val_size: float = 0.15
    random_state: int = 42
    artifact_dir: str = "ml/artifacts"
    model_version: str = "v1.2.0"
    lr_max_iter: int = 1500
    lr_C: float = 1.0
    rf_n_estimators: int = 300
    rf_max_depth: int = 12
    rf_min_samples_split: int = 3
    rf_min_samples_leaf: int = 1
    xgb_n_estimators: int = 250
    xgb_max_depth: int = 5
    xgb_learning_rate: float = 0.035
    xgb_min_child_weight: int = 2
    xgb_gamma: float = 0.10
    xgb_subsample: float = 0.85
    xgb_colsample_bytree: float = 0.85
    xgb_reg_alpha: float = 0.1
    xgb_reg_lambda: float = 1.0


class FraudModelTrainer:
    """Engine for training, evaluating, ensemble stacking, and serializing fraud detection ML models."""

    def __init__(self, config: Optional[TrainingConfig] = None) -> None:
        self.config = config or TrainingConfig()
        self.preprocessor = FullFraudPreprocessor()
        self.models: Dict[str, Any] = {}
        self.evaluations: Dict[str, Any] = {}
        self.training_metadata: Dict[str, Any] = {}

    def prepare_data_splits(
        self, df: pd.DataFrame
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, Dict[str, Any]]:
        """Stratified 70/15/15 Train/Validation/Test split and feature preprocessing."""
        target_col = self.config.target_column
        if target_col not in df.columns:
            if "Fraud_Label" in df.columns:
                target_col = "Fraud_Label"
            elif "risk_label" in df.columns:
                target_col = "risk_label"
            elif "is_fraud" in df.columns:
                target_col = "is_fraud"
            else:
                raise ValueError(f"Target column '{target_col}' not found in dataset.")

        X = df.drop(columns=[target_col])
        y = df[target_col].values.astype(int)

        # 1. Stratified split into Train+Val (85%) and Test (15%)
        X_train_val, X_test, y_train_val, y_test = train_test_split(
            X,
            y,
            test_size=self.config.test_size,
            random_state=self.config.random_state,
            stratify=y,
        )

        # 2. Stratified split into Train (70%) and Val (15%)
        val_ratio_relative = self.config.val_size / (1.0 - self.config.test_size)
        X_train, X_val, y_train, y_val = train_test_split(
            X_train_val,
            y_train_val,
            test_size=val_ratio_relative,
            random_state=self.config.random_state,
            stratify=y_train_val,
        )

        # 3. Fit preprocessor ONLY on X_train to prevent data leakage
        X_train_mat = self.preprocessor.fit_transform(X_train)
        X_val_mat = self.preprocessor.transform(X_val)
        X_test_mat = self.preprocessor.transform(X_test)

        split_info = {
            "total_samples": len(df),
            "train_samples": len(X_train),
            "val_samples": len(X_val),
            "test_samples": len(X_test),
            "train_fraud_rate": round(float(np.mean(y_train)) * 100, 3),
            "val_fraud_rate": round(float(np.mean(y_val)) * 100, 3),
            "test_fraud_rate": round(float(np.mean(y_test)) * 100, 3),
            "feature_dimension": X_train_mat.shape[1],
        }

        return X_train_mat, y_train, X_val_mat, y_val, X_test_mat, y_test, split_info

    def train_all_models(self, X_train: np.ndarray, y_train: np.ndarray) -> Dict[str, Any]:
        """Train tuned Logistic Regression, Random Forest, XGBoost, and Stacking Ensemble."""
        # Calculate positive class imbalance weight for XGBoost
        n_neg = int(np.sum(y_train == 0))
        n_pos = int(np.sum(y_train == 1))
        scale_pos_weight = float(n_neg / max(1, n_pos))

        # 1. Regularized Logistic Regression with Balanced Class Weights
        lr = LogisticRegression(
            C=self.config.lr_C,
            class_weight="balanced",
            max_iter=self.config.lr_max_iter,
            random_state=self.config.random_state,
            solver="lbfgs",
        )
        lr.fit(X_train, y_train)
        self.models["logistic_regression"] = lr

        # 2. Tuned Random Forest Classifier
        rf = RandomForestClassifier(
            n_estimators=self.config.rf_n_estimators,
            max_depth=self.config.rf_max_depth,
            min_samples_split=self.config.rf_min_samples_split,
            min_samples_leaf=self.config.rf_min_samples_leaf,
            class_weight="balanced_subsample",
            random_state=self.config.random_state,
            n_jobs=-1,
        )
        rf.fit(X_train, y_train)
        self.models["random_forest"] = rf

        # 3. Tuned High-Performance XGBoost with Regularization
        xgb = XGBClassifier(
            n_estimators=self.config.xgb_n_estimators,
            max_depth=self.config.xgb_max_depth,
            learning_rate=self.config.xgb_learning_rate,
            min_child_weight=self.config.xgb_min_child_weight,
            gamma=self.config.xgb_gamma,
            subsample=self.config.xgb_subsample,
            colsample_bytree=self.config.xgb_colsample_bytree,
            reg_alpha=self.config.xgb_reg_alpha,
            reg_lambda=self.config.xgb_reg_lambda,
            scale_pos_weight=scale_pos_weight,
            eval_metric="logloss",
            random_state=self.config.random_state,
        )
        xgb.fit(X_train, y_train)
        self.models["xgboost"] = xgb

        # 4. Expert Stacking / Soft-Voting Ensemble (XGBoost 45% + Random Forest 40% + Logistic Regression 15%)
        ensemble = VotingClassifier(
            estimators=[
                ("xgb", xgb),
                ("rf", rf),
                ("lr", lr),
            ],
            voting="soft",
            weights=[0.45, 0.40, 0.15],
            n_jobs=-1,
        )
        ensemble.fit(X_train, y_train)
        self.models["ensemble_stacking"] = ensemble

        return self.models

    def evaluate_model(
        self, model: Any, X_eval: np.ndarray, y_eval: np.ndarray, model_name: str
    ) -> Dict[str, Any]:
        """Compute comprehensive evaluation metrics on test/validation set."""
        y_pred = model.predict(X_eval)

        # Continuous fraud probabilities
        if hasattr(model, "predict_proba"):
            y_prob = model.predict_proba(X_eval)[:, 1]
        elif hasattr(model, "decision_function"):
            decision = model.decision_function(X_eval)
            y_prob = 1.0 / (1.0 + np.exp(-decision))
        else:
            y_prob = y_pred.astype(float)

        acc = float(accuracy_score(y_eval, y_pred))
        prec = float(precision_score(y_eval, y_pred, zero_division=0))
        rec = float(recall_score(y_eval, y_pred, zero_division=0))
        f1 = float(f1_score(y_eval, y_pred, zero_division=0))

        try:
            roc_auc = float(roc_auc_score(y_eval, y_prob))
        except Exception:
            roc_auc = 0.5

        try:
            pr_auc = float(average_precision_score(y_eval, y_prob))
        except Exception:
            pr_auc = float(np.mean(y_eval))

        cm = confusion_matrix(y_eval, y_pred, labels=[0, 1])
        tn, fp, fn, tp = int(cm[0, 0]), int(cm[0, 1]), int(cm[1, 0]), int(cm[1, 1])

        fpr = float(fp / (fp + tn)) if (fp + tn) > 0 else 0.0
        fnr = float(fn / (fn + tp)) if (fn + tp) > 0 else 0.0

        return {
            "model_name": model_name,
            "accuracy": round(acc, 4),
            "precision": round(prec, 4),
            "recall": round(rec, 4),
            "f1_score": round(f1, 4),
            "roc_auc": round(roc_auc, 4),
            "pr_auc": round(pr_auc, 4),
            "false_positive_rate": round(fpr, 4),
            "false_negative_rate": round(fnr, 4),
            "confusion_matrix": {
                "true_negatives": tn,
                "false_positives": fp,
                "false_negatives": fn,
                "true_positives": tp,
            },
        }

    def run_pipeline(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Execute full end-to-end training and evaluation pipeline."""
        X_train, y_train, X_val, y_val, X_test, y_test, split_info = self.prepare_data_splits(df)

        # Train models
        self.train_all_models(X_train, y_train)

        # Evaluate all models on both validation and test sets
        test_evaluations: Dict[str, Any] = {}
        val_evaluations: Dict[str, Any] = {}

        for name, model in self.models.items():
            test_evaluations[name] = self.evaluate_model(model, X_test, y_test, name)
            val_evaluations[name] = self.evaluate_model(model, X_val, y_val, name)

        self.evaluations = {
            "test_metrics": test_evaluations,
            "validation_metrics": val_evaluations,
            "data_splits": split_info,
        }

        self.training_metadata = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "model_version": self.config.model_version,
            "random_state": self.config.random_state,
            "models_trained": list(self.models.keys()),
            "config": asdict(self.config),
            "splits": split_info,
        }

        # Save artifacts
        self.save_artifacts()

        return {
            "evaluations": self.evaluations,
            "metadata": self.training_metadata,
        }

    def save_artifacts(self) -> None:
        """Save all model artifacts, preprocessor, and metadata to disk."""
        artifact_path = Path(self.config.artifact_dir)
        artifact_path.mkdir(parents=True, exist_ok=True)

        # 1. Save Preprocessor & Feature Metadata
        self.preprocessor.save(artifact_path / "preprocessor.joblib")
        with open(artifact_path / "feature_metadata.json", "w", encoding="utf-8") as f:
            json.dump(self.preprocessor.get_metadata(), f, indent=2)

        # 2. Save Trained Models
        for name, model in self.models.items():
            joblib.dump(model, artifact_path / f"{name}.joblib")

        # 3. Save Evaluation Results
        with open(artifact_path / "evaluation_results.json", "w", encoding="utf-8") as f:
            json.dump(self.evaluations, f, indent=2)

        # 4. Save Training Metadata
        with open(artifact_path / "training_metadata.json", "w", encoding="utf-8") as f:
            json.dump(self.training_metadata, f, indent=2)

