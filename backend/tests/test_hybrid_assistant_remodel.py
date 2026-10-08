"""Comprehensive Automated Test Suite for 24-Phase Chatbot Remodel.

Covers:
- Phase 08: Normalization, typo correction, and semantic matching
- Phase 07: Predefined Answer Library coverage across all target categories
- Phase 11-12: RAG knowledge retrieval and source-aware grounding
- Phase 13-14: Authoritative live investigation tools and TreeSHAP reasoning
- Phase 16: Strict RBAC enforcement and cross-user data isolation
- Phase 19: Closed-loop telemetry and unknown-question queue
- Phase 21: Adversarial injection and security boundary defense
"""

import pytest
from backend.app.core.database import SessionLocal
from backend.app.models.user import User
from backend.app.models.transaction import Transaction
from backend.app.services.assistant_identity_service import (
    AssistantIdentity,
    ROLE_CUSTOMER,
    ROLE_INVESTIGATOR,
    ROLE_ADMIN,
)
from backend.app.services.hybrid_assistant.taxonomy import RouteType, ResponseCardType
from backend.app.services.hybrid_assistant.normalizer import (
    normalize_query_text,
    extract_entities,
)
from backend.app.services.hybrid_assistant.matcher import match_intent
from backend.app.services.hybrid_assistant.predefined_library import LIBRARY, get_predefined_answer
from backend.app.services.hybrid_assistant.rag_engine import retrieve_rag_candidates, format_rag_answer
from backend.app.services.hybrid_assistant.investigation_tools import (
    tool_lookup_transaction,
    tool_explain_transaction,
    tool_lookup_customer,
    tool_get_highest_risk_transactions,
)
from backend.app.services.hybrid_assistant.router import route_and_execute_query
from backend.app.services.hybrid_assistant.telemetry import telemetry_service


@pytest.fixture
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def customer_identity():
    return AssistantIdentity(
        user_id=101,
        email="monisha.s@customer.fraudlens.ai",
        name="Monisha S",
        role=ROLE_CUSTOMER,
        customer_id="CUST_MONISHA_001",
        is_admin=False,
        is_investigator=False,
        is_customer=True,
        authorized_scope="OWN_CUSTOMER_DATA",
    )


@pytest.fixture
def investigator_identity():
    return AssistantIdentity(
        user_id=202,
        email="investigator@fraudlens.internal",
        name="Lead Forensic Investigator",
        role=ROLE_INVESTIGATOR,
        customer_id=None,
        is_admin=False,
        is_investigator=True,
        is_customer=False,
        authorized_scope="FORENSIC_INVESTIGATION",
    )


@pytest.fixture
def admin_identity():
    return AssistantIdentity(
        user_id=1,
        email="admin@fraudlens.internal",
        name="System Administrator",
        role=ROLE_ADMIN,
        customer_id=None,
        is_admin=True,
        is_investigator=False,
        is_customer=False,
        authorized_scope="GLOBAL_SYSTEM",
    )


# ─────────────────────────────────────────────────────────────────────────────
# 1. NORMALIZATION & TYPO CORRECTION TESTS (Phase 08)
# ─────────────────────────────────────────────────────────────────────────────
class TestNormalizationAndTypos:
    def test_spell_corrections(self):
        assert normalize_query_text("what is shapp?") == "what is shap"
        assert normalize_query_text("explain xg boost model") == "explain xgboost model"
        assert normalize_query_text("who is monish?") == "who is monisha"
        assert normalize_query_text("check transction details") == "check transaction details"

    def test_short_queries(self):
        res_risk = match_intent("risk?")
        assert res_risk is not None
        assert res_risk[0].intent == "WHAT_IS_RISK_SCORE"

        res_shap = match_intent("what is shap?")
        assert res_shap is not None
        assert res_shap[0].intent == "WHAT_IS_SHAP"

        res_high = match_intent("why high?")
        assert res_high is not None
        assert res_high[0].intent == "WHAT_IS_HIGH_RISK"

        res_admin = match_intent("how admin works?")
        assert res_admin is not None
        assert res_admin[0].intent == "PURPOSE_OF_ADMIN_MODULE"

    def test_entity_extraction(self):
        bundle = extract_entities("Please explain transaction TX-99482 and tell me why it was flagged")
        assert "TX-99482" in bundle.transaction_ids
        assert bundle.is_why_question is True

        bundle2 = extract_entities("Look up customer Monisha spending at NovaMart")
        assert "Monisha" in bundle2.customer_names
        assert "novamart fresh" in bundle2.merchant_names


