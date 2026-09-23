"""Model Uncertainty Estimation and Confidence Scoring Service.

Computes prediction uncertainty through:
1. Ensemble probability disagreement across multiple diverse estimators (XGB, RF, LR).
2. Boundary margin (proximity to decision threshold).
3. Entropy / spread proxy.

Assigns explicit uncertainty levels: 'LOW', 'MODERATE', 'HIGH'.
Transactions with HIGH uncertainty are flagged for manual review.
"""

from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional
import numpy as np


@dataclass
class UncertaintyEvaluation:
    """Structured uncertainty assessment for an inference request."""

    uncertainty_score: float         # 0.0 (high certainty) to 1.0 (high uncertainty)
    uncertainty_level: str           # LOW | MODERATE | HIGH
    confidence_status: str           # HIGH_CONFIDENCE | MODERATE_CONFIDENCE | LOW_CONFIDENCE
    boundary_proximity: float        # Distance to decision threshold [0.0 - 1.0]
    ensemble_variance: float         # Variance of predictions across estimators
    should_route_to_review: bool     # True if uncertainty is high enough to warrant human investigation
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class UncertaintyEstimationService:
    """Quantifies epistemic and aleatoric confidence on individual transactions."""

    @classmethod
    def evaluate_uncertainty(
        cls,
        probabilities: Dict[str, float],
        active_probability: float,
        threshold: float = 0.5,
        uncertainty_threshold: float = 0.60,
    ) -> UncertaintyEvaluation:
        """
        Evaluate prediction uncertainty across available model outputs.
        
        Args:
            probabilities: Dict mapping model_name -> float probability (e.g. {'xgboost': 0.12, 'random_forest': 0.18, 'logistic_regression': 0.08})
            active_probability: Probability from the promoted active champion model.
            threshold: Operating decision threshold for active model.
            uncertainty_threshold: Threshold above which uncertainty triggers manual review.
        """
        prob_values = list(probabilities.values()) if probabilities else [active_probability]
        
        # 1. Ensemble Disagreement Variance
        if len(prob_values) > 1:
            ens_var = float(np.var(prob_values))
            ens_std = float(np.std(prob_values))
            max_diff = float(np.max(prob_values) - np.min(prob_values))
        else:
            ens_var = 0.0
            ens_std = 0.0
            max_diff = 0.0

        # 2. Boundary Proximity (How close active probability is to decision threshold)
        # Distance = |p - threshold| / max(threshold, 1 - threshold)
        denom = max(1e-5, max(threshold, 1.0 - threshold))
        dist_from_threshold = abs(active_probability - threshold) / denom
        # Invert so 1.0 = right on the boundary (maximum ambiguity)
        boundary_ambiguity = float(np.clip(1.0 - dist_from_threshold, 0.0, 1.0))

        # 3. Model Entropy
        p_safe = np.clip(active_probability, 1e-6, 1.0 - 1e-6)
        entropy = float(- (p_safe * np.log2(p_safe) + (1 - p_safe) * np.log2(1 - p_safe)))

        # 4. Composite Uncertainty Score (Weighted combination of boundary proximity and ensemble disagreement)
        if len(prob_values) > 1:
            uncertainty_score = float(0.55 * boundary_ambiguity + 0.30 * max_diff + 0.15 * ens_std)
        else:
            uncertainty_score = float(0.75 * boundary_ambiguity + 0.25 * entropy)

        uncertainty_score = round(float(np.clip(uncertainty_score, 0.0, 1.0)), 4)

        # 5. Classify Uncertainty Level
        if uncertainty_score >= 0.65 or (boundary_ambiguity > 0.85 and max_diff > 0.25):
            unc_level = "HIGH"
            conf_status = "LOW_CONFIDENCE"
            route_review = True
        elif uncertainty_score >= 0.35:
            unc_level = "MODERATE"
            conf_status = "MODERATE_CONFIDENCE"
            route_review = False
        else:
            unc_level = "LOW"
            conf_status = "HIGH_CONFIDENCE"
            route_review = False

        return UncertaintyEvaluation(
            uncertainty_score=uncertainty_score,
            uncertainty_level=unc_level,
            confidence_status=conf_status,
            boundary_proximity=round(boundary_ambiguity, 4),
            ensemble_variance=round(ens_var, 5),
            should_route_to_review=route_review,
            details={
                "probabilities": {k: round(v, 4) for k, v in probabilities.items()},
                "active_probability": round(active_probability, 4),
                "threshold": round(threshold, 4),
                "entropy": round(entropy, 4),
                "max_estimator_spread": round(max_diff, 4),
            },
        )
