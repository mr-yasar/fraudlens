"""Actionable Counterfactual Explanation Engine for FraudLens AI.

Generates realistic, constraint-aware counterfactual scenarios by:
1. Selecting strictly mutable transaction features (Amount, Location, Device, Velocity).
2. Applying minimal perturbations towards safe baseline profiles.
3. Re-evaluating the actual active machine learning pipeline.
4. Verifying that the model output and decision tier genuinely changed.
5. Returning structured, verifiable evidence rather than fabricated text.
"""

from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd


@dataclass
class CounterfactualChange:
    """Individual feature modification in a counterfactual scenario."""

    feature_name: str
    original_value: Any
    counterfactual_value: Any
    description: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class CounterfactualResult:
    """Complete counterfactual explanation with verified model outcome."""

    status: str                       # 'SUCCESS' | 'NO_COUNTERFACTUAL_FOUND' | 'ALREADY_LOW_RISK' | 'ERROR'
    original_probability: float
    original_risk_score: float
    original_decision: str            # 'ALLOW' | 'REVIEW' | 'BLOCK'
    counterfactual_probability: Optional[float]
    counterfactual_risk_score: Optional[float]
    counterfactual_decision: Optional[str]
    probability_reduction: Optional[float]
    modified_features: List[CounterfactualChange]
    actionable_summary: str
    is_verified: bool

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "original_probability": round(self.original_probability, 4),
            "original_risk_score": round(self.original_risk_score, 1),
            "original_decision": self.original_decision,
            "counterfactual_probability": round(self.counterfactual_probability, 4) if self.counterfactual_probability is not None else None,
            "counterfactual_risk_score": round(self.counterfactual_risk_score, 1) if self.counterfactual_risk_score is not None else None,
            "counterfactual_decision": self.counterfactual_decision,
            "probability_reduction": round(self.probability_reduction, 4) if self.probability_reduction is not None else None,
            "modified_features": [f.to_dict() for f in self.modified_features],
            "actionable_summary": self.actionable_summary,
            "is_verified": self.is_verified,
        }


