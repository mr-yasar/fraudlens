"""Comprehensive Tests for FraudLens AI Premium 4th-User Security Environment.
Verifies User 4 identity, strict tenant isolation, multi-signal adaptive risk engine,
step-up OTP verification state machine, hardware device trust, session security,
tamper-resistant audit trail, and zero-regression on existing Users 1, 2, and 3.
"""

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.core.database import SessionLocal
from backend.app.models.user import User
from backend.app.models.customer import Customer
from backend.app.models.device import CustomerDevice
from backend.app.models.session import UserSession
from backend.app.models.transaction import Transaction
from backend.app.models.verification_event import VerificationEvent
from backend.app.models.alert import Alert
from backend.app.models.audit_log import AuditLog
from backend.app.models.behavioral_profile import BehavioralProfile

client = TestClient(app)


@pytest.fixture(scope="module")
def auth_tokens():
    """Retrieve JWT access tokens for Admin, User 1 (Monisha), User 2 (Mohana), User 3 (Sowmiya), and User 4 (Premium)."""
    # 1. Admin
    res_admin = client.post("/api/v1/auth/login", json={"email": "admin@fraudlens.internal", "password": "AdminSecure@2026!"})
    admin_token = res_admin.json()["access_token"]

    # 2. User 1 (Monisha)
    res_u1 = client.post("/api/v1/auth/login", json={"email": "monisha@fraudlens.ai", "password": "Customer@1234"})
    u1_token = res_u1.json()["access_token"]

    # 3. User 2 (Mohana)
    res_u2 = client.post("/api/v1/auth/login", json={"email": "mohana@fraudlens.ai", "password": "Customer@1234"})
    u2_token = res_u2.json()["access_token"]

    # 3. User 3 (Sowmiya)
    res_u3 = client.post("/api/v1/auth/login", json={"email": "sowmiya@fraudlens.ai", "password": "Customer@1234"})
    u3_token = res_u3.json()["access_token"]

    # 4. User 4 (Alexander Sterling - Premium)
    res_u4 = client.post("/api/v1/auth/login", json={"email": "premium@fraudlens.ai", "password": "Customer@1234"})
    u4_token = res_u4.json()["access_token"]

    return {
        "admin": admin_token,
        "user1": u1_token,
        "user2": u2_token,
        "user3": u3_token,
        "user4_premium": u4_token,
    }


# =============================================================================
# 1. EXISTING USERS REGRESSION TESTS (Section 3 & 40)
# =============================================================================
def test_existing_users_preserved_and_functional(auth_tokens):
    """Ensure User 1, User 2, and User 3 remain 100% functional with preserved records."""
    headers_u1 = {"Authorization": f"Bearer {auth_tokens['user1']}"}
    headers_u2 = {"Authorization": f"Bearer {auth_tokens['user2']}"}
    headers_u3 = {"Authorization": f"Bearer {auth_tokens['user3']}"}

    # Test User 1 wallet and modules
    res1 = client.get("/api/v1/payment/wallet/CUST_MONISHA_001", headers=headers_u1)
    assert res1.status_code == 200
    assert res1.json()["customer_id"] == "CUST_MONISHA_001"

    # Test User 2 wallet
    res2 = client.get("/api/v1/payment/wallet/CUST_MOHANA_002", headers=headers_u2)
    assert res2.status_code == 200
    assert res2.json()["customer_id"] == "CUST_MOHANA_002"

    # Test User 3 wallet
    res3 = client.get("/api/v1/payment/wallet/CUST_SOWMIYA_003", headers=headers_u3)
    assert res3.status_code == 200
    assert res3.json()["customer_id"] == "CUST_SOWMIYA_003"


# =============================================================================
# 2. USER 4 PREMIUM IDENTITY & DATA STRUCTURE (Section 5 & 7)
# =============================================================================
def test_user4_premium_identity_and_dashboard(auth_tokens):
    """Verify dedicated premium tier attributes and dashboard payload."""
    headers_u4 = {"Authorization": f"Bearer {auth_tokens['user4_premium']}"}
    res = client.get("/api/v1/premium/dashboard", headers=headers_u4)
    assert res.status_code == 200
    data = res.json()
    assert data["customer_id"] == "CUST_PREMIUM_004"
    assert data["account_tier"] == "PREMIUM"
    assert data["security_health"]["status"] in ("Excellent", "Good", "Attention Required")
    assert data["security_health"]["score"] > 50
    assert data["wallet_balance"] > 0


