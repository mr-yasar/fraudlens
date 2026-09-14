"""Comprehensive test suite for Phase 3 Authentication & Role-Based Access Control (RBAC)."""

from datetime import timedelta
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.main import app
from backend.app.core.database import Base, get_db
from backend.app.core.security import get_password_hash, create_access_token
from backend.app.models.user import User
from backend.app.schemas.user import UserRole

# SQLite engine with StaticPool for multi-threaded TestClient sharing
test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="module", autouse=True)
def setup_test_app():
    """Setup test database tables and dependency overrides."""
    app.dependency_overrides[get_db] = override_get_db
    Base.metadata.create_all(bind=test_engine)
    db = TestingSessionLocal()

    # Seed Admin User
    admin = User(
        name="Test Admin",
        email="admin@test.internal",
        password_hash=get_password_hash("AdminPass123!"),
        role=UserRole.ADMIN.value,
        is_active=True,
    )
    # Seed Fraud Investigator User
    investigator = User(
        name="Test Investigator",
        email="investigator@test.internal",
        password_hash=get_password_hash("InvestigatorPass123!"),
        role=UserRole.FRAUD_INVESTIGATOR.value,
        is_active=True,
    )
    # Seed Inactive User
    inactive = User(
        name="Inactive User",
        email="inactive@test.internal",
        password_hash=get_password_hash("InactivePass123!"),
        role=UserRole.FRAUD_INVESTIGATOR.value,
        is_active=False,
    )
    db.add_all([admin, investigator, inactive])
    db.commit()
    db.close()

    yield

    Base.metadata.drop_all(bind=test_engine)
    app.dependency_overrides.clear()


@pytest.fixture
def client():
    return TestClient(app)


def test_login_success_admin(client):
    """Verify admin login produces valid JWT token and correct role metadata."""
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@test.internal", "password": "AdminPass123!"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["role"] == "ADMIN"
    assert data["email"] == "admin@test.internal"
    assert "password_hash" not in data


def test_login_success_investigator(client):
    """Verify investigator login produces valid JWT token."""
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "investigator@test.internal", "password": "InvestigatorPass123!"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["role"] == "FRAUD_INVESTIGATOR"
    assert "password_hash" not in data


def test_login_invalid_password(client):
    """Verify login failure with incorrect password."""
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@test.internal", "password": "WrongPassword!"},
    )
    assert response.status_code == 401
    assert "Incorrect email or password" in response.json()["detail"]


def test_login_nonexistent_user(client):
    """Verify login failure with unknown email."""
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "unknown@test.internal", "password": "SomePassword123!"},
    )
    assert response.status_code == 401


def test_login_inactive_user(client):
    """Verify inactive users are rejected."""
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "inactive@test.internal", "password": "InactivePass123!"},
    )
    assert response.status_code == 403
    assert "Inactive" in response.json()["detail"]


def test_get_me_endpoint(client):
    """Verify /me returns sanitized profile for authenticated user."""
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@test.internal", "password": "AdminPass123!"},
    )
    token = login_resp.json()["access_token"]

    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "admin@test.internal"
    assert data["name"] == "Test Admin"
    assert "password_hash" not in data


def test_missing_token(client):
    """Verify protected endpoints return 401 when token is omitted."""
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401


def test_invalid_token(client):
    """Verify malformed or invalid token returns 401."""
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer invalid.jwt.token"},
    )
    assert response.status_code == 401


def test_expired_token(client):
    """Verify expired token returns 401."""
    expired_token = create_access_token(
        subject=1,
        role="ADMIN",
        expires_delta=timedelta(hours=-1),
    )
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {expired_token}"},
    )
    assert response.status_code == 401
    assert "expired" in response.json()["detail"].lower()


def test_admin_access_to_admin_route(client):
    """Verify ADMIN role can access admin endpoints."""
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@test.internal", "password": "AdminPass123!"},
    )
    token = login_resp.json()["access_token"]

    response = client.get(
        "/api/v1/admin/system-status",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["access"] == "granted"


def test_investigator_denied_from_admin_route(client):
    """Verify FRAUD_INVESTIGATOR is denied (403 Forbidden) from admin endpoints."""
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"email": "investigator@test.internal", "password": "InvestigatorPass123!"},
    )
    token = login_resp.json()["access_token"]

    response = client.get(
        "/api/v1/admin/system-status",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403
    assert "not permitted" in response.json()["detail"].lower()


def test_investigator_access_to_investigator_route(client):
    """Verify FRAUD_INVESTIGATOR can access investigator endpoints."""
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"email": "investigator@test.internal", "password": "InvestigatorPass123!"},
    )
    token = login_resp.json()["access_token"]

    response = client.get(
        "/api/v1/investigations/cases-summary",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["access"] == "granted"


def test_admin_access_to_investigator_route(client):
    """Verify ADMIN also has access to investigator endpoints."""
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@test.internal", "password": "AdminPass123!"},
    )
    token = login_resp.json()["access_token"]

    response = client.get(
        "/api/v1/investigations/cases-summary",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["access"] == "granted"


def test_admin_create_user_success(client):
    """Verify ADMIN can create new users."""
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@test.internal", "password": "AdminPass123!"},
    )
    token = login_resp.json()["access_token"]

    response = client.post(
        "/api/v1/auth/users",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "Junior Analyst",
            "email": "junior@test.internal",
            "password": "SecurePassword123!",
            "role": "FRAUD_INVESTIGATOR",
            "is_active": True,
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "junior@test.internal"
    assert "password_hash" not in data


def test_investigator_cannot_create_user(client):
    """Verify FRAUD_INVESTIGATOR cannot create users (403 Forbidden)."""
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"email": "investigator@test.internal", "password": "InvestigatorPass123!"},
    )
    token = login_resp.json()["access_token"]

    response = client.post(
        "/api/v1/auth/users",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "Hacker",
            "email": "hacker@test.internal",
            "password": "SecurePassword123!",
            "role": "ADMIN",
            "is_active": True,
        },
    )
    assert response.status_code == 403
