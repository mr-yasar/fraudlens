"""Database initialization and initial user seeding utilities."""

from sqlalchemy.orm import Session
from backend.app.core.config import settings
from backend.app.core.database import SessionLocal, engine, Base
from backend.app.core.security import get_password_hash
from backend.app.models.user import User
from backend.app.schemas.user import UserRole


def init_db(db: Session) -> None:
    """Initialize database tables and create default administrator and investigator accounts if not existing."""
    Base.metadata.create_all(bind=engine)

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

    # 3. Seed Initial Customer Profiles if empty
    from backend.app.models.customer import Customer
    from backend.app.models.transaction import Transaction
    from backend.app.models.investigation import Investigation
    from backend.app.models.audit_log import AuditLog

    if db.query(Customer).count() == 0:

        c1 = Customer(customer_id="CUST-1001", account_age_days=180)
        c2 = Customer(customer_id="CUST-1002", account_age_days=45)
        c3 = Customer(customer_id="CUST-1003", account_age_days=12)
        db.add_all([c1, c2, c3])
        db.commit()

        # 4. Seed Initial Transactions
        t1 = Transaction(
            transaction_id="TX-2026-001",
            customer_id="CUST-1001",
            amount=42.50,
            transaction_hour=14,
            merchant_category="grocery",
            transaction_country="US",
            device_type="mobile_ios",
            transaction_type="POS",
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
            device_type="desktop_windows",
            transaction_type="ONLINE",
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
            device_type="unknown",
            transaction_type="ONLINE",
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
            status="OPEN",
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
        print("Database initialized and default accounts verified.")
    finally:
        db.close()