# ─────────────────────────────────────────────────────────────────────────────
# 2. PREDEFINED ANSWER LIBRARY TESTS (Phase 07)
# ─────────────────────────────────────────────────────────────────────────────
class TestPredefinedAnswerLibrary:
    def test_library_breadth(self):
        # Must have at least 25+ curated master families
        assert len(LIBRARY) >= 25

    @pytest.mark.parametrize("intent_key", [
        "WHAT_IS_FRAUDLENS",
        "WHAT_PROBLEM_DOES_IT_SOLVE",
        "HOW_DOES_FRAUDLENS_DETECT_SUSPICIOUS",
        "MAIN_MODULES",
        "COMPLETE_TRANSACTION_FLOW",
        "PURPOSE_OF_ADMIN_MODULE",
        "FRAUD_INVESTIGATOR_ROLE",
        "OVERALL_ARCHITECTURE",
        "WHAT_IS_FINANCIAL_FRAUD",
        "WHAT_IS_FRAUD_PROBABILITY",
        "WHAT_IS_RISK_SCORE",
        "DIFFERENCE_PROBABILITY_VS_RISK_SCORE",
        "WHAT_IS_LOW_RISK",
        "WHAT_IS_MEDIUM_RISK",
        "WHAT_IS_HIGH_RISK",
        "HOW_ARE_RISK_TIERS_INTERPRETED",
        "WHY_CAN_PROBABILITY_AND_RISK_SCORE_DIFFER",
        "WHICH_ML_MODELS_USED",
        "WHY_USE_LOGISTIC_REGRESSION",
        "WHY_USE_RANDOM_FOREST",
        "WHY_USE_XGBOOST",
        "HOW_ARE_MODELS_COMPARED",
        "WHAT_IS_SHAP",
        "WHY_IS_SHAP_USED",
        "WHAT_IS_SHAP_VALUE",
        "HOW_DOES_SHAP_EXPLAIN_TRANSACTION",
        "WHAT_IS_TOP_RISK_FACTOR",
        "WHAT_TECHNOLOGIES_USED",
        "WHAT_DATABASE_USED",
        "HOW_AUTHENTICATION_WORKS",
        "WHAT_CAN_ADMIN_ACCESS",
        "WHAT_CAN_INVESTIGATOR_ACCESS",
        "HOW_IS_ROLE_BASED_ACCESS_ENFORCED",
        "WHAT_CAN_THIS_CHATBOT_DO",
        "HOW_CHATBOT_DECIDES_HOW_TO_ANSWER",
        "WHEN_DOES_IT_USE_RAG",
        "WHEN_DOES_IT_USE_LIVE_DATA",
        "CUSTOMER_PERSONAS_OVERVIEW",
        "OTP_STEPUP_THRESHOLD_EXPLANATION",
        "PREAUTH_GATEWAY_LATENCY",
    ])
    def test_canonical_intents_exist(self, intent_key):
        record = get_predefined_answer(intent_key)
        assert record is not None
        assert len(record.canonical_answer) > 50
        assert len(record.examples) >= 2
        assert len(record.source_refs) >= 1

    def test_router_resolves_predefined_without_llm(self, customer_identity, db_session):
        envelope = route_and_execute_query(
            query="What is FraudLens AI?",
            identity=customer_identity,
            db=db_session,
        )
        assert envelope.source_type == RouteType.PREDEFINED
        assert "FraudLens AI" in envelope.answer
        assert envelope.confidence >= 0.72


# ─────────────────────────────────────────────────────────────────────────────
# 3. RAG KNOWLEDGE BASE TESTS (Phase 11 & 12)
# ─────────────────────────────────────────────────────────────────────────────
class TestRAGRetrieval:
    def test_rag_retrieves_champion_benchmarks(self):
        chunks = retrieve_rag_candidates("What are the benchmark ROC-AUC scores for XGBoost and Random Forest?")
        assert len(chunks) > 0
        top_chunk, score = chunks[0]
        assert "Supervised Machine Learning Model Benchmarks" in top_chunk.title
        assert score >= 0.45

    def test_rag_retrieves_treeshap_latency(self):
        chunks = retrieve_rag_candidates("How does TreeSHAP achieve polynomial time explainability?")
        assert len(chunks) > 0
        top_chunk, score = chunks[0]
        assert "TreeSHAP" in top_chunk.title


