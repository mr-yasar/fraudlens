"""Comprehensive tests for Phase 2 Database Architecture and SQLAlchemy Models."""

import pytest
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker

from backend.app.core.database import Base, get_db
from backend.app.models import (
    User,
    Customer,
    Transaction,
    Investigation,
    ShapExplanation,
    ModelVersion,
    AuditLog,
)


@pytest.fixture(scope="module")
def db_engine():
    """In-memory SQLite engine to test DDL schema creation and table constraints."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session(db_engine):
    """Transactional session for testing model relationships and constraints."""
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)
    session = TestingSessionLocal()
    yield session
    session.rollback()
    session.close()


def test_table_registry():
    """Verify all 7 required tables are defined in metadata."""
    expected_tables = {
        "users",
        "customers",
        "transactions",
        "investigations",
        "shap_explanations",
        "model_versions",
        "audit_logs",
    }
    actual_tables = set(Base.metadata.tables.keys())
    assert expected_tables.issubset(actual_tables), f"Missing tables: {expected_tables - actual_tables}"


def test_user_model_columns(db_engine):
    """Verify users table structure."""
    inspector = inspect(db_engine)
    columns = {col["name"]: col for col in inspector.get_columns("users")}
    expected_cols = ["id", "name", "email", "password_hash", "role", "is_active", "created_at", "updated_at"]
    for col in expected_cols:
        assert col in columns, f"Column '{col}' missing from users table"


def test_customer_model_columns(db_engine):
    """Verify customers table structure."""
    inspector = inspect(db_engine)
    columns = {col["name"]: col for col in inspector.get_columns("customers")}
    expected_cols = ["id", "customer_id", "account_age_days", "created_at"]
    for col in expected_cols:
        assert col in columns, f"Column '{col}' missing from customers table"


def test_transaction_model_columns(db_engine):
    """Verify transactions table structure."""
    inspector = inspect(db_engine)
    columns = {col["name"]: col for col in inspector.get_columns("transactions")}
    expected_cols = [
        "id",
        "transaction_id",
        "customer_id",
        "amount",
        "transaction_hour",
        "merchant_category",
        "transaction_country",
        "geo_location_region",
        "device_type",
        "transaction_type",
        "fraud_probability",
        "prediction",
        "risk_score",
        "risk_level",
        "created_at",
    ]
    for col in expected_cols:
        assert col in columns, f"Column '{col}' missing from transactions table"


def test_investigation_model_columns(db_engine):
    """Verify investigations table structure."""
    inspector = inspect(db_engine)
    columns = {col["name"]: col for col in inspector.get_columns("investigations")}
    expected_cols = ["id", "case_id", "transaction_id", "investigator_id", "status", "decision", "notes", "created_at", "updated_at"]
    for col in expected_cols:
        assert col in columns, f"Column '{col}' missing from investigations table"


def test_shap_explanation_model_columns(db_engine):
    """Verify shap_explanations table structure."""
    inspector = inspect(db_engine)
    columns = {col["name"]: col for col in inspector.get_columns("shap_explanations")}
    expected_cols = ["id", "transaction_id", "feature_name", "shap_value", "impact", "created_at"]
    for col in expected_cols:
        assert col in columns, f"Column '{col}' missing from shap_explanations table"


def test_model_version_model_columns(db_engine):
    """Verify model_versions table structure."""
    inspector = inspect(db_engine)
    columns = {col["name"]: col for col in inspector.get_columns("model_versions")}
    expected_cols = [
        "id",
        "model_name",
        "version",
        "accuracy",
        "precision",
        "recall",
        "f1_score",
        "roc_auc",
        "pr_auc",
        "model_path",
        "is_active",
        "trained_at",
    ]
    for col in expected_cols:
        assert col in columns, f"Column '{col}' missing from model_versions table"


def test_audit_log_model_columns(db_engine):
    """Verify audit_logs table structure."""
    inspector = inspect(db_engine)
    columns = {col["name"]: col for col in inspector.get_columns("audit_logs")}
    expected_cols = ["id", "user_id", "action", "resource_type", "resource_id", "details", "created_at"]
    for col in expected_cols:
        assert col in columns, f"Column '{col}' missing from audit_logs table"


def test_model_instantiation_and_relationships(db_session):
    """Test model object creation and foreign key relationship bindings."""
    # 1. Create User
    user = User(
        name="Lead Fraud Analyst",
        email="analyst@fraudlens.internal",
        password_hash="argon2_hashed_password",
        role="investigator",
        is_active=True,
    )
    db_session.add(user)
    db_session.flush()
    assert user.id is not None

    # 2. Create Customer
    customer = Customer(
        customer_id="CUST-98231",
        account_age_days=365,
    )
    db_session.add(customer)
    db_session.flush()

    # 3. Create Transaction linked to Customer
    tx = Transaction(
        transaction_id="TX-849204",
        customer_id=customer.customer_id,
        amount=1450.50,
        transaction_hour=14,
        merchant_category="Electronics",
        transaction_country="US",
        geo_location_region="CA",
        device_type="mobile",
        transaction_type="online_payment",
        fraud_probability=0.88,
        prediction=1,
        risk_score=88.5,
        risk_level="HIGH",
    )
    db_session.add(tx)
    db_session.flush()

    # 4. Create Investigation linked to Transaction and User
    investigation = Investigation(
        case_id="CASE-2026-001",
        transaction_id=tx.transaction_id,
        investigator_id=user.id,
        status="under_review",
        notes="Flagged due to unusual device and amount spike",
    )
    db_session.add(investigation)
    db_session.flush()

    # 5. Create SHAP Explanation linked to Transaction
    shap = ShapExplanation(
        transaction_id=tx.transaction_id,
        feature_name="amount",
        shap_value=0.42,
        impact="positive_risk",
    )
    db_session.add(shap)
    db_session.flush()

    # 6. Create ModelVersion
    mv = ModelVersion(
        model_name="xgboost_fraud_detector",
        version="v1.0.0",
        accuracy=0.985,
        precision=0.942,
        recall=0.918,
        f1_score=0.930,
        roc_auc=0.991,
        pr_auc=0.954,
        model_path="ml/models/xgboost_v1.joblib",
        is_active=True,
    )
    db_session.add(mv)
    db_session.flush()

    # 7. Create AuditLog linked to User
    audit = AuditLog(
        user_id=user.id,
        action="INVESTIGATION_OPENED",
        resource_type="investigation",
        resource_id=investigation.case_id,
        details="Opened investigation case for transaction TX-849204",
    )
    db_session.add(audit)
    db_session.flush()

    # Verify relationships
    db_session.commit()
    assert tx.customer.customer_id == "CUST-98231"
    assert len(tx.investigations) == 1
    assert tx.investigations[0].case_id == "CASE-2026-001"
    assert len(tx.shap_explanations) == 1
    assert tx.shap_explanations[0].feature_name == "amount"
    assert len(user.investigations) == 1
    assert len(user.audit_logs) == 1


def test_get_db_session_dependency():
    """Verify get_db generator yields an active Session."""
    db_gen = get_db()
    session = next(db_gen)
    assert session is not None
    # Clean up generator
    try:
        next(db_gen)
    except StopIteration:
        pass
