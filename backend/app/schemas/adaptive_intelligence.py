"""Schemas for Adaptive Fraud Threat Intelligence & Federated Learning Simulation (Phase 2)."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ThreatPatternItem(BaseModel):
    pattern_id: str
    detection_time: str
    pattern_name: str
    pattern_type: str
    affected_segment: str
    evidence: List[str]
    severity: str = Field(description="LOW, MEDIUM, HIGH, CRITICAL")
    confidence: float = Field(ge=0.0, le=1.0)
    status: str = Field(description="NEW, UNDER_REVIEW, CONFIRMED, DISMISSED, MONITORED")
    sample_transaction_ids: List[str] = []


class ThreatIntelligenceSummary(BaseModel):
    total_patterns_detected: int
    active_threats: int
    critical_threats: int
    emerging_patterns: List[ThreatPatternItem]
    model_drift_status: str
    drift_score: float
    feature_drift_indicators: Dict[str, float]
    summary_timestamp: str


class RuleEffectivenessItem(BaseModel):
    rule_id: str
    rule_name: str
    category: str
    total_hits: int
    confirmed_fraud_hits: int
    confirmed_legitimate_hits: int
    false_positive_rate: float
    effectiveness_score: float
    status: str
    recommendation: str


class CandidateRuleCreate(BaseModel):
    rule_id: str
    rule_name: str
    condition_description: str
    category: str
    proposed_action: str
    rationale: str


class CandidateRuleItem(BaseModel):
    rule_id: str
    rule_name: str
    condition_description: str
    category: str
    proposed_action: str
    rationale: str
    status: str = "CANDIDATE"  # CANDIDATE, APPROVED, REJECTED, ACTIVE
    created_at: str
    created_by: str = "System Adaptive Intelligence"


class FederatedInstitutionMetrics(BaseModel):
    institution_id: str
    institution_name: str
    local_sample_count: int
    local_fraud_rate_pct: float
    local_precision: float
    local_recall: float
    local_f1: float
    local_pr_auc: float
    weight_update_norm: float
    data_privacy_status: str = "ZERO_RAW_DATA_SHARED (LOCAL BOUNDARY PRESERVED)"


class FederatedSimulationResponse(BaseModel):
    simulation_id: str
    simulation_mode: str = "FEDERATED_LEARNING_SIMULATION"
    aggregation_strategy: str = "Federated Averaging (FedAvg)"
    rounds_completed: int
    participating_institutions: List[FederatedInstitutionMetrics]
    global_candidate_metrics: Dict[str, Any]
    champion_comparison: Dict[str, Any]
    privacy_guarantee: Dict[str, Any]
    challenger_eligible: bool
    status: str
    timestamp: str


class ModelGovernanceAction(BaseModel):
    model_name: str
    version: str
    action: str = Field(description="APPROVE, REJECT, PROMOTE, ROLLBACK")
    reason: str
    approval_notes: Optional[str] = None


class FeedbackOutcomeRecord(BaseModel):
    transaction_id: str
    prediction_probability: float
    system_decision: str
    investigator_decision: str
    verified_label: str
    recorded_at: str
    feedback_notes: Optional[str] = None