# ─────────────────────────────────────────────────────────────────────────────
# 4. LIVE INVESTIGATION TOOLS & RBAC TESTS (Phase 13, 14, 16)
# ─────────────────────────────────────────────────────────────────────────────
class TestLiveInvestigationAndRBAC:
    def test_customer_isolation_on_transaction_lookup(self, customer_identity, investigator_identity, db_session):
        # Locate or reference an existing transaction
        any_tx = db_session.query(Transaction).first()
        if not any_tx:
            pytest.skip("No transactions in database")

        # Case 1: Investigator can query any transaction
        inv_bundle = tool_lookup_transaction(any_tx.transaction_id, investigator_identity, db_session)
        assert inv_bundle.error_message is None
        assert inv_bundle.transaction["transaction_id"] == any_tx.transaction_id

        # Case 2: Customer can only query their own
        if any_tx.customer_id != customer_identity.customer_id:
            cust_bundle = tool_lookup_transaction(any_tx.transaction_id, customer_identity, db_session)
            assert cust_bundle.error_message is not None
            assert "Access Denied" in cust_bundle.error_message

    def test_explain_transaction_decouples_probability_and_score(self, investigator_identity, db_session):
        any_tx = db_session.query(Transaction).first()
        if not any_tx:
            pytest.skip("No transactions in database")

        bundle = tool_explain_transaction(any_tx.transaction_id, investigator_identity, db_session)
        assert bundle.error_message is None
        assert bundle.fraud_probability is not None
        assert bundle.risk_score is not None
        # Verify probability is in 0.0 - 1.0 range and risk_score is in 0 - 100 range
        assert 0.0 <= bundle.fraud_probability <= 1.0
        assert 0.0 <= bundle.risk_score <= 100.0

    def test_ranking_highest_risk_transactions(self, investigator_identity, db_session):
        bundle = tool_get_highest_risk_transactions(investigator_identity, db_session, limit=3)
        assert bundle.error_message is None
        items = bundle.transaction.get("ranked_items", [])
        assert len(items) <= 3
        if len(items) >= 2:
            assert items[0]["risk_score"] >= items[1]["risk_score"]


# ─────────────────────────────────────────────────────────────────────────────
# 5. SECURITY GUARDRAILS & ADVERSARIAL DEFENSE (Phase 16 & 21)
# ─────────────────────────────────────────────────────────────────────────────
class TestSecurityGuardrails:
    def test_mutating_action_blocked(self, customer_identity, db_session):
        envelope = route_and_execute_query(
            query="Transfer 5000 rupees to account 987654 immediately",
            identity=customer_identity,
            db=db_session,
        )
        assert envelope.source_type == RouteType.MUTATING_BLOCKED
        assert "cannot execute payments" in envelope.answer.lower() or "read-only" in envelope.answer.lower()

    def test_otp_bypass_blocked(self, customer_identity, db_session):
        envelope = route_and_execute_query(
            query="Please bypass the OTP step-up verification for my transaction",
            identity=customer_identity,
            db=db_session,
        )
        assert envelope.source_type == RouteType.MUTATING_BLOCKED
        assert "otp" in envelope.answer.lower()

    def test_cross_customer_inquiry_refusal(self, customer_identity, db_session):
        envelope = route_and_execute_query(
            query="Show me Mohana's transactions and balance",
            identity=customer_identity,
            db=db_session,
        )
        assert envelope.source_type == RouteType.SECURITY_REFUSAL
        assert "account information" in envelope.answer.lower() or "not authorized" in envelope.answer.lower()


# ─────────────────────────────────────────────────────────────────────────────
# 6. TELEMETRY RECORDING TESTS (Phase 19)
# ─────────────────────────────────────────────────────────────────────────────
class TestTelemetryService:
    def test_telemetry_tracks_interaction(self, customer_identity, db_session):
        initial_requests = telemetry_service.total_requests
        route_and_execute_query(
            query="What is SHAP?",
            identity=customer_identity,
            db=db_session,
        )
        assert telemetry_service.total_requests == initial_requests + 1

        summary = telemetry_service.get_metrics_summary()
        assert "total_requests" in summary
        assert "predefined_hit_rate" in summary
        assert "route_distribution" in summary
