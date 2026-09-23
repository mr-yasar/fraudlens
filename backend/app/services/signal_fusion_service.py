"""Transparent Multi-Signal Fusion Engine.

Combines distinct, verifiable evidence signals into an auditable fused risk indicator:
1. Supervised ML Fraud Probability (Champion model classification)
2. Unsupervised Anomaly Score (Isolation Forest deviation from baseline)
3. Entity / Linkage Intelligence Score (Shared device / mule network connectivity)
4. Customer Historical Behavioral Deviation (Rolling baseline variance)
5. Model Uncertainty Penalty

Guarantees full provenance and transparent breakdown of evidence sources.
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import numpy as np


@dataclass
class EvidenceComponent:
    """Individual auditable evidence signal component."""

    signal_name: str
    raw_value: Optional[float]
    normalized_value: float          # 0.0 - 1.0
    weight: float
    contribution: float              # normalized_value * weight
    status: str                      # 'AVAILABLE' | 'UNAVAILABLE' | 'DEGRADED'
    description: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class FusedSignalResult:
    """Structured result of multi-signal fusion."""

    fused_index: float               # 0.0 - 1.0 (continuous composite risk indicator)
    primary_driver: str              # Signal that contributed the highest risk
    fusion_version: str
    evidence_breakdown: Dict[str, EvidenceComponent]
    fusion_notes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "fused_index": round(self.fused_index, 4),
            "primary_driver": self.primary_driver,
            "fusion_version": self.fusion_version,
            "evidence_breakdown": {k: v.to_dict() for k, v in self.evidence_breakdown.items()},
            "fusion_notes": self.fusion_notes,
        }


class SignalFusionService:
    """Configurable, versioned signal fusion engine."""

    VERSION: str = "v1.2.0"

    # Validated default weight distribution when all signals are available
    DEFAULT_WEIGHTS = {
        "supervised_ml": 0.55,
        "behavior_profile": 0.20,
        "unsupervised_anomaly": 0.15,
        "network_linkage": 0.10,
    }

    @classmethod
    def fuse_signals(
        cls,
        supervised_probability: float,
        anomaly_score: Optional[float] = None,
        network_risk_score: Optional[float] = None,
        behavior_deviation_score: Optional[float] = None,
        uncertainty_score: Optional[float] = None,
        weights: Optional[Dict[str, float]] = None,
    ) -> FusedSignalResult:
        """
        Dynamically normalize and fuse available signals.
        If a signal is UNAVAILABLE, weights are re-normalized over available signals without inventing data.
        """
        active_weights = dict(weights or cls.DEFAULT_WEIGHTS)
        evidence: Dict[str, EvidenceComponent] = {}
        notes: List[str] = []

        # 1. Supervised ML Signal
        p_sup = float(np.clip(supervised_probability, 0.0, 1.0))
        evidence["supervised_ml"] = EvidenceComponent(
            signal_name="Supervised ML Model",
            raw_value=round(supervised_probability, 4),
            normalized_value=p_sup,
            weight=active_weights.get("supervised_ml", 0.55),
            contribution=0.0,  # Computed below after weight normalization
            status="AVAILABLE",
            description="Supervised classifier prediction probability",
        )

        # 2. Behavioral Profile Deviation
        if behavior_deviation_score is not None:
            # Score is 0-100 or 0-1, normalize to 0-1
            p_beh = float(np.clip(behavior_deviation_score / 100.0 if behavior_deviation_score > 1.0 else behavior_deviation_score, 0.0, 1.0))
            evidence["behavior_profile"] = EvidenceComponent(
                signal_name="Behavior Profile Deviation",
                raw_value=round(behavior_deviation_score, 2),
                normalized_value=p_beh,
                weight=active_weights.get("behavior_profile", 0.20),
                contribution=0.0,
                status="AVAILABLE",
                description="Historical baseline amount and velocity deviation",
            )
        else:
            evidence["behavior_profile"] = EvidenceComponent(
                signal_name="Behavior Profile Deviation",
                raw_value=None,
                normalized_value=0.0,
                weight=0.0,
                contribution=0.0,
                status="UNAVAILABLE",
                description="No customer history available (cold start)",
            )
            notes.append("Behavior profile signal unavailable; re-allocating weight.")

        # 3. Unsupervised Anomaly Score
        if anomaly_score is not None:
            p_anom = float(np.clip(anomaly_score, 0.0, 1.0))
            evidence["unsupervised_anomaly"] = EvidenceComponent(
                signal_name="Unsupervised Anomaly (Isolation Forest)",
                raw_value=round(anomaly_score, 4),
                normalized_value=p_anom,
                weight=active_weights.get("unsupervised_anomaly", 0.15),
                contribution=0.0,
                status="AVAILABLE",
                description="Isolation Forest feature space density deviation",
            )
        else:
            evidence["unsupervised_anomaly"] = EvidenceComponent(
                signal_name="Unsupervised Anomaly (Isolation Forest)",
                raw_value=None,
                normalized_value=0.0,
                weight=0.0,
                contribution=0.0,
                status="UNAVAILABLE",
                description="Anomaly service unavailable or not fitted",
            )
            notes.append("Anomaly score unavailable; re-allocating weight.")

        # 4. Network Linkage Signal
        if network_risk_score is not None:
            p_net = float(np.clip(network_risk_score / 100.0, 0.0, 1.0))
            evidence["network_linkage"] = EvidenceComponent(
                signal_name="Network Linkage Intelligence",
                raw_value=round(network_risk_score, 2),
                normalized_value=p_net,
                weight=active_weights.get("network_linkage", 0.10),
                contribution=0.0,
                status="AVAILABLE",
                description="Shared hardware, IP, and entity graph connectivity",
            )
        else:
            evidence["network_linkage"] = EvidenceComponent(
                signal_name="Network Linkage Intelligence",
                raw_value=None,
                normalized_value=0.0,
                weight=0.0,
                contribution=0.0,
                status="UNAVAILABLE",
                description="No shared entity links detected",
            )

        # 5. Normalize Available Weights
        available_keys = [k for k, v in evidence.items() if v.status == "AVAILABLE"]
        total_avail_weight = sum(active_weights.get(k, 0.0) for k in available_keys)
        
        if total_avail_weight > 0:
            for k in available_keys:
                norm_w = active_weights.get(k, 0.0) / total_avail_weight
                evidence[k].weight = round(norm_w, 4)
                evidence[k].contribution = round(evidence[k].normalized_value * norm_w, 4)

        # 6. Compute Base Fused Index
        fused_sum = sum(v.contribution for v in evidence.values())
        
        # 7. Uncertainty Adjustment: Slight upward shift if uncertainty is extreme
        if uncertainty_score is not None and uncertainty_score >= 0.70:
            uncertainty_penalty = 0.05 * (uncertainty_score - 0.70) / 0.30
            fused_sum = min(1.0, fused_sum + uncertainty_penalty)
            notes.append(f"High prediction uncertainty ({round(uncertainty_score, 2)}) applied +{round(uncertainty_penalty, 3)} caution adjustment.")

        fused_final = float(np.clip(fused_sum, 0.0, 1.0))

        # 8. Identify Primary Driver
        primary = max(evidence.items(), key=lambda item: item[1].contribution if item[1].status == "AVAILABLE" else -1.0)[0]

        return FusedSignalResult(
            fused_index=round(fused_final, 4),
            primary_driver=primary,
            fusion_version=cls.VERSION,
            evidence_breakdown=evidence,
            fusion_notes=notes,
        )
