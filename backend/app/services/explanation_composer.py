"""Evidence-Grounded Explanation Composer.

Composes human-auditable, verifiable investigation briefs by synthesizing:
1. SHAP local feature attribution contributions
2. Verified counterfactual perturbations
3. Unsupervised Isolation Forest anomaly deviations
4. Entity & device network linkage signals
5. Deterministic rule engine triggers
6. Model uncertainty & boundary proximity
7. Historical customer behavioral profile deviations

Eliminates ungrounded LLM hallucinations by using deterministic, evidence-traceable templates.
"""

from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional
from ml.explainability.counterfactual_engine import CounterfactualResult
from ml.anomaly.isolation_forest_service import AnomalyEvaluationResult
from ml.evaluation.uncertainty_service import UncertaintyEvaluation
from backend.app.services.network_intelligence_service import NetworkIntelligenceReport
from backend.app.schemas.payment import TriggeredRule, StructuredShapFactor


@dataclass
class EvidenceItem:
    """Individual structured evidence bullet for fraud analysts."""

    category: str        # 'MODEL_SHAP' | 'UNSUPERVISED_ANOMALY' | 'NETWORK_GRAPH' | 'DETERMINISTIC_RULE' | 'UNCERTAINTY' | 'BEHAVIOR_PROFILE'
    severity: str        # 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW' | 'INFO'
    headline: str
    detail: str
    observed_metric: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ComposedExplanation:
    """Complete composed explanation bundle."""

    investigator_summary: str
    technical_summary: str
    evidence_items: List[EvidenceItem]
    counterfactual_summary: Optional[str]
    confidence_statement: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "investigator_summary": self.investigator_summary,
            "technical_summary": self.technical_summary,
            "evidence_items": [e.to_dict() for e in self.evidence_items],
            "counterfactual_summary": self.counterfactual_summary,
            "confidence_statement": self.confidence_statement,
        }


