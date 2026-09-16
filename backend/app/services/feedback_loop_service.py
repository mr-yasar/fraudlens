"""Feedback Loop and Continuous Model Quality Evaluation Service (Phase 30).

Ingests investigator case resolutions and chargeback notifications to evaluate
actual model accuracy, precision, recall, false positive rates, and drift metrics.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from backend.app.models.investigation import Investigation
from backend.app.models.transaction import Transaction
from backend.app.models.audit_log import AuditLog
from backend.app.models.payment_intent import PaymentIntent


@dataclass
class ModelPerformanceMetrics:
    total_evaluated_cases: int
    true_positives: int
    false_positives: int
    true_negatives: int
    false_negatives: int
    precision: float
    recall: float
    f1_score: float
    false_positive_rate: float
    alert_rate: float
    evaluated_at: str


class FeedbackLoopService:
    """Computes model performance metrics and tracks ground truth outcomes."""

    @classmethod
    def calculate_performance_metrics(cls, db: Session) -> ModelPerformanceMetrics:
        """
        Derives production model accuracy against resolved investigation cases.
        - Case decision 'CONFIRMED_FRAUD' -> Actual = 1
        - Case decision 'GENUINE' -> Actual = 0
        """
        resolved_cases = (
            db.query(Investigation)
            .filter(Investigation.status == "RESOLVED", Investigation.decision.isnot(None))
            .all()
        )

        tp = 0
        fp = 0
        tn = 0
        fn = 0

        for case in resolved_cases:
            tx = db.query(Transaction).filter(Transaction.transaction_id == case.transaction_id).first()
            if not tx or tx.prediction is None:
                continue

            actual = 1 if case.decision == "CONFIRMED_FRAUD" else 0
            predicted = int(tx.prediction)

            if predicted == 1 and actual == 1:
                tp += 1
            elif predicted == 1 and actual == 0:
                fp += 1
            elif predicted == 0 and actual == 0:
                tn += 1
            elif predicted == 0 and actual == 1:
                fn += 1

        total = tp + fp + tn + fn
        precision = tp / (tp + fp) if (tp + fp) > 0 else 1.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 1.0
        f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 1.0
        fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
        alert_rate = (tp + fp) / total if total > 0 else 0.0

        return ModelPerformanceMetrics(
            total_evaluated_cases=total,
            true_positives=tp,
            false_positives=fp,
            true_negatives=tn,
            false_negatives=fn,
            precision=round(precision, 4),
            recall=round(recall, 4),
            f1_score=round(f1, 4),
            false_positive_rate=round(fpr, 4),
            alert_rate=round(alert_rate, 4),
            evaluated_at=datetime.now(timezone.utc).isoformat(),
        )

    @classmethod
    def record_ground_truth(
        cls,
        db: Session,
        transaction_id: str,
        is_fraud: bool,
        source: str = "investigator_resolution",
        notes: Optional[str] = None,
        user_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Record explicit ground truth confirmation and log compliance audit event."""
        # Find or create investigation case
        case = db.query(Investigation).filter(Investigation.transaction_id == transaction_id).first()
        decision_val = "CONFIRMED_FRAUD" if is_fraud else "GENUINE"

        if case:
            case.status = "RESOLVED"
            case.decision = decision_val
            if notes:
                case.notes = (case.notes or "") + f" | Ground Truth: {notes}"
        
        # Sync PaymentIntent if exists
        intent = db.query(PaymentIntent).filter(PaymentIntent.payment_id == transaction_id).first()
        if intent:
            intent.lifecycle_status = "BLOCKED" if is_fraud else "APPROVED"

        db.add(AuditLog(
            user_id=user_id,
            action="GROUND_TRUTH_RECORDED",
            resource_type="transaction",
            resource_id=transaction_id,
            details=f"Outcome marked as {decision_val} (Source: {source})",
        ))
        db.commit()

        metrics = cls.calculate_performance_metrics(db)
        return {
            "transaction_id": transaction_id,
            "recorded_outcome": decision_val,
            "source": source,
            "current_metrics": metrics.__dict__,
        }