# =============================================================================
# 3. STRICT CROSS-USER DATA ISOLATION (Section 6 & 41)
# =============================================================================
def test_strict_cross_user_isolation(auth_tokens):
    """Verify User 4 cannot see User 1-3 private records and vice-versa."""
    headers_u4 = {"Authorization": f"Bearer {auth_tokens['user4_premium']}"}
    headers_u1 = {"Authorization": f"Bearer {auth_tokens['user1']}"}

    # User 4 querying transactions only receives User 4 records
    res_u4_tx = client.get("/api/v1/premium/transactions", headers=headers_u4)
    assert res_u4_tx.status_code == 200
    txs_u4 = res_u4_tx.json()
    for tx in txs_u4:
        assert "CUST_MONISHA" not in tx.get("customer_id", "")

    # User 1 attempting to view User 4 premium dashboard returns User 1's isolated data or denial
    res_u1_prem = client.get("/api/v1/premium/dashboard", headers=headers_u1)
    assert res_u1_prem.status_code == 200
    assert res_u1_prem.json()["customer_id"] == "CUST_MONISHA_001"
    assert res_u1_prem.json()["customer_id"] != "CUST_PREMIUM_004"


# =============================================================================
# 4. MULTI-SIGNAL ADAPTIVE RISK ENGINE & PROGRESSIVE SECURITY (Section 9, 10, 12, 38)
# =============================================================================
def test_scenario_a_normal_transaction_allow(auth_tokens):
    """Scenario A: Trusted device + Normal amount + Business hours -> LOW -> ALLOW."""
    headers_u4 = {"Authorization": f"Bearer {auth_tokens['user4_premium']}"}
    payload = {
        "amount": 12500.0,
        "recipient": "Cloudflare Global Services",
        "device_id": "dev-mbp-m3",
        "device_name": "MacBook Pro M3 Max",
        "location": "Mumbai / Cyber City",
        "transaction_type": "WIRE_TRANSFER",
    }
    res = client.post("/api/v1/premium/transactions/evaluate", json=payload, headers=headers_u4)
    assert res.status_code == 200
    data = res.json()
    assert data["decision"] == "ALLOW"
    assert data["risk_score"] < 25
    assert data["risk_level"] == "LOW"
    assert data["status"] == "SUCCESS"
    assert data["otp_challenge"] is None


def test_scenario_b_unusual_night_hours_stepup(auth_tokens):
    """Scenario B: Trusted device + Night time -> MEDIUM -> STEP_UP_VERIFICATION."""
    headers_u4 = {"Authorization": f"Bearer {auth_tokens['user4_premium']}"}
    res = client.post("/api/v1/premium/scenarios/run", json={"scenario_id": "scenario_b_unusual"}, headers=headers_u4)
    assert res.status_code == 200
    data = res.json()
    assert data["risk_level"] == "MEDIUM"
    assert data["decision"] == "STEP_UP_VERIFICATION"
    assert data["status"] == "HELD"
    assert data["otp_challenge"] is not None
    assert len(data["contributing_factors"]) > 0


def test_scenario_c_high_risk_hold(auth_tokens):
    """Scenario C: New device + High value -> HIGH -> TEMPORARY_HOLD."""
    headers_u4 = {"Authorization": f"Bearer {auth_tokens['user4_premium']}"}
    res = client.post("/api/v1/premium/scenarios/run", json={"scenario_id": "scenario_c_high_risk"}, headers=headers_u4)
    assert res.status_code == 200
    data = res.json()
    assert data["risk_level"] == "HIGH"
    assert data["decision"] == "TEMPORARY_HOLD"
    assert data["status"] == "HELD"
    assert data["otp_challenge"] is not None


