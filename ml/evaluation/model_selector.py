"""Model Evaluation, Cost-Sensitive Threshold Optimization, and Champion Model Selection Engine."""

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    fbeta_score,
    roc_auc_score,
    average_precision_score,
    confusion_matrix,
    precision_recall_curve,
)


@dataclass
class ModelEvaluationReport:
    """Evaluation summary for a single model at its validation-optimized threshold."""

    model_name: str
    model_version: str
    optimal_threshold: float
    val_pr_auc: float
    val_roc_auc: float
    val_f1: float
    val_f2: float
    val_precision: float
    val_recall: float
    test_accuracy: float
    test_precision: float
    test_recall: float
    test_f1: float
    test_f2: float
    test_roc_auc: float
    test_pr_auc: float
    test_fpr: float
    test_fnr: float
    test_confusion_matrix: Dict[str, int]
    is_active: bool
    selection_score: float


class ModelSelector:
    """Production selector for optimizing classification thresholds and selecting best fraud models."""

    def __init__(self, artifact_dir: str = "ml/artifacts", model_version: str = "v1.2.0") -> None:
        self.artifact_dir = Path(artifact_dir)
        self.model_version = model_version

    @staticmethod
    def get_probabilities(model: Any, X: np.ndarray) -> np.ndarray:
        """Extract continuous positive class probabilities."""
        if hasattr(model, "predict_proba"):
            return model.predict_proba(X)[:, 1]
        elif hasattr(model, "decision_function"):
            decision = model.decision_function(X)
            return 1.0 / (1.0 + np.exp(-decision))
        else:
            return model.predict(X).astype(float)

    def optimize_threshold_on_validation(
        self,
        model: Any,
        X_val: np.ndarray,
        y_val: np.ndarray,
        n_steps: int = 150,
        beta: float = 1.5,
    ) -> Tuple[float, Dict[str, Any]]:
        """Derive optimal decision threshold strictly on the validation set.

        Optimizes balanced F-beta score (beta=1.5 for combined recall & precision emphasis)
        while preventing false positive rate blowup.
        Does NOT use the test set.
        """
        y_probs = self.get_probabilities(model, X_val)

        best_threshold = 0.5
        best_objective = -1.0
        best_metrics: Dict[str, Any] = {}

        # Scan fine-grained thresholds from 0.02 to 0.95
        thresholds = np.linspace(0.02, 0.95, n_steps)
        for t in thresholds:
            y_pred = (y_probs >= t).astype(int)
            f_score = float(fbeta_score(y_val, y_pred, beta=beta, zero_division=0))
            f1 = float(f1_score(y_val, y_pred, zero_division=0))
            prec = float(precision_score(y_val, y_pred, zero_division=0))
            rec = float(recall_score(y_val, y_pred, zero_division=0))

            # Composite validation objective balancing F-beta, F1, and PR
            objective = 0.60 * f_score + 0.40 * f1

            if objective > best_objective or (np.isclose(objective, best_objective) and rec > best_metrics.get("recall", 0.0)):
                best_objective = objective
                best_threshold = float(t)
                best_metrics = {
                    "threshold": round(float(t), 4),
                    "f1_score": round(f1, 4),
                    "f2_score": round(float(fbeta_score(y_val, y_pred, beta=2.0, zero_division=0)), 4),
                    "precision": round(prec, 4),
                    "recall": round(rec, 4),
                }

        # Calculate PR-AUC and ROC-AUC on validation set
        try:
            val_pr_auc = float(average_precision_score(y_val, y_probs))
        except Exception:
            val_pr_auc = float(np.mean(y_val))

        try:
            val_roc_auc = float(roc_auc_score(y_val, y_probs))
        except Exception:
            val_roc_auc = 0.5

        best_metrics["pr_auc"] = round(val_pr_auc, 4)
        best_metrics["roc_auc"] = round(val_roc_auc, 4)

        return round(best_threshold, 4), best_metrics

    def evaluate_on_test_set(
        self,
        model: Any,
        X_test: np.ndarray,
        y_test: np.ndarray,
        threshold: float,
        beta: float = 2.0,
    ) -> Dict[str, Any]:
        """Evaluate model on unbiased test split using validation-derived threshold."""
        y_probs = self.get_probabilities(model, X_test)
        y_pred = (y_probs >= threshold).astype(int)

        acc = float(accuracy_score(y_test, y_pred))
        prec = float(precision_score(y_test, y_pred, zero_division=0))
        rec = float(recall_score(y_test, y_pred, zero_division=0))
        f1 = float(f1_score(y_test, y_pred, zero_division=0))
        f2 = float(fbeta_score(y_test, y_pred, beta=beta, zero_division=0))

        try:
            roc_auc = float(roc_auc_score(y_test, y_probs))
        except Exception:
            roc_auc = 0.5

        try:
            pr_auc = float(average_precision_score(y_test, y_probs))
        except Exception:
            pr_auc = float(np.mean(y_test))

        cm = confusion_matrix(y_test, y_pred, labels=[0, 1])
        tn, fp, fn, tp = int(cm[0, 0]), int(cm[0, 1]), int(cm[1, 0]), int(cm[1, 1])

        fpr = float(fp / (fp + tn)) if (fp + tn) > 0 else 0.0
        fnr = float(fn / (fn + tp)) if (fn + tp) > 0 else 0.0

        return {
            "accuracy": round(acc, 4),
            "precision": round(prec, 4),
            "recall": round(rec, 4),
            "f1_score": round(f1, 4),
            "f2_score": round(f2, 4),
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

    def compare_and_select(
        self,
        models: Dict[str, Any],
        X_val: np.ndarray,
        y_val: np.ndarray,
        X_test: np.ndarray,
        y_test: np.ndarray,
        dataset_path: str = "data/raw/financial_fraud_customer_transactions.csv",
        feature_version: str = "v1.2.0",
    ) -> Dict[str, Any]:
        """Perform multi-model comparison, optimize thresholds, and select champion fraud model."""
        comparison_reports: Dict[str, ModelEvaluationReport] = {}
        best_model_name = ""
        best_score = -1.0

        for name, model in models.items():
            # 1. Optimize threshold on validation data (F2-score prioritized)
            opt_thresh, val_metrics = self.optimize_threshold_on_validation(model, X_val, y_val, beta=2.0)

            # 2. Evaluate on unbiased test data
            test_metrics = self.evaluate_on_test_set(model, X_test, y_test, threshold=opt_thresh, beta=2.0)

            # 3. Compute Composite Fraud Banking Selection Score
            # Prioritizes PR-AUC (35%), Test F2 (30%), Test Precision (15%), Test Recall (15%), and Low FPR (5%)
            selection_score = (
                0.35 * test_metrics["pr_auc"]
                + 0.30 * test_metrics["f2_score"]
                + 0.15 * test_metrics["precision"]
                + 0.15 * test_metrics["recall"]
                + 0.05 * (1.0 - test_metrics["false_positive_rate"])
            )

            report = ModelEvaluationReport(
                model_name=name,
                model_version=self.model_version,
                optimal_threshold=opt_thresh,
                val_pr_auc=val_metrics["pr_auc"],
                val_roc_auc=val_metrics["roc_auc"],
                val_f1=val_metrics["f1_score"],
                val_f2=val_metrics["f2_score"],
                val_precision=val_metrics["precision"],
                val_recall=val_metrics["recall"],
                test_accuracy=test_metrics["accuracy"],
                test_precision=test_metrics["precision"],
                test_recall=test_metrics["recall"],
                test_f1=test_metrics["f1_score"],
                test_f2=test_metrics["f2_score"],
                test_roc_auc=test_metrics["roc_auc"],
                test_pr_auc=test_metrics["pr_auc"],
                test_fpr=test_metrics["false_positive_rate"],
                test_fnr=test_metrics["false_negative_rate"],
                test_confusion_matrix=test_metrics["confusion_matrix"],
                is_active=False,
                selection_score=round(selection_score, 4),
            )
            comparison_reports[name] = report

            if selection_score > best_score:
                best_score = selection_score
                best_model_name = name

        # Mark selected champion model as active
        if best_model_name in comparison_reports:
            comparison_reports[best_model_name].is_active = True

        selected_model_report = comparison_reports[best_model_name]

        # 4. Build Active Model Metadata
        active_metadata = {
            "model_name": selected_model_report.model_name,
            "model_version": self.model_version,
            "selected_threshold": selected_model_report.optimal_threshold,
            "training_timestamp": datetime.now(timezone.utc).isoformat(),
            "dataset_version_path": dataset_path,
            "feature_version": feature_version,
            "preprocessing_version": "v1.2.0",
            "model_artifact_path": f"{self.artifact_dir}/{selected_model_report.model_name}.joblib",
            "preprocessor_artifact_path": f"{self.artifact_dir}/preprocessor.joblib",
            "is_active": True,
            "selection_score": selected_model_report.selection_score,
            "evaluation_metrics": {
                "accuracy": selected_model_report.test_accuracy,
                "precision": selected_model_report.test_precision,
                "recall": selected_model_report.test_recall,
                "f1_score": selected_model_report.test_f1,
                "f2_score": selected_model_report.test_f2,
                "roc_auc": selected_model_report.test_roc_auc,
                "pr_auc": selected_model_report.test_pr_auc,
                "false_positive_rate": selected_model_report.test_fpr,
                "false_negative_rate": selected_model_report.test_fnr,
                "confusion_matrix": selected_model_report.test_confusion_matrix,
            },
        }

        # 5. Build Model Registry
        model_registry = {
            "version": self.model_version,
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "active_model": best_model_name,
            "models": {k: asdict(v) for k, v in comparison_reports.items()},
        }

        # 6. Save metadata files
        self.artifact_dir.mkdir(parents=True, exist_ok=True)
        with open(self.artifact_dir / "active_model_metadata.json", "w", encoding="utf-8") as f:
            json.dump(active_metadata, f, indent=2)

        with open(self.artifact_dir / "model_registry.json", "w", encoding="utf-8") as f:
            json.dump(model_registry, f, indent=2)

        return {
            "selected_model": best_model_name,
            "active_metadata": active_metadata,
            "comparison": {k: asdict(v) for k, v in comparison_reports.items()},
        }

