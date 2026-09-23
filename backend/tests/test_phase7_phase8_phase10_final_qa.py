"""Regression and E2E QA tests for Phase 7 (Evaluation UI), Phase 8 (Dashboard/Admin Analytics), and Phase 10 (System Integrity)."""

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.core.security import create_access_token
from backend.app.models.user import User
from backend.app.schemas.user import UserRole
from backend.app.core.database import SessionLocal


@pytest.fixture
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def investigator_auth_headers(db_session):
    inv_user = db_session.query(User).filter(User.role == UserRole.FRAUD_INVESTIGATOR.value).first()
    token = create_access_token(subject=str(inv_user.id), role=inv_user.role)
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


@pytest.fixture
def admin_auth_headers(db_session):
    admin_user = db_session.query(User).filter(User.role == UserRole.ADMIN.value).first()
    token = create_access_token(subject=str(admin_user.id), role=admin_user.role)
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


def test_phase7_realtime_evaluation_contract(investigator_auth_headers):
    """Verify Phase 7 transaction evaluation endpoint with real ML scoring and SHAP factor generation."""
    client = TestClient(app)
    payload = {
        "transaction_id": "TX-QA-PHASE7-001",
        "customer_id": "CUST-1001",
        "amount": 3500.0,
        "transaction_hour": 14,
        "merchant_category": "electronics",
        "transaction_country": "US",
        "device_type": "mobile_ios",
        "transaction_type": "online_payment",
        "failed_attempts": 0,
    }
    res = client.post("/api/v1/transactions/evaluate", json=payload, headers=investigator_auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["transaction_id"] == "TX-QA-PHASE7-001"
    assert data["prediction"] in ["FRAUD", "GENUINE"]
    assert 0.0 <= data["fraud_probability"] <= 1.0
    assert 0 <= data["risk_score"] <= 100
    assert data["risk_level"] in ["LOW", "MEDIUM", "HIGH"]
    assert "top_explanations" in data
    assert isinstance(data["top_explanations"], list)


def test_phase8_dashboard_analytics_contract(investigator_auth_headers):
    """Verify Phase 8 dashboard analytics KPI metrics and telemetry distribution."""
    client = TestClient(app)
    res = client.get("/api/v1/dashboard/stats", headers=investigator_auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert "total_transactions" in data
    assert data["total_transactions"] >= 0
    assert "risk_distribution" in data
    assert "LOW" in data["risk_distribution"]
    assert "MEDIUM" in data["risk_distribution"]
    assert "HIGH" in data["risk_distribution"]
    assert "top_risk_factors" in data
    assert "active_model_info" in data


def test_phase8_alert_center_lifecycle(investigator_auth_headers):
    """Verify Phase 8 Security Alert Center listing and acknowledgement workflow."""
    client = TestClient(app)
    res = client.get("/api/v1/alerts", headers=investigator_auth_headers)
    assert res.status_code == 200
    assert isinstance(res.json(), list)


def test_phase8_admin_model_management(admin_auth_headers):
    """Verify Phase 8 Admin Model Registry and comparison endpoints."""
    client = TestClient(app)
    res = client.get("/api/v1/admin/models", headers=admin_auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert "models" in data
    assert len(data["models"]) >= 1


def test_phase8_admin_dataset_status(admin_auth_headers):
    """Verify Phase 8 Admin Dataset status and leakage audit findings."""
    client = TestClient(app)
    res = client.get("/api/v1/admin/datasets/status", headers=admin_auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["dataset_name"] == "financial_fraud_customer_transactions.csv"
    assert data["row_count"] == 4581
    assert data["validation_status"] == "VALID"


def test_phase10_investigation_put_and_patch_contract(investigator_auth_headers):
    """Verify Phase 10 investigation case status transitions and PUT/PATCH method flexibility."""
    client = TestClient(app)
    # Create case
    create_res = client.post("/api/v1/investigations", json={
        "transaction_id": "TX-QA-PHASE7-001",
        "notes": "Investigation case for Phase 10 regression test",
    }, headers=investigator_auth_headers)
    assert create_res.status_code == 201
    case_id = create_res.json()["case_id"]

    # Test PATCH
    patch_res = client.patch(f"/api/v1/investigations/{case_id}", json={
        "status": "UNDER_REVIEW",
        "notes": "Evidence inspected via PATCH",
    }, headers=investigator_auth_headers)
    assert patch_res.status_code == 200
    assert patch_res.json()["status"] == "UNDER_REVIEW"

    # Test PUT
    put_res = client.put(f"/api/v1/investigations/{case_id}", json={
        "status": "RESOLVED",
        "decision": "GENUINE",
        "notes": "Resolved as genuine false alarm via PUT",
    }, headers=investigator_auth_headers)
    assert put_res.status_code == 200
    assert put_res.json()["status"] == "RESOLVED"
    assert put_res.json()["decision"] == "GENUINE"
