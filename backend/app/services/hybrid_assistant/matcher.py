"""Semantic Intent Matcher, Confidence Scoring, and Negative Collision Prevention.

Implements Phase 08 of the 24-Phase Chatbot Remodel:
- Token overlap, Levenshtein/Jaccard similarity, and keyword weighting
- Multi-example matching against curated intents in predefined_library
- Negative example collision rejection
- Calibrated confidence scoring (High >= 0.72, Medium 0.50 - 0.71, Low < 0.50)
- Short query special handling ("risk?", "what is shap?", "why high?")
"""

import math
import re
from typing import Dict, List, Optional, Tuple
from backend.app.services.hybrid_assistant.taxonomy import (
    ConfidenceBand,
    IntentCandidate,
    PredefinedAnswerRecord,
)
from backend.app.services.hybrid_assistant.normalizer import normalize_query_text
from backend.app.services.hybrid_assistant.predefined_library import LIBRARY, get_all_predefined_records


# Direct short-query fast-path index
SHORT_QUERY_MAP = {
    "risk?": "WHAT_IS_RISK_SCORE",
    "risk": "WHAT_IS_RISK_SCORE",
    "what is risk": "WHAT_IS_RISK_SCORE",
    "what is risk score": "WHAT_IS_RISK_SCORE",
    "why high?": "WHAT_IS_HIGH_RISK",
    "why high": "WHAT_IS_HIGH_RISK",
    "why is this high risk": "WHAT_IS_HIGH_RISK",
    "what is shap": "WHAT_IS_SHAP",
    "what is shap?": "WHAT_IS_SHAP",
    "what is shapp": "WHAT_IS_SHAP",
    "shap?": "WHAT_IS_SHAP",
    "shap": "WHAT_IS_SHAP",
    "how admin works": "PURPOSE_OF_ADMIN_MODULE",
    "how admin works?": "PURPOSE_OF_ADMIN_MODULE",
    "how investigator works": "FRAUD_INVESTIGATOR_ROLE",
    "how investigator works?": "FRAUD_INVESTIGATOR_ROLE",
    "what is fraudlens": "WHAT_IS_FRAUDLENS",
    "what is fraudlens ai": "WHAT_IS_FRAUDLENS",
    "what is fraudlens?": "WHAT_IS_FRAUDLENS",
    "what is financial fraud": "WHAT_IS_FINANCIAL_FRAUD",
    "what is financial fraud?": "WHAT_IS_FINANCIAL_FRAUD",
    "otp?": "OTP_STEPUP_THRESHOLD_EXPLANATION",
    "why otp": "OTP_STEPUP_THRESHOLD_EXPLANATION",
    "why otp?": "OTP_STEPUP_THRESHOLD_EXPLANATION",
}


def _tokenize(text: str) -> List[str]:
    """Split text into normalized tokens, stripping non-alphanumeric punctuation."""
    clean = re.sub(r"[^\w\s-]", "", text.lower())
    return [t for t in clean.split() if t]


def _compute_jaccard_similarity(tokens_a: List[str], tokens_b: List[str]) -> float:
    """Compute token Jaccard similarity between two token lists."""
    if not tokens_a or not tokens_b:
        return 0.0
    set_a = set(tokens_a)
    set_b = set(tokens_b)
    intersection = len(set_a.intersection(set_b))
    union = len(set_a.union(set_b))
    return float(intersection) / float(union) if union > 0 else 0.0


def _compute_containment(query_tokens: List[str], target_tokens: List[str]) -> float:
    """Calculate the fraction of query tokens contained in target tokens."""
    if not query_tokens or not target_tokens:
        return 0.0
    q_set = set(query_tokens)
    t_set = set(target_tokens)
    common = len(q_set.intersection(t_set))
    return float(common) / float(len(q_set))


def score_query_against_record(norm_query: str, record: PredefinedAnswerRecord) -> float:
    """Score a normalized query against an answer record across examples, synonyms, and negative collisions."""
    query_tokens = _tokenize(norm_query)
    if not query_tokens:
        return 0.0

    best_score = 0.0

    # 1. Check exact phrase matches in examples or synonyms
    for ex in record.examples:
        norm_ex = normalize_query_text(ex)
        if norm_query == norm_ex:
            return 1.0
        # Substring / exact containment
        if norm_query in norm_ex or norm_ex in norm_query:
            best_score = max(best_score, 0.90)
        # Jaccard token score
        ex_tokens = _tokenize(norm_ex)
        jaccard = _compute_jaccard_similarity(query_tokens, ex_tokens)
        containment = _compute_containment(query_tokens, ex_tokens)
        combined = (jaccard * 0.5) + (containment * 0.5)
        best_score = max(best_score, combined)

    # 2. Check synonyms
    for syn in record.synonyms:
        norm_syn = normalize_query_text(syn)
        if norm_query == norm_syn:
            return 0.98
        if norm_syn in norm_query:
            best_score = max(best_score, 0.88)
        syn_tokens = _tokenize(norm_syn)
        jaccard = _compute_jaccard_similarity(query_tokens, syn_tokens)
        best_score = max(best_score, jaccard * 0.85)

    # 3. Check tags
    tag_matches = sum(1 for t in record.tags if t in norm_query)
    if tag_matches > 0:
        best_score = max(best_score, min(0.40 + (tag_matches * 0.15), 0.70))

    # 4. Check negative collisions: if query matches a negative example, penalize heavily
    for neg in record.negative_examples:
        norm_neg = normalize_query_text(neg)
        neg_tokens = _tokenize(norm_neg)
        neg_sim = _compute_jaccard_similarity(query_tokens, neg_tokens)
        if neg_sim > 0.65 or norm_query == norm_neg:
            # Severe collision penalty
            best_score = best_score * 0.35

    return min(round(best_score, 3), 1.0)


def match_intent(
    query: str,
    threshold: float = 0.72,
) -> Optional[Tuple[PredefinedAnswerRecord, IntentCandidate]]:
    """Find the best matching predefined answer record for a user query."""
    norm_query = normalize_query_text(query)
    if not norm_query:
        return None

    # Check direct short query map
    clean_stripped = norm_query.strip(" ?.").lower()
    if norm_query in SHORT_QUERY_MAP or clean_stripped in SHORT_QUERY_MAP:
        intent_key = SHORT_QUERY_MAP.get(norm_query) or SHORT_QUERY_MAP.get(clean_stripped)
        record = LIBRARY.get(intent_key)
        if record:
            cand = IntentCandidate(
                intent_name=record.intent,
                confidence=0.99,
                score_breakdown={"short_map_hit": 1.0},
                matched_phrase=norm_query,
            )
            return (record, cand)

    best_record: Optional[PredefinedAnswerRecord] = None
    best_candidate: Optional[IntentCandidate] = None
    highest_score = 0.0

    for record in get_all_predefined_records():
        score = score_query_against_record(norm_query, record)
        if score > highest_score:
            highest_score = score
            best_record = record
            best_candidate = IntentCandidate(
                intent_name=record.intent,
                confidence=score,
                score_breakdown={"jaccard_containment": score},
                matched_phrase=norm_query,
            )

    if best_record and highest_score >= threshold:
        return (best_record, best_candidate)

    return None


def get_confidence_band(score: float) -> ConfidenceBand:
    """Classify confidence score into calibrated bands."""
    if score >= 0.72:
        return ConfidenceBand.HIGH
    elif score >= 0.50:
        return ConfidenceBand.MEDIUM
    return ConfidenceBand.LOW