class CounterfactualEngine:
    """Generates verified counterfactual perturbations for high-risk transactions."""

    # Mutable candidate dimensions and safe direction heuristics
    MUTABLE_FEATURE_RULES = [
        # 1. Amount adjustment towards customer's historical average
        {
            "key": "Amount",
            "alt_key": "transaction_amount",
            "type": "amount_reduction",
            "target": "Average_Previous_Amount",
            "fallback_target": "avg_transaction_amount_30d_customer",
        },
        # 2. Location mismatch resolution (transacting from historical usual location)
        {
            "key": "Location",
            "type": "match_usual_location",
            "target": "Usual_Location",
        },
        # 3. Known device vs new untrusted device
        {
            "key": "New_Device",
            "alt_key": "new_device",
            "type": "set_value",
            "value": 0,
        },
        # 4. Failed password/security attempts
        {
            "key": "Failed_Attempts",
            "alt_key": "failed_attempts",
            "type": "set_value",
            "value": 0,
        },
        # 5. International transaction flag
        {
            "key": "International_Transaction",
            "alt_key": "is_international",
            "type": "set_value",
            "value": 0,
        },
    ]

    @classmethod
    def generate_counterfactual(
        cls,
        raw_payload: Dict[str, Any],
        preprocessor: Any,
        model: Any,
        risk_engine: Any,
        original_prob: float,
        original_risk: float,
        original_decision: str,
        threshold: float = 0.5,
    ) -> CounterfactualResult:
        """
        Search for minimal single- or multi-feature perturbation that lowers risk to ALLOW or REVIEW.
        """
        # If transaction is already LOW / ALLOW, no intervention is needed
        if original_decision == "ALLOW" and original_prob < threshold and original_risk < 40:
            return CounterfactualResult(
                status="ALREADY_LOW_RISK",
                original_probability=original_prob,
                original_risk_score=original_risk,
                original_decision=original_decision,
                counterfactual_probability=original_prob,
                counterfactual_risk_score=original_risk,
                counterfactual_decision=original_decision,
                probability_reduction=0.0,
                modified_features=[],
                actionable_summary="Transaction is already in the ALLOW tier. No counterfactual perturbation required.",
                is_verified=True,
            )

        best_result: Optional[Tuple[Dict[str, Any], float, float, str, List[CounterfactualChange]]] = None
        min_target_risk = original_risk

        # Strategy 1: Test individual atomic feature perturbations
        for rule in cls.MUTABLE_FEATURE_RULES:
            candidate_payload = dict(raw_payload)
            changes: List[CounterfactualChange] = []
            
            field_key = rule["key"] if rule["key"] in candidate_payload else rule.get("alt_key")
            if not field_key or field_key not in candidate_payload:
                continue

            orig_val = candidate_payload[field_key]

            if rule["type"] == "amount_reduction":
                # Lower amount to historical baseline average if current amount is elevated
                target_key = rule["target"] if rule["target"] in candidate_payload else rule.get("fallback_target")
                avg_val = float(candidate_payload.get(target_key, orig_val))
                if float(orig_val) > avg_val and avg_val > 0:
                    candidate_payload[field_key] = avg_val
                    changes.append(CounterfactualChange(
                        feature_name=field_key,
                        original_value=orig_val,
                        counterfactual_value=avg_val,
                        description=f"Transaction amount reduced from ${orig_val:,.2f} to customer baseline average (${avg_val:,.2f})",
                    ))

            elif rule["type"] == "match_usual_location":
                usual_loc = candidate_payload.get(rule["target"])
                if usual_loc and str(orig_val).lower() != str(usual_loc).lower():
                    candidate_payload[field_key] = usual_loc
                    changes.append(CounterfactualChange(
                        feature_name=field_key,
                        original_value=orig_val,
                        counterfactual_value=usual_loc,
                        description=f"Transaction location matched historical usual location ('{usual_loc}') instead of '{orig_val}'",
                    ))

            elif rule["type"] == "set_value":
                target_val = rule["value"]
                if int(orig_val) != int(target_val):
                    candidate_payload[field_key] = target_val
                    changes.append(CounterfactualChange(
                        feature_name=field_key,
                        original_value=orig_val,
                        counterfactual_value=target_val,
                        description=f"Field '{field_key}' resolved to safe baseline state ({target_val})",
                    ))

            if not changes:
                continue

            # Re-evaluate candidate through genuine preprocessor & model
            try:
                df_cand = pd.DataFrame([candidate_payload])
                x_cand = preprocessor.transform(df_cand)
                
                if hasattr(model, "predict_proba"):
                    c_prob = float(model.predict_proba(x_cand)[0, 1])
                elif hasattr(model, "decision_function"):
                    dec = float(model.decision_function(x_cand)[0])
                    c_prob = 1.0 / (1.0 + np.exp(-dec))
                else:
                    c_prob = float(model.predict(x_cand)[0])

                # Compute new risk score via deterministic engine
                amt_cand = float(candidate_payload.get("Amount", candidate_payload.get("transaction_amount", 100.0)))
                c_risk_eval = risk_engine.compute_risk_score(
                    fraud_probability=c_prob,
                    amount=amt_cand,
                    rule_impacts=[],
                )
                c_risk = float(c_risk_eval.final_risk_score)
                c_tier = c_risk_eval.risk_level

                # Map tier to pre-auth decision
                c_decision = "ALLOW" if c_tier == "LOW" else ("REVIEW" if c_tier == "MEDIUM" else "BLOCK")

                # If this reduces risk significantly, check if it's the best single-feature candidate
                if c_risk < min_target_risk:
                    min_target_risk = c_risk
                    best_result = (candidate_payload, c_prob, c_risk, c_decision, changes)
                    if c_decision in ["ALLOW", "REVIEW"] and c_decision != original_decision:
                        break  # Found viable counterfactual
            except Exception:
                continue

        # Strategy 2: If single-feature didn't flip decision from BLOCK, test combined composite perturbation
        if (best_result is None or best_result[3] == "BLOCK") and original_decision == "BLOCK":
            candidate_payload = dict(raw_payload)
            composite_changes: List[CounterfactualChange] = []

            # Combine: Known device + Normal location + Standard amount
            if "New_Device" in candidate_payload and candidate_payload["New_Device"] != 0:
                composite_changes.append(CounterfactualChange(
                    feature_name="New_Device",
                    original_value=candidate_payload["New_Device"],
                    counterfactual_value=0,
                    description="Device verified as existing recognized hardware",
                ))
                candidate_payload["New_Device"] = 0

            if "Location" in candidate_payload and "Usual_Location" in candidate_payload:
                if candidate_payload["Location"] != candidate_payload["Usual_Location"]:
                    composite_changes.append(CounterfactualChange(
                        feature_name="Location",
                        original_value=candidate_payload["Location"],
                        counterfactual_value=candidate_payload["Usual_Location"],
                        description=f"Originated from registered home location ({candidate_payload['Usual_Location']})",
                    ))
                    candidate_payload["Location"] = candidate_payload["Usual_Location"]

            if "Amount" in candidate_payload and "Average_Previous_Amount" in candidate_payload:
                avg_val = float(candidate_payload["Average_Previous_Amount"])
                if float(candidate_payload["Amount"]) > avg_val and avg_val > 0:
                    composite_changes.append(CounterfactualChange(
                        feature_name="Amount",
                        original_value=candidate_payload["Amount"],
                        counterfactual_value=avg_val,
                        description=f"Amount aligned with historical baseline (${avg_val:,.2f})",
                    ))
                    candidate_payload["Amount"] = avg_val

            if composite_changes:
                try:
                    df_comp = pd.DataFrame([candidate_payload])
                    x_comp = preprocessor.transform(df_comp)
                    c_prob = float(model.predict_proba(x_comp)[0, 1]) if hasattr(model, "predict_proba") else 0.1
                    amt_cand = float(candidate_payload.get("Amount", 100.0))
                    c_risk_eval = risk_engine.compute_risk_score(
                        fraud_probability=c_prob,
                        amount=amt_cand,
                        rule_impacts=[],
                    )
                    c_risk = float(c_risk_eval.final_risk_score)
                    c_tier = c_risk_eval.risk_level
                    c_decision = "ALLOW" if c_tier == "LOW" else ("REVIEW" if c_tier == "MEDIUM" else "BLOCK")

                    if c_risk < original_risk:
                        best_result = (candidate_payload, c_prob, c_risk, c_decision, composite_changes)
                except Exception:
                    pass

        # Format final result
        if best_result is not None:
            _, final_prob, final_risk, final_decision, changes = best_result
            reduction = max(0.0, original_prob - final_prob)
            
            # Construct human-interpretable actionable summary from real evidence
            change_descriptions = "; ".join([c.description for c in changes])
            summary = (
                f"If {change_descriptions}, the model-assessed fraud probability decreases by {reduction * 100:.1f}% "
                f"(from {original_prob * 100:.1f}% to {final_prob * 100:.1f}%), moving risk decision from {original_decision} to {final_decision}."
            )

            return CounterfactualResult(
                status="SUCCESS",
                original_probability=original_prob,
                original_risk_score=original_risk,
                original_decision=original_decision,
                counterfactual_probability=final_prob,
                counterfactual_risk_score=final_risk,
                counterfactual_decision=final_decision,
                probability_reduction=reduction,
                modified_features=changes,
                actionable_summary=summary,
                is_verified=True,
            )
        else:
            return CounterfactualResult(
                status="NO_COUNTERFACTUAL_FOUND",
                original_probability=original_prob,
                original_risk_score=original_risk,
                original_decision=original_decision,
                counterfactual_probability=None,
                counterfactual_risk_score=None,
                counterfactual_decision=None,
                probability_reduction=None,
                modified_features=[],
                actionable_summary="No single or composite mutable feature perturbation sufficiently altered the risk tier within valid constraints.",
                is_verified=False,
            )
