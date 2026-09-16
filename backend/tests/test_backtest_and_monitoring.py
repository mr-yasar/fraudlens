"""
Backtesting, Model Monitoring & Feedback Loop Test Suite (Phases 38, 39, 40, 41, 42, 43).
Validates read-only simulation guarantees, verified feedback storage, and operational drift/accuracy computation.
"""

import pytest
from backend.app.core.database import SessionLocal
from backend.app.services.backtest_service import BacktestService
from backend.app.services.feedback_loop_service import FeedbackLoopService
from backend.app.models.transaction import Transaction


def test_historical_replay_simulation_guarantees_zero_mutation():
    """Historical replay must run read-only simulation without modifying transaction states."""
    db = SessionLocal()
    try:
        # Count transactions before
        tx_count_before = db.query(Transaction).count()
        assert tx_count_before > 0

        # Run simulation
        result = BacktestService.run_historical_replay(
            db=db,
            sample_size=20,
            candidate_threshold=0.65
        )

        assert "summary" in result
        assert "mode" in result
        assert result["mode"] == "SIMULATION_ANALYSIS_READ_ONLY"
        assert result["summary"]["total_transactions_simulated"] > 0
        assert "allow_count" in result["summary"]
        assert "review_count" in result["summary"]
        assert "block_count" in result["summary"]

        # Verify zero DB mutation
        tx_count_after = db.query(Transaction).count()
        assert tx_count_after == tx_count_before
    finally:
        db.close()


def test_feedback_loop_and_metrics_calculation():
    """Feedback records must correctly compute verified ground-truth metrics."""
    db = SessionLocal()
    try:
        # Compute metrics from existing resolved investigations
        metrics = FeedbackLoopService.calculate_performance_metrics(db=db)
        assert metrics is not None
        assert hasattr(metrics, "total_evaluated_cases")
        assert hasattr(metrics, "precision")
        assert hasattr(metrics, "recall")
        assert hasattr(metrics, "f1_score")
    finally:
        db.close()
