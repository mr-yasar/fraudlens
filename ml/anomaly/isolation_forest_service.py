"""Unsupervised Anomaly Intelligence Layer using Isolation Forest.

Independent anomaly scoring layer that measures deviation from normal
baseline transactions without using ground truth fraud labels.

Rules:
- anomaly_score != fraud_probability
- Score direction: 0.0 (Normal baseline) to 1.0 (Highly anomalous)
- Graceful degradation: anomaly_status = 'UNAVAILABLE', never fabricated.
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest


@dataclass
class AnomalyEvaluationResult:
    """Structured output for unsupervised anomaly scoring."""

    anomaly_score: Optional[float]
    anomaly_status: str  # 'AVAILABLE' | 'UNAVAILABLE' | 'DEGRADED'
    is_anomaly: bool
    threshold: float
    contamination: float
    model_version: str
    feature_dimension: int
    top_deviating_features: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class AnomalyIntelligenceService:
    """Engine for training, persisting, and evaluating unsupervised Isolation Forest anomalies."""

    _instance: Optional["AnomalyIntelligenceService"] = None

    def __init__(self, artifact_dir: Union[str, Path] = "ml/artifacts") -> None:
        self.artifact_dir = Path(artifact_dir)
        self.model: Optional[IsolationForest] = None
        self.metadata: Dict[str, Any] = {}
        self.model_version: str = "v1.0.0"
        self.contamination: float = 0.03
        self.threshold: float = 0.65
        self.feature_names: List[str] = []
        self.baseline_mean: Optional[np.ndarray] = None
        self.baseline_std: Optional[np.ndarray] = None
        self.is_ready: bool = False

        self._load_artifact()

    @classmethod
    def get_instance(cls, artifact_dir: Union[str, Path] = "ml/artifacts") -> "AnomalyIntelligenceService":
        if cls._instance is None:
            cls._instance = cls(artifact_dir=artifact_dir)
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        cls._instance = None

    def _load_artifact(self) -> None:
        """Safely load serialized Isolation Forest artifact and baseline distribution."""
        model_path = self.artifact_dir / "isolation_forest.joblib"
        meta_path = self.artifact_dir / "anomaly_metadata.json"

        if not model_path.exists() or not meta_path.exists():
            self.is_ready = False
            return

        try:
            with open(meta_path, "r", encoding="utf-8") as f:
                self.metadata = json.load(f)

            self.model = joblib.load(model_path)
            self.model_version = self.metadata.get("version", "v1.0.0")
            self.contamination = float(self.metadata.get("contamination", 0.03))
            self.threshold = float(self.metadata.get("anomaly_threshold", 0.65))
            self.feature_names = self.metadata.get("feature_names", [])

            if "baseline_mean" in self.metadata and "baseline_std" in self.metadata:
                self.baseline_mean = np.array(self.metadata["baseline_mean"])
                self.baseline_std = np.array(self.metadata["baseline_std"])

            self.is_ready = True
        except Exception:
            self.is_ready = False

    def train_and_persist(
        self,
        X_train_mat: np.ndarray,
        feature_names: List[str],
        contamination: float = 0.03,
        n_estimators: int = 150,
        random_state: int = 42,
    ) -> Dict[str, Any]:
        """Train Isolation Forest on normal/baseline feature representations."""
        if len(X_train_mat) == 0:
            raise ValueError("Training matrix for Isolation Forest cannot be empty.")

        iso_forest = IsolationForest(
            n_estimators=n_estimators,
            contamination=contamination,
            max_samples="auto",
            random_state=random_state,
            n_jobs=-1,
        )
        iso_forest.fit(X_train_mat)

        # Raw decision scores: higher = normal, lower = anomalous
        raw_scores = iso_forest.score_samples(X_train_mat)
        # Convert to 0.0 - 1.0 where 1.0 = most anomalous
        min_s, max_s = float(np.min(raw_scores)), float(np.max(raw_scores))
        
        baseline_mean = np.mean(X_train_mat, axis=0).tolist()
        baseline_std = (np.std(X_train_mat, axis=0) + 1e-5).tolist()

        metadata = {
            "version": "v1.0.0",
            "model_type": "IsolationForest",
            "contamination": contamination,
            "n_estimators": n_estimators,
            "random_state": random_state,
            "training_samples": int(X_train_mat.shape[0]),
            "feature_dimension": int(X_train_mat.shape[1]),
            "feature_names": feature_names,
            "raw_score_min": min_s,
            "raw_score_max": max_s,
            "anomaly_threshold": 0.65,
            "baseline_mean": baseline_mean,
            "baseline_std": baseline_std,
            "trained_at": datetime.now(timezone.utc).isoformat(),
        }

        # Save artifacts
        self.artifact_dir.mkdir(parents=True, exist_ok=True)
        joblib.dump(iso_forest, self.artifact_dir / "isolation_forest.joblib")
        with open(self.artifact_dir / "anomaly_metadata.json", "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)

        self.model = iso_forest
        self.metadata = metadata
        self.model_version = metadata["version"]
        self.contamination = contamination
        self.threshold = 0.65
        self.feature_names = feature_names
        self.baseline_mean = np.array(baseline_mean)
        self.baseline_std = np.array(baseline_std)
        self.is_ready = True

        return metadata

    def score_vector(self, x_vec: np.ndarray) -> AnomalyEvaluationResult:
        """Evaluate a single 1D or 2D feature vector and compute anomaly score."""
        if not self.is_ready or self.model is None:
            return AnomalyEvaluationResult(
                anomaly_score=None,
                anomaly_status="UNAVAILABLE",
                is_anomaly=False,
                threshold=self.threshold,
                contamination=self.contamination,
                model_version=self.model_version,
                feature_dimension=0,
                metadata={"reason": "Isolation Forest model artifact not loaded."},
            )

        try:
            vec_2d = x_vec.reshape(1, -1) if x_vec.ndim == 1 else x_vec
            
            # IsolationForest score_samples: opposite of anomaly score (higher is normal, lower is anomalous)
            raw_score = float(self.model.score_samples(vec_2d)[0])
            
            # Normalization to [0.0, 1.0] using recorded calibration bounds
            min_s = float(self.metadata.get("raw_score_min", -0.8))
            max_s = float(self.metadata.get("raw_score_max", -0.3))
            spread = max(1e-5, max_s - min_s)
            
            # Invert: low raw score -> high anomaly score
            norm_anomaly_score = float(np.clip(1.0 - ((raw_score - min_s) / spread), 0.0, 1.0))
            norm_anomaly_score = round(norm_anomaly_score, 4)

            is_anomaly = bool(norm_anomaly_score >= self.threshold)

            # Top deviating features relative to baseline
            top_deviations: List[Dict[str, Any]] = []
            if self.baseline_mean is not None and self.baseline_std is not None and len(self.feature_names) > 0:
                flat_vec = vec_2d[0]
                z_scores = np.abs((flat_vec - self.baseline_mean) / self.baseline_std)
                top_indices = np.argsort(z_scores)[::-1][:5]
                for idx in top_indices:
                    feat_name = self.feature_names[idx] if idx < len(self.feature_names) else f"feature_{idx}"
                    top_deviations.append({
                        "feature_name": feat_name,
                        "observed_value": round(float(flat_vec[idx]), 4),
                        "z_score": round(float(z_scores[idx]), 3),
                        "baseline_mean": round(float(self.baseline_mean[idx]), 4),
                    })

            return AnomalyEvaluationResult(
                anomaly_score=norm_anomaly_score,
                anomaly_status="AVAILABLE",
                is_anomaly=is_anomaly,
                threshold=self.threshold,
                contamination=self.contamination,
                model_version=self.model_version,
                feature_dimension=vec_2d.shape[1],
                top_deviating_features=top_deviations,
                metadata={
                    "raw_score": round(raw_score, 5),
                    "model_type": "IsolationForest",
                },
            )
        except Exception as err:
            return AnomalyEvaluationResult(
                anomaly_score=None,
                anomaly_status="DEGRADED",
                is_anomaly=False,
                threshold=self.threshold,
                contamination=self.contamination,
                model_version=self.model_version,
                feature_dimension=x_vec.shape[-1] if hasattr(x_vec, "shape") else 0,
                metadata={"error": str(err)},
            )
