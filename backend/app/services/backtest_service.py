"""Historical Replay and Policy Simulation Engine (Phase 41).

Allows security administrators to backtest new risk thresholds, rules,
and challenger models against historical transaction ledgers without mutating any records.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from backend.app.models.transaction import Transaction
from backend.app.services.behavior_profile_service import BehaviorProfileService
from backend.app.services.prediction_service import FraudPredictionService
from backend.app.services.risk_scoring_service import RiskScoringEngine
from backend.app.services.rule_engine import RuleEngine, RuleActionImpact


@dataclass
class SimulationSummary:
    total_transactions_simulated: int
    allow_count: int
    review_count: int
    block_count: int
    allow_rate_pct: float
    review_rate_pct: float
    block_rate_pct: float
    estimated_fraud_capture_pct: float
    average_risk_score: float
    tested_model: str
    applied_threshold: float
    simulation_timestamp: str
    simulation_mode: str = "SIMULATION_ANALYSIS_ZERO_DB_MUTATION"


class BacktestService:
    """Simulates pre-auth decisioning policies against historical data."""

    @classmethod
    def run_historical_replay(
        cls,
        db: Session,
        sample_size: int = 100,
        candidate_threshold: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Execute safe read-only simulation over historical transactions.
        Guarantees zero database modifications.
        """
        transactions = (
            db.query(Transaction)
            .order_by(Transaction.created_at.desc())
            .limit(sample_size)
            .all()
        )

        if not transactions:
            return {
                "message": "No historical transactions found for simulation.",
                "total_simulated": 0,
            }

        pred_service = FraudPredictionService.get_instance()
        threshold = candidate_threshold if candidate_threshold is not None else pred_service.threshold

        allow_cnt = 0
        review_cnt = 0
        block_cnt = 0
        total_scores = 0.0
        caught_frauds = 0
        total_historical_frauds = 0

        simulated_records = []

        for tx in transactions:
            # 1. Feature synthesis
            amount = float(tx.amount) if tx.amount else 100.0
            category = tx.merchant_category or "retail"
            dev_type = tx.device_type or "web"
            loc = tx.geo_location_region or "US"
            country = tx.transaction_country or "US"
            tx_type = tx.transaction_type or "online_payment"

            features = BehaviorProfileService.derive_pre_auth_features(
                db=db,
                customer_id=tx.customer_id,
                amount=amount,
                merchant_category=category,
                device_type=dev_type,
                location=loc,
                transaction_country=country,
                transaction_type=tx_type,
                current_timestamp=tx.created_at,
            )

            # 2. ML Probability
            ml_prob = float(tx.fraud_probability) if tx.fraud_probability is not None else 0.1

            # 3. Rule Evaluation
            rule_res = RuleEngine.evaluate(features=features, merchant_name="Replay", ml_fraud_prob=ml_prob)

            # 4. Risk Scoring
            risk_calc = RiskScoringEngine()
            model_input_dict = {
                "Amount": amount,
                "Average_Previous_Amount": features.historical_avg_amount,
                "Amount_to_Average_Ratio": features.amount_ratio,
                "Transaction_Hour": features.transaction_hour,
                "Account_Age_Days": features.account_age_days,
                "Velocity_1h": features.velocity_1h,
                "Velocity_24h": features.velocity_24h,
                "Failed_Attempts_Count": features.failed_attempts,
                "Is_New_Device": int(features.is_new_device),
                "Is_Unusual_Location": int(features.is_unusual_location),
                "Is_International": int(features.is_international),
                "Is_Night_Transaction": int(features.is_night_transaction),
                "Merchant_Category": category,
                "Device_Type": dev_type,
                "Transaction_Type": tx_type,
                "Transaction_Country": country,
                "Geo_Location_Region": loc,
            }
            score_res = risk_calc.compute_risk_score(fraud_probability=ml_prob, transaction_data=model_input_dict)
            base_score = score_res.risk_score

            # Apply rule floors
            if rule_res.hard_block:
                final_score = max(base_score, 80)
            elif rule_res.recommended_action == RuleActionImpact.FLAG_REVIEW:
                final_score = max(base_score, 40)
            else:
                final_score = base_score

            final_score = min(100, max(0, int(round(final_score))))
            total_scores += final_score

            # 5. Simulated Decision
            if rule_res.hard_block or final_score >= 71 or ml_prob >= threshold:
                sim_decision = "BLOCK"
                block_cnt += 1
            elif rule_res.recommended_action == RuleActionImpact.FLAG_REVIEW or final_score >= 31:
                sim_decision = "REVIEW"
                review_cnt += 1
            else:
                sim_decision = "ALLOW"
                allow_cnt += 1

            is_actual_fraud = (tx.prediction == 1)
            if is_actual_fraud:
                total_historical_frauds += 1
                if sim_decision in ("BLOCK", "REVIEW"):
                    caught_frauds += 1

            simulated_records.append({
                "transaction_id": tx.transaction_id,
                "customer_id": tx.customer_id,
                "amount": amount,
                "simulated_score": final_score,
                "simulated_decision": sim_decision,
                "actual_historical_prediction": tx.prediction,
            })

        n = len(transactions)
        summary = SimulationSummary(
            total_transactions_simulated=n,
            allow_count=allow_cnt,
            review_count=review_cnt,
            block_count=block_cnt,
            allow_rate_pct=round((allow_cnt / n) * 100.0, 2),
            review_rate_pct=round((review_cnt / n) * 100.0, 2),
            block_rate_pct=round((block_cnt / n) * 100.0, 2),
            estimated_fraud_capture_pct=round((caught_frauds / total_historical_frauds * 100.0), 2) if total_historical_frauds > 0 else 100.0,
            average_risk_score=round(total_scores / n, 2),
            tested_model=pred_service.model_name,
            applied_threshold=threshold,
            simulation_timestamp=datetime.now(timezone.utc).isoformat(),
        )

        return {
            "summary": summary.__dict__,
            "sample_simulated_items": simulated_records[:10],
            "mode": "SIMULATION_ANALYSIS_READ_ONLY",
        }
