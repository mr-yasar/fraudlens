"""
Security & Hardening Audit Test Suite (Phases 33, 34, 35, 36, 54).
Validates authentication, RBAC, token tampering, SQL injection resilience, rate limiting, and sensitive data safety.
"""

import time
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.core.security import create_access_token
from backend.app.core.rate_limiter import limiter
from backend.app.core.database import SessionLocal
from backend.app.models.user import User

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_limiter_before_each_test():
    """Reset rate limiter state before each test."""
    limiter.reset()
    yield
    limiter.reset()


def get_test_tokens():
    """Helper to get real tokens for admin and investigator."""
    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.role == "ADMIN").first()
        investigator = db.query(User).filter(User.role == "FRAUD_INVESTIGATOR").first()

        admin_token = create_access_token(
            subject=admin.id if admin else "admin-test-id",
            role="ADMIN",
            extra_claims={"email": admin.email if admin else "admin@fraudlens.io"}
        )

        inv_token = create_access_token(
            subject=investigator.id if investigator else "inv-test-id",
            role="FRAUD_INVESTIGATOR",
            extra_claims={"email": investigator.email if investigator else "investigator@fraudlens.io"}
        )
        return admin_token, inv_token
    finally:
        db.close()


def test_unauthenticated_request_rejected():
    """Unauthenticated requests to protected endpoints must return 401 Unauthorized."""
    response = client.get("/api/v1/customers")
    assert response.status_code == 401
    assert "detail" in response.json()


def test_tampered_jwt_token_rejected():
    """Tampered JWT signature must be rejected with 401."""
    admin_token, _ = get_test_tokens()
    tampered_token = admin_token[:-6] + "XYZ123"
    response = client.get(
        "/api/v1/customers",
        headers={"Authorization": f"Bearer {tampered_token}"}
    )
    assert response.status_code == 401


def test_expired_jwt_token_rejected():
    """Expired JWT token must be rejected with 401."""
    import jwt
    from backend.app.core.config import settings
    payload = {
        "sub": "test-user",
        "role": "ADMIN",
        "exp": int(time.time()) - 3600  # 1 hour in the past
    }
    expired_token_str = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
    
    response = client.get(
        "/api/v1/customers",
        headers={"Authorization": f"Bearer {expired_token_str}"}
    )
    assert response.status_code == 401


def test_rbac_investigator_cannot_access_admin_endpoints():
    """Investigator role cannot access admin-only endpoints (403 Forbidden)."""
    _, inv_token = get_test_tokens()
    response = client.get(
        "/api/v1/admin/datasets/status",
        headers={"Authorization": f"Bearer {inv_token}"}
    )
    assert response.status_code == 403


def test_sql_injection_payload_handled_safely():
    """SQL injection payloads in queries should be sanitized by ORM without crashing."""
    admin_token, _ = get_test_tokens()
    sql_injection_payload = "1' OR '1'='1' --"
    
    response = client.get(
        f"/api/v1/customers?search={sql_injection_payload}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    # Must succeed cleanly with parameterized query returning safe list or empty
    assert response.status_code in [200, 404]
    assert "syntax error" not in response.text.lower()


def test_rate_limiter_throttling():
    """Bursting requests beyond rate limit triggers 429 Too Many Requests."""
    # Temporarily set tight limit for testing
    client_key = "test-rate-limit-key"
    
    # Allow 3 requests per 10 seconds
    for _ in range(3):
        allowed, _, _ = limiter.is_allowed(client_key, max_requests=3, window_seconds=10)
        assert allowed is True

    # 4th request must be rejected
    allowed, remaining, retry_after = limiter.is_allowed(client_key, max_requests=3, window_seconds=10)
    assert allowed is False
    assert remaining == 0
    assert retry_after > 0


def test_sensitive_payment_fields_never_returned():
    """Audit endpoint responses to ensure sensitive fields (cvv, pin, password) are absent."""
    admin_token, _ = get_test_tokens()
    response = client.get(
        "/api/v1/transactions",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    res_str = response.text.lower()
    
    # Strict safety assertions
    assert "cvv" not in res_str or '"cvv": null' in res_str or '"cvv":null' in res_str
    assert "password_hash" not in res_str
    assert "pin" not in res_str or '"pin": null' in res_str or '"pin":null' in res_str
    assert "secret_key" not in res_str
