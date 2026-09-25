"""Database initialization, schema synchronization, and initial user/customer seeding utilities."""

import logging
from sqlalchemy import text
from sqlalchemy.orm import Session
from backend.app.core.config import settings
from backend.app.core.database import SessionLocal, engine, Base
from backend.app.core.security import get_password_hash
from backend.app.models.user import User
from backend.app.models.customer import Customer
from backend.app.models.transaction import Transaction
from backend.app.models.investigation import Investigation
from backend.app.models.audit_log import AuditLog
from backend.app.models.beneficiary import Beneficiary
from backend.app.models.device import CustomerDevice
from backend.app.models.approval import TransactionApproval
from backend.app.models.payment_intent import PaymentIntent
from backend.app.schemas.user import UserRole

logger = logging.getLogger("fraudlens.init_db")


def _sync_sqlite_columns(db: Session) -> None:
    """Safely apply non-destructive ALTER TABLE ADD COLUMN for SQLite if missing."""
    try:
        with engine.connect() as conn:
            # Check customers columns
            res = conn.execute(text("PRAGMA table_info(customers);")).fetchall()
            cust_cols = {row[1] for row in res}
            if "simulated_balance" not in cust_cols:
                conn.execute(text("ALTER TABLE customers ADD COLUMN simulated_balance FLOAT DEFAULT 50000.0;"))
            if "currency" not in cust_cols:
                conn.execute(text("ALTER TABLE customers ADD COLUMN currency VARCHAR(10) DEFAULT 'USD';"))
            if "name" not in cust_cols:
                conn.execute(text("ALTER TABLE customers ADD COLUMN name VARCHAR(200);"))
            if "email" not in cust_cols:
                conn.execute(text("ALTER TABLE customers ADD COLUMN email VARCHAR(200);"))
            if "risk_segment" not in cust_cols:
                conn.execute(text("ALTER TABLE customers ADD COLUMN risk_segment VARCHAR(50) DEFAULT 'Standard';"))


            # Check payment_intents columns
            res = conn.execute(text("PRAGMA table_info(payment_intents);")).fetchall()
            pi_cols = {row[1] for row in res}
            if "beneficiary_name" not in pi_cols:
                conn.execute(text("ALTER TABLE payment_intents ADD COLUMN beneficiary_name VARCHAR(150);"))
            if "is_new_beneficiary" not in pi_cols:
                conn.execute(text("ALTER TABLE payment_intents ADD COLUMN is_new_beneficiary BOOLEAN DEFAULT 0;"))
            if "is_new_device" not in pi_cols:
                conn.execute(text("ALTER TABLE payment_intents ADD COLUMN is_new_device BOOLEAN DEFAULT 0;"))
            if "approval_id" not in pi_cols:
                conn.execute(text("ALTER TABLE payment_intents ADD COLUMN approval_id VARCHAR(100);"))

            # Check transactions columns
            res = conn.execute(text("PRAGMA table_info(transactions);")).fetchall()
            tx_cols = {row[1] for row in res}
            if "beneficiary" not in tx_cols:
                conn.execute(text("ALTER TABLE transactions ADD COLUMN beneficiary VARCHAR(150);"))
            if "status" not in tx_cols:
                conn.execute(text("ALTER TABLE transactions ADD COLUMN status VARCHAR(50) DEFAULT 'SUCCESS';"))
            if "approval_id" not in tx_cols:
                conn.execute(text("ALTER TABLE transactions ADD COLUMN approval_id VARCHAR(100);"))
            if "is_new_beneficiary" not in tx_cols:
                conn.execute(text("ALTER TABLE transactions ADD COLUMN is_new_beneficiary BOOLEAN DEFAULT 0;"))
            if "is_new_device" not in tx_cols:
                conn.execute(text("ALTER TABLE transactions ADD COLUMN is_new_device BOOLEAN DEFAULT 0;"))

            conn.commit()
    except Exception as exc:
        logger.debug("Schema column sync note: %s", exc)


