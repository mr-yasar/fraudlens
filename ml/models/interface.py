"""Standardized Model Interface for Supervised Fraud Detection."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    average_precision_score,
    confusion_matrix,
    brier_score_loss,
)


@dataclass
class ModelValidationReport:
    """Comprehensive validation metrics report for a model on held-out data."""

    model_name: str
    model_version: str
    threshold: float
    accuracy: float
    precision: float
    recall: float
    f1: float
    roc_auc: float
    pr_auc: float
    brier_score: float
    true_positives: int
    false_positives: int
    true_negatives: int
    false_negatives: int
    selection_score: float
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class BaseFraudModel(ABC):
    """Abstract base class ensuring consistent API across all supervised algorithms."""

    def __init__(self, model_name: str, model_version: str = "v1.2.0") -> None:
        self.model_name = model_name
        self.model_version = model_version
        self.is_fitted: bool = False
        self.optimal_threshold: float = 0.5

    @abstractmethod
    def fit(self, X: np.ndarray, y: np.ndarray) -> "BaseFraudModel":
        """Train the underlying model using uniform feature matrices."""
        pass

    @abstractmethod
    def predict(self, X: np.ndarray, threshold: Optional[float] = None) -> np.ndarray:
        """Binary prediction (0=Legitimate, 1=Fraud) at operating threshold."""
        pass

    @abstractmethod
    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """Continuous probability estimate of positive class [0.0, 1.0]."""
        pass

    def validate(
        self, X_val: np.ndarray, y_val: np.ndarray, threshold: Optional[float] = None
    ) -> ModelValidationReport:
        """Standardized validation protocol across all models."""
        thresh = threshold if threshold is not None else self.optimal_threshold
        y_prob = self.predict_proba(X_val)
        y_pred = (y_prob >= thresh).astype(int)

        acc = float(accuracy_score(y_val, y_pred))
        prec = float(precision_score(y_val, y_pred, zero_division=0))
        rec = float(recall_score(y_val, y_pred, zero_division=0))
        f1 = float(f1_score(y_val, y_pred, zero_division=0))

        try:
            roc = float(roc_auc_score(y_val, y_prob))
        except Exception:
            roc = 0.5

        try:
            pr = float(average_precision_score(y_val, y_prob))
        except Exception:
            pr = 0.0

        try:
            brier = float(brier_score_loss(y_val, y_prob))
        except Exception:
            brier = 0.5

        tn, fp, fn, tp = confusion_matrix(y_val, y_pred, labels=[0, 1]).ravel()

        # Selection score: 60% PR-AUC + 40% F1 score
        selection_score = round(0.6 * pr + 0.4 * f1, 4)

        return ModelValidationReport(
            model_name=self.model_name,
            model_version=self.model_version,
            threshold=thresh,
            accuracy=round(acc, 4),
            precision=round(prec, 4),
            recall=round(rec, 4),
            f1=round(f1, 4),
            roc_auc=round(roc, 4),
            pr_auc=round(pr, 4),
            brier_score=round(brier, 4),
            true_positives=int(tp),
            false_positives=int(fp),
            true_negatives=int(tn),
            false_negatives=int(fn),
            selection_score=selection_score,
            metadata=self.metadata(),
        )

    def metadata(self) -> Dict[str, Any]:
        """Model parameters, fitted state, and threshold configuration."""
        return {
            "model_name": self.model_name,
            "model_version": self.model_version,
            "is_fitted": self.is_fitted,
            "optimal_threshold": self.optimal_threshold,
        }