class ExplanationComposer:
    """Synthesizes structured multi-model evidence into actionable investigator narratives."""

    @classmethod
    def compose_explanation(
        cls,
        decision: str,
        risk_score: float,
        fraud_probability: float,
        model_version: str,
        shap_factors: Optional[List[StructuredShapFactor]] = None,
        counterfactual: Optional[CounterfactualResult] = None,
        anomaly: Optional[AnomalyEvaluationResult] = None,
        network: Optional[NetworkIntelligenceReport] = None,
        triggered_rules: Optional[List[TriggeredRule]] = None,
        uncertainty: Optional[UncertaintyEvaluation] = None,
        behavior_deviation: Optional[float] = None,
    ) -> ComposedExplanation:
        """
        Build fully grounded, traceable explanation artifact.
        """
        evidence_items: List[EvidenceItem] = []
        investigator_sentences: List[str] = []

        # 1. Decision Headline
        investigator_sentences.append(
            f"Pre-authorization evaluated transaction as {decision} with a composite Risk Score of {risk_score:.0f}/100 "
            f"(Model Fraud Probability: {fraud_probability * 100:.1f}%)."
        )

        # 2. Rule Engine Evidence
        if triggered_rules and len(triggered_rules) > 0:
            rule_names = [r.rule_name for r in triggered_rules]
            investigator_sentences.append(
                f"Evaluation intercepted {len(triggered_rules)} active policy rule(s): {', '.join(rule_names)}."
            )
            for r in triggered_rules:
                evidence_items.append(EvidenceItem(
                    category="DETERMINISTIC_RULE",
                    severity=r.severity if hasattr(r, "severity") else "HIGH",
                    headline=f"Rule Triggered: {r.rule_name}",
                    detail=r.description if hasattr(r, "description") else f"Policy rule {r.rule_id} condition satisfied.",
                    observed_metric=f"Action: {getattr(r, 'action_impact', 'FLAG')}",
                ))

        # 3. SHAP Top Feature Drivers
        if shap_factors and len(shap_factors) > 0:
            top_risk_inc = [f for f in shap_factors if getattr(f, "direction", "INCREASE") in ["INCREASE", "POSITIVE", "INCREASES_FRAUD_RISK"]][:3]
            if top_risk_inc:
                driver_descs = [f"{f.feature_name} ({f.reason})" for f in top_risk_inc]
                investigator_sentences.append(
                    f"Primary statistical risk drivers: {'; '.join(driver_descs)}."
                )
            for sf in shap_factors[:5]:
                direction = getattr(sf, "direction", "INCREASE")
                sev = "HIGH" if direction in ["INCREASE", "POSITIVE", "INCREASES_FRAUD_RISK"] else "INFO"
                evidence_items.append(EvidenceItem(
                    category="MODEL_SHAP",
                    severity=sev,
                    headline=f"SHAP Attribution: {sf.feature_name}",
                    detail=sf.reason,
                    observed_metric=f"Impact: {getattr(sf, 'importance_weight', 0.0):+.3f}",
                ))

        # 4. Unsupervised Anomaly Evidence
        if anomaly and anomaly.anomaly_status == "AVAILABLE" and anomaly.anomaly_score is not None:
            if anomaly.is_anomaly or anomaly.anomaly_score > 0.60:
                investigator_sentences.append(
                    f"Unsupervised Isolation Forest detected notable multidimensional deviation (Anomaly Score: {anomaly.anomaly_score:.2f}, Threshold: {anomaly.threshold:.2f})."
                )
                evidence_items.append(EvidenceItem(
                    category="UNSUPERVISED_ANOMALY",
                    severity="HIGH" if anomaly.anomaly_score >= 0.75 else "MEDIUM",
                    headline="Unsupervised Isolation Forest Outlier Detected",
                    detail=f"Transaction vector deviates from normal baseline distribution across {len(anomaly.top_deviating_features)} monitored features.",
                    observed_metric=f"Score: {anomaly.anomaly_score:.3f} (Threshold: {anomaly.threshold:.2f})",
                ))

        # 5. Network / Entity Linkage Evidence
        if network and network.network_risk_score > 30:
            investigator_sentences.append(
                f"Entity graph analysis identified elevated linkage risk ({network.network_risk_score:.0f}/100) across {network.connected_entity_count} connected nodes."
            )
            evidence_items.append(EvidenceItem(
                category="NETWORK_GRAPH",
                severity="HIGH" if network.network_risk_score >= 70 else "MEDIUM",
                headline="Sybil / Multi-Entity Linkage Detected",
                detail="; ".join(network.evidence) if network.evidence else "Hardware or merchant clustering observed.",
                observed_metric=f"Network Risk: {network.network_risk_score:.0f}/100",
            ))

        # 6. Customer Behavioral Baseline
        if behavior_deviation is not None and behavior_deviation > 40:
            evidence_items.append(EvidenceItem(
                category="BEHAVIOR_PROFILE",
                severity="HIGH" if behavior_deviation > 70 else "MEDIUM",
                headline="Customer Baseline Behavioral Deviation",
                detail="Monetary volume and velocity diverge significantly from customer's 30-day historical mean.",
                observed_metric=f"Deviation Index: {behavior_deviation:.1f}/100",
            ))

        # 7. Uncertainty Assessment
        confidence_statement = "Model inference confidence is HIGH."
        if uncertainty:
            if uncertainty.uncertainty_level == "HIGH":
                confidence_statement = (
                    f"CAUTION: Prediction uncertainty is HIGH (Score: {uncertainty.uncertainty_score:.2f}). "
                    f"Decision lies near classification boundary ({uncertainty.boundary_proximity:.2f} ambiguity). "
                    "Manual investigator review is recommended."
                )
                evidence_items.append(EvidenceItem(
                    category="UNCERTAINTY",
                    severity="MEDIUM",
                    headline="Elevated Prediction Boundary Ambiguity",
                    detail=f"Model outputs show boundary proximity of {uncertainty.boundary_proximity:.2f} and estimator variance of {uncertainty.ensemble_variance:.4f}.",
                    observed_metric=f"Uncertainty: {uncertainty.uncertainty_level} ({uncertainty.uncertainty_score:.2f})",
                ))
            elif uncertainty.uncertainty_level == "MODERATE":
                confidence_statement = f"Model inference confidence is MODERATE (Uncertainty Score: {uncertainty.uncertainty_score:.2f})."

        # 8. Counterfactual Synthesis
        cf_summary = counterfactual.actionable_summary if counterfactual else None

        # 9. Technical Summary
        technical_summary = (
            f"Active Model: {model_version} | Probability: {fraud_probability:.4f} | Risk Score: {risk_score:.1f} | "
            f"Decision: {decision} | Rules Fired: {len(triggered_rules) if triggered_rules else 0} | "
            f"Anomaly Status: {anomaly.anomaly_status if anomaly else 'N/A'} | Confidence: {uncertainty.confidence_status if uncertainty else 'STANDARD'}"
        )

        return ComposedExplanation(
            investigator_summary=" ".join(investigator_sentences),
            technical_summary=technical_summary,
            evidence_items=evidence_items,
            counterfactual_summary=cf_summary,
            confidence_statement=confidence_statement,
        )
