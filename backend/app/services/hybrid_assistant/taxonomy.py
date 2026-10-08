"""Hybrid Fraud Investigation and Knowledge Assistant Data Taxonomy & Contracts.

Defines canonical schemas, enums, confidence thresholds, and response envelopes
aligned with the 24-Phase Chatbot Remodel specification.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class RouteType(str, Enum):
    PREDEFINED = "PREDEFINED"
    RAG = "RAG"
    LIVE_TOOL = "LIVE_TOOL"
    SAFE_FALLBACK = "SAFE_FALLBACK"
    MUTATING_BLOCKED = "MUTATING_BLOCKED"
    SECURITY_REFUSAL = "SECURITY_REFUSAL"


class ResponseCardType(str, Enum):
    DEFINITION = "definition"
    EXPLANATION = "explanation"
    INVESTIGATION_RESULT = "investigation_result"
    EVIDENCE_SUMMARY = "evidence_summary"
    RISK_BREAKDOWN = "risk_breakdown"
    NEXT_STEP = "next_step"
    GENERAL_CARD = "general"


class ConfidenceBand(str, Enum):
    HIGH = "HIGH"          # >= 0.72
    MEDIUM = "MEDIUM"      # 0.50 - 0.71
    LOW = "LOW"            # < 0.50


@dataclass
class IntentCandidate:
    intent_name: str
    confidence: float
    score_breakdown: Dict[str, float] = field(default_factory=dict)
    matched_phrase: Optional[str] = None


@dataclass
class EntityBundle:
    transaction_ids: List[str] = field(default_factory=list)
    customer_ids: List[str] = field(default_factory=list)
    customer_names: List[str] = field(default_factory=list)
    case_ids: List[str] = field(default_factory=list)
    merchant_names: List[str] = field(default_factory=list)
    amounts: List[float] = field(default_factory=list)
    risk_levels: List[str] = field(default_factory=list)
    dates: List[str] = field(default_factory=list)
    is_why_question: bool = False
    is_ranking_request: bool = False
    is_comparison_request: bool = False
    raw_entities: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PredefinedAnswerRecord:
    intent: str
    canonical_answer: str
    short_answer: str
    detailed_answer: str
    category: str
    synonyms: List[str] = field(default_factory=list)
    examples: List[str] = field(default_factory=list)
    negative_examples: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    source_refs: List[str] = field(default_factory=list)
    card_type: ResponseCardType = ResponseCardType.DEFINITION
    card_data: Optional[Dict[str, Any]] = None
    follow_up_suggestions: List[str] = field(default_factory=list)
    version: str = "1.0.0"


@dataclass
class LiveEvidenceBundle:
    transaction: Optional[Dict[str, Any]] = None
    prediction: Optional[Dict[str, Any]] = None
    fraud_probability: Optional[float] = None
    risk_score: Optional[float] = None
    risk_tier: Optional[str] = None
    shap_factors: List[Dict[str, Any]] = field(default_factory=list)
    investigation: Optional[Dict[str, Any]] = None
    customer: Optional[Dict[str, Any]] = None
    query_target: Optional[str] = None
    retrieved_at: Optional[str] = None
    error_message: Optional[str] = None


@dataclass
class AssistantResponseEnvelope:
    response_type: str                     # definition, explanation, investigation_result, etc.
    answer: str                            # human-readable markdown response
    evidence_refs: List[str]               # citation sources / record identifiers
    follow_up_suggestions: List[str]       # clickable interactive suggestions
    confidence: float                      # 0.0 - 1.0 confidence score
    source_type: RouteType                 # PREDEFINED, RAG, LIVE_TOOL, etc.
    structured_card: Optional[Dict[str, Any]] = None
    debug_routing: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "response_type": self.response_type,
            "answer": self.answer,
            "evidence_refs": self.evidence_refs,
            "follow_up_suggestions": self.follow_up_suggestions,
            "confidence": self.confidence,
            "source_type": self.source_type.value if hasattr(self.source_type, "value") else str(self.source_type),
            "structured_card": self.structured_card,
            "debug_routing": self.debug_routing,
        }