def init_db(db: Session) -> None:
    """Initialize database tables and create default administrator and investigator accounts if not existing."""
    Base.metadata.create_all(bind=engine)
    _sync_sqlite_columns(db)

    # 1. Seed Initial Administrator Account if not present
    admin_user = db.query(User).filter(User.email == settings.INITIAL_ADMIN_EMAIL).first()
    if not admin_user:
        admin_user = User(
            name="System Administrator",
            email=settings.INITIAL_ADMIN_EMAIL,
            password_hash=get_password_hash(settings.INITIAL_ADMIN_PASSWORD),
            role=UserRole.ADMIN.value,
            is_active=True,
        )
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)

    # 2. Seed Initial Fraud Investigator Account if not present
    investigator_user = db.query(User).filter(User.email == settings.INITIAL_INVESTIGATOR_EMAIL).first()
    if not investigator_user:
        investigator_user = User(
            name="Lead Fraud Investigator",
            email=settings.INITIAL_INVESTIGATOR_EMAIL,
            password_hash=get_password_hash(settings.INITIAL_INVESTIGATOR_PASSWORD),
            role=UserRole.FRAUD_INVESTIGATOR.value,
            is_active=True,
        )
        db.add(investigator_user)
        db.commit()
        db.refresh(investigator_user)

    # 3. Seed Initial Demo Customer Account if not present
    customer_user = db.query(User).filter(User.email == "customer@fraudlens.internal").first()
    if not customer_user:
        customer_user = User(
            name="Alice Taylor (Customer)",
            email="customer@fraudlens.internal",
            password_hash=get_password_hash("Customer@2026!"),
            role=UserRole.CUSTOMER.value,
            is_active=True,
        )
        db.add(customer_user)
        db.commit()
        db.refresh(customer_user)

    # 4. Seed Initial Customer Profiles if empty
    if db.query(Customer).count() == 0:
        c1 = Customer(customer_id="CUST-1001", name="Alice Taylor", email="customer@fraudlens.internal", account_age_days=180, simulated_balance=50000.0, currency="USD")
        c2 = Customer(customer_id="CUST-1002", name="Bob Reynolds", email="bob.reynolds@example.com", account_age_days=45, simulated_balance=35000.0, currency="USD")
        c3 = Customer(customer_id="CUST-1003", name="Charlie Davis", email="charlie.davis@example.com", account_age_days=12, simulated_balance=25000.0, currency="USD")
        db.add_all([c1, c2, c3])
        db.commit()

        # Seed initial beneficiaries for CUST-1001
        b1 = Beneficiary(customer_id="CUST-1001", beneficiary_name="Whole Foods Market", category="grocery", is_trusted=True)
        b2 = Beneficiary(customer_id="CUST-1001", beneficiary_name="Alice Smith", category="family", is_trusted=True)
        b3 = Beneficiary(customer_id="CUST-1002", beneficiary_name="Best Buy Electronics", category="retail", is_trusted=True)
        db.add_all([b1, b2, b3])

        # Seed initial devices for CUST-1001
        d1 = CustomerDevice(customer_id="CUST-1001", device_identifier="dev-web-chrome-mac", device_type="web", is_trusted=True)
        d2 = CustomerDevice(customer_id="CUST-1001", device_identifier="dev-iphone-15", device_type="mobile_ios", is_trusted=True)
        db.add_all([d1, d2])

        # 4. Seed Initial Transactions
        t1 = Transaction(
            transaction_id="TX-2026-001",
            customer_id="CUST-1001",
            amount=42.50,
            transaction_hour=14,
            merchant_category="grocery",
            transaction_country="US",
            geo_location_region="CA",
            device_type="mobile_ios",
            transaction_type="POS",
            beneficiary="Whole Foods Market",
            status="SUCCESS",
            fraud_probability=0.04,
            prediction=0,
            risk_score=12.0,
            risk_level="LOW",
        )
        t2 = Transaction(
            transaction_id="TX-2026-002",
            customer_id="CUST-1002",
            amount=650.00,
            transaction_hour=18,
            merchant_category="electronics",
            transaction_country="US",
            geo_location_region="CA",
            device_type="desktop_windows",
            transaction_type="ONLINE",
            beneficiary="Best Buy Electronics",
            status="SUCCESS",
            fraud_probability=0.38,
            prediction=0,
            risk_score=45.0,
            risk_level="MEDIUM",
        )
        t3 = Transaction(
            transaction_id="TX-2026-003",
            customer_id="CUST-1003",
            amount=2850.00,
            transaction_hour=3,
            merchant_category="luxury_goods",
            transaction_country="RU",
            geo_location_region="Moscow",
            device_type="unknown",
            transaction_type="ONLINE",
            beneficiary="Apex Luxury Bullion",
            status="BLOCKED",
            fraud_probability=0.94,
            prediction=1,
            risk_score=91.0,
            risk_level="HIGH",
        )
        db.add_all([t1, t2, t3])
        db.commit()

        # 5. Seed Initial Investigation Case for High Risk Tx
        inv = Investigation(
            case_id="INV-CASE-001",
            transaction_id="TX-2026-003",
            status="open",
            decision=None,
            notes="Automated anomaly case opened for high-risk cross-border luxury transaction.",
        )
        db.add(inv)

        # 6. Seed Audit Log
        audit = AuditLog(
            user_id=admin_user.id,
            action="CREATE",
            resource_type="TRANSACTION",
            resource_id="TX-2026-003",
            details='{"amount": 2850.0, "risk_score": 91.0, "risk_level": "HIGH"}',
        )
        db.add(audit)
        db.commit()


if __name__ == "__main__":
    db = SessionLocal()
    try:
        init_db(db)
        print("Database initialized, synced and default accounts verified.")
    finally:
        db.close()
