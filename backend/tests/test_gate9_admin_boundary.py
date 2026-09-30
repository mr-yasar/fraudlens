"""Verification Gate 9 - Admin Boundary & Assist-Only Actions Check (Phases 25-27).

Tests:
1. Admin & Investigator role authorization for 4-model telemetry and sub-4ms latency.
2. Strict rejection of admin telemetry when accessed by customer personas.
3. FinCEN/FIU SAR narrative generation for forensic investigations.
4. Assist-only action proposals: requires UI confirmation and prevents direct chat execution.
"""

import pytest
from unittest.mock import MagicMock
from backend.app.services.assistant_identity_service import AssistantIdentity, ROLE_ADMIN, ROLE_INVESTIGATOR, ROLE_CUSTOMER
from backend.app.services.assistant_admin_service import (
    get_admin_system_telemetry,
    get_comparative_customer_profiles,
    generate_regulatory_sar_narrative,
    propose_investigator_action,
)


@pytest.fixture
def admin_identity():
    return AssistantIdentity(
        user_id=1,
        email="admin@fraudlens.internal",
        name="Platform Admin",
        role=ROLE_ADMIN,
        customer_id=None,
        is_admin=True,
        is_investigator=False,
        is_customer=False,
        authorized_scope="GLOBAL_SYSTEM",
        account_number_masked="•••• 0000",
    )


@pytest.fixture
def investigator_identity():
    return AssistantIdentity(
        user_id=2,
        email="analyst@fraudlens.internal",
        name="SOC Analyst",
        role=ROLE_INVESTIGATOR,
        customer_id=None,
        is_admin=False,
        is_investigator=True,
        is_customer=False,
        authorized_scope="FORENSIC_INVESTIGATION",
        account_number_masked="•••• 0000",
    )


@pytest.fixture
def customer_identity():
    return AssistantIdentity(
        user_id=10,
        email="monisha@fraudlens.com",
        name="Monisha",
        role=ROLE_CUSTOMER,
        customer_id="CUST_MONISHA_001",
        is_admin=False,
        is_investigator=False,
        is_customer=True,
        authorized_scope="OWN_CUSTOMER_DATA",
        account_number_masked="•••• 4821",
    )


def test_admin_and_investigator_telemetry_access(admin_identity, investigator_identity):
    """
    Verification Gate 9 - Test 1:
    Admin and Investigator roles have access to 4-model ensemble metrics and sub-4ms latency.
    """
    # Admin telemetry
    admin_telemetry = get_admin_system_telemetry(admin_identity)
    assert "models" in admin_telemetry
    assert "xgboost" in admin_telemetry["models"]
    assert admin_telemetry["models"]["xgboost"]["roc_auc"] > 0.99
    assert admin_telemetry["sub_4ms_sla_compliant"] is True

    # Investigator telemetry
    inv_telemetry = get_admin_system_telemetry(investigator_identity)
    assert "models" in inv_telemetry
    assert inv_telemetry["champion_model"] == "XGBoost"


def test_customer_denied_admin_telemetry(customer_identity):
    """
    Verification Gate 9 - Test 2:
    Customer personas must be strictly denied access to system telemetry and comparative baselines.
    """
    res = get_admin_system_telemetry(customer_identity)
    assert "error" in res
    assert res["error"] == "UNAUTHORIZED_ROLE"

    res_comp = get_comparative_customer_profiles(customer_identity)
    assert "error" in res_comp
    assert res_comp["error"] == "UNAUTHORIZED_ROLE"


def test_regulatory_sar_narrative_generation(investigator_identity):
    """
    Verification Gate 9 - Test 3:
    Investigator can generate standardized FinCEN/FIU SAR narrative containing required sections.
    """
    mock_db = MagicMock()
    mock_tx = MagicMock()
    mock_tx.amount = 75000.0
    mock_tx.merchant_name = "Offshore Crypto Exchange"
    mock_tx.customer_id = "CUST_FLAGGED_001"
    mock_db.query.return_value.filter.return_value.first.return_value = mock_tx

    sar = generate_regulatory_sar_narrative(
        transaction_id="TX_SUSPECT_9001",
        case_reference="CASE_2026_0930_01",
        db=mock_db,
        identity=investigator_identity,
    )

    assert sar["success"] is True
    assert "narrative" in sar
    assert "SUSPICIOUS ACTIVITY REPORT" in sar["narrative"]
    assert "SUBJECT IDENTIFICATION" in sar["narrative"]
    assert "TREESHAP EXPLAINABILITY" in sar["narrative"]
    assert sar["is_assist_only"] is True


def test_assist_only_action_proposal(investigator_identity):
    """
    Verification Gate 9 - Test 4:
    Proposed enforcement actions must require UI modal confirmation and never execute directly in chat.
    """
    prop = propose_investigator_action(
        action_type="FREEZE_CUSTOMER_ACCOUNT",
        target_id="CUST_BURST_88",
        reason="Velocity burst exceeding thresholds",
        identity=investigator_identity,
    )

    assert prop["success"] is True
    assert prop["proposal"]["requires_ui_confirmation"] is True
    assert prop["proposal"]["target_modal"] == "AccountSecurityModal"
    assert "open the AccountSecurityModal" in prop["guidance_message"]
    assert prop["is_assist_only"] is True