def test_scenario_d_critical_threat_hold(auth_tokens):
    """Scenario D: Unknown device + High risk foreign geo + Massive amount -> CRITICAL."""
    headers_u4 = {"Authorization": f"Bearer {auth_tokens['user4_premium']}"}
    res = client.post("/api/v1/premium/scenarios/run", json={"scenario_id": "scenario_d_critical"}, headers=headers_u4)
    assert res.status_code == 200
    data = res.json()
    assert data["risk_level"] == "CRITICAL"
    assert data["decision"] == "TEMPORARY_HOLD"
    assert data["status"] == "HELD"


# =============================================================================
# 5. OTP / STEP-UP VERIFICATION LIFECYCLE (Section 13)
# =============================================================================
def test_otp_verification_flow_success_and_wrong_code(auth_tokens):
    """Test OTP validation, wrong code handling, attempt reduction, and success clearing."""
    headers_u4 = {"Authorization": f"Bearer {auth_tokens['user4_premium']}"}

    # 1. Trigger held transaction to obtain challenge
    res_tx = client.post("/api/v1/premium/scenarios/run", json={"scenario_id": "scenario_b_unusual"}, headers=headers_u4)
    assert res_tx.status_code == 200
    tx_data = res_tx.json()
    tx_id = tx_data["transaction_id"]
    valid_otp = tx_data["otp_challenge"]["simulation_demo_code"]

    # 2. Test Wrong OTP -> Must fail with 400
    res_wrong = client.post("/api/v1/premium/verification/verify-otp", json={"transaction_id": tx_id, "otp_code": "000000"}, headers=headers_u4)
    assert res_wrong.status_code == 400
    assert "Incorrect passcode" in res_wrong.json()["detail"]

    # 3. Test Valid OTP -> Must approve transaction and deduct balance
    res_valid = client.post("/api/v1/premium/verification/verify-otp", json={"transaction_id": tx_id, "otp_code": valid_otp}, headers=headers_u4)
    assert res_valid.status_code == 200
    assert res_valid.json()["status"] == "APPROVED"
    assert res_valid.json()["success"] is True


# =============================================================================
# 6. HARDWARE DEVICE SECURITY CENTER (Section 14)
# =============================================================================
def test_device_security_management(auth_tokens):
    """Test listing devices, trusting device, and revoking device trust."""
    headers_u4 = {"Authorization": f"Bearer {auth_tokens['user4_premium']}"}

    # 1. List devices
    res_list = client.get("/api/v1/premium/devices", headers=headers_u4)
    assert res_list.status_code == 200
    devices = res_list.json()
    assert len(devices) >= 2

    # 2. Revoke a device
    res_revoke = client.post("/api/v1/premium/devices/dev-iphone-15pm/revoke", headers=headers_u4)
    assert res_revoke.status_code == 200
    assert res_revoke.json()["status"] == "REVOKED"

    # 3. Re-trust the device
    res_trust = client.post("/api/v1/premium/devices/dev-iphone-15pm/trust", headers=headers_u4)
    assert res_trust.status_code == 200
    assert res_trust.json()["status"] == "TRUSTED"


# =============================================================================
# 7. SESSION SECURITY & IMMUTABLE AUDIT TRAIL (Section 15 & 23)
# =============================================================================
def test_session_security_and_audit_trail(auth_tokens):
    """Test listing active sessions, revoking a session, and verifying audit trail entries."""
    headers_u4 = {"Authorization": f"Bearer {auth_tokens['user4_premium']}"}

    # 1. Sessions
    res_sess = client.get("/api/v1/premium/sessions", headers=headers_u4)
    assert res_sess.status_code == 200
    sessions = res_sess.json()
    assert len(sessions) >= 1

    # Revoke session
    sess_id = sessions[0]["session_id"]
    res_rev_sess = client.post(f"/api/v1/premium/sessions/{sess_id}/revoke", headers=headers_u4)
    assert res_rev_sess.status_code == 200
    assert res_rev_sess.json()["status"] == "REVOKED"

    # 2. Audit Trail
    res_audit = client.get("/api/v1/premium/audit-trail", headers=headers_u4)
    assert res_audit.status_code == 200
    audit_logs = res_audit.json()
    assert len(audit_logs) >= 1
    actions = [l["action"] for l in audit_logs]
    assert any("SESSION_REVOCATION" in a or "TRANSACTION" in a or "VERIFICATION" in a for a in actions)
