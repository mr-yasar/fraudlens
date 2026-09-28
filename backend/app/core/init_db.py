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
from backend.app.models.session import UserSession
from backend.app.models.behavioral_profile import BehavioralProfile
from backend.app.models.alert import Alert
from backend.app.models.approval import TransactionApproval
from backend.app.models.payment_intent import PaymentIntent
from backend.app.schemas.user import UserRole

logger = logging.getLogger("fraudlens.init_db")


def _sync_sqlite_columns(db: Session) -> None:
    """Safely apply non-destructive ALTER TABLE ADD COLUMN for SQLite if missing."""
    try:
        with engine.connect() as conn:
            # Check users columns
            res = conn.execute(text("PRAGMA table_info(users);")).fetchall()
            user_cols = {row[1] for row in res}
            if "account_tier" not in user_cols:
                conn.execute(text("ALTER TABLE users ADD COLUMN account_tier VARCHAR(50) DEFAULT 'STANDARD';"))
            if "account_status" not in user_cols:
                conn.execute(text("ALTER TABLE users ADD COLUMN account_status VARCHAR(50) DEFAULT 'ACTIVE';"))

            # Check customer_devices columns
            res = conn.execute(text("PRAGMA table_info(customer_devices);")).fetchall()
            dev_cols = {row[1] for row in res}
            if "user_id" not in dev_cols:
                conn.execute(text("ALTER TABLE customer_devices ADD COLUMN user_id INTEGER;"))
            if "device_name" not in dev_cols:
                conn.execute(text("ALTER TABLE customer_devices ADD COLUMN device_name VARCHAR(150);"))
            if "os" not in dev_cols:
                conn.execute(text("ALTER TABLE customer_devices ADD COLUMN os VARCHAR(100);"))
            if "browser" not in dev_cols:
                conn.execute(text("ALTER TABLE customer_devices ADD COLUMN browser VARCHAR(100);"))
            if "trust_score" not in dev_cols:
                conn.execute(text("ALTER TABLE customer_devices ADD COLUMN trust_score INTEGER DEFAULT 100;"))
            if "status" not in dev_cols:
                conn.execute(text("ALTER TABLE customer_devices ADD COLUMN status VARCHAR(50) DEFAULT 'ACTIVE';"))

            # Check alerts columns
            res = conn.execute(text("PRAGMA table_info(alerts);")).fetchall()
            alert_cols = {row[1] for row in res}
            if "user_id" not in alert_cols:
                conn.execute(text("ALTER TABLE alerts ADD COLUMN user_id INTEGER;"))
            if "customer_id" not in alert_cols:
                conn.execute(text("ALTER TABLE alerts ADD COLUMN customer_id VARCHAR(100);"))
            if "title" not in alert_cols:
                conn.execute(text("ALTER TABLE alerts ADD COLUMN title VARCHAR(200);"))
            if "status" not in alert_cols:
                conn.execute(text("ALTER TABLE alerts ADD COLUMN status VARCHAR(50) DEFAULT 'OPEN';"))
            if "resolved_at" not in alert_cols:
                conn.execute(text("ALTER TABLE alerts ADD COLUMN resolved_at DATETIME;"))

            # Check audit_logs columns
            res = conn.execute(text("PRAGMA table_info(audit_logs);")).fetchall()
            audit_cols = {row[1] for row in res}
            if "entity" not in audit_cols:
                conn.execute(text("ALTER TABLE audit_logs ADD COLUMN entity VARCHAR(100);"))
            if "entity_id" not in audit_cols:
                conn.execute(text("ALTER TABLE audit_logs ADD COLUMN entity_id VARCHAR(100);"))
            if "ip_address" not in audit_cols:
                conn.execute(text("ALTER TABLE audit_logs ADD COLUMN ip_address VARCHAR(50);"))
            if "device_id" not in audit_cols:
                conn.execute(text("ALTER TABLE audit_logs ADD COLUMN device_id VARCHAR(100);"))
            if "result" not in audit_cols:
                conn.execute(text("ALTER TABLE audit_logs ADD COLUMN result VARCHAR(50) DEFAULT 'SUCCESS';"))

            # Check customers columns
            res = conn.execute(text("PRAGMA table_info(customers);")).fetchall()
            cust_cols = {row[1] for row in res}
            if "simulated_balance" not in cust_cols:
                conn.execute(text("ALTER TABLE customers ADD COLUMN simulated_balance FLOAT DEFAULT 1500000.0;"))
            if "currency" not in cust_cols:
                conn.execute(text("ALTER TABLE customers ADD COLUMN currency VARCHAR(10) DEFAULT 'INR';"))
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
    """Initialize database tables and create default administrator, investigator, and customer accounts."""
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
            account_tier="ENTERPRISE",
            account_status="ACTIVE",
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
            account_tier="ENTERPRISE",
            account_status="ACTIVE",
            is_active=True,
        )
        db.add(investigator_user)
        db.commit()
        db.refresh(investigator_user)

    # 3. Seed Existing Customer 1 (Monisha)
    u_monisha = db.query(User).filter(User.email == "monisha@fraudlens.ai").first()
    if not u_monisha:
        u_monisha = User(
            name="Monisha",
            email="monisha@fraudlens.ai",
            password_hash=get_password_hash("Customer@1234"),
            role="customer",
            account_tier="STANDARD",
            account_status="ACTIVE",
            is_active=True,
        )
        db.add(u_monisha)
        db.commit()

    c_monisha = db.query(Customer).filter(Customer.customer_id == "CUST_MONISHA_001").first()
    if not c_monisha:
        c_monisha = Customer(
            customer_id="CUST_MONISHA_001",
            name="Monisha",
            email="monisha@fraudlens.ai",
            account_age_days=180,
            simulated_balance=547855.0,
            currency="INR",
            risk_segment="Standard Low Risk",
        )
        db.add(c_monisha)
        db.commit()

    # 4. Seed Existing Customer 2 (Mohana)
    u_mohana = db.query(User).filter(User.email == "mohana@fraudlens.ai").first()
    if not u_mohana:
        u_mohana = User(
            name="Mohana",
            email="mohana@fraudlens.ai",
            password_hash=get_password_hash("Customer@1234"),
            role="customer",
            account_tier="STANDARD",
            account_status="ACTIVE",
            is_active=True,
        )
        db.add(u_mohana)
        db.commit()

    c_mohana = db.query(Customer).filter(Customer.customer_id == "CUST_MOHANA_002").first()
    if not c_mohana:
        c_mohana = Customer(
            customer_id="CUST_MOHANA_002",
            name="Mohana",
            email="mohana@fraudlens.ai",
            account_age_days=90,
            simulated_balance=385000.0,
            currency="INR",
            risk_segment="Medium Velocity",
        )
        db.add(c_mohana)
        db.commit()

    # 5. Seed Existing Customer 3 (Sowmiya)
    u_sowmiya = db.query(User).filter(User.email == "sowmiya@fraudlens.ai").first()
    if not u_sowmiya:
        u_sowmiya = User(
            name="Sowmiya",
            email="sowmiya@fraudlens.ai",
            password_hash=get_password_hash("Customer@1234"),
            role="customer",
            account_tier="STANDARD",
            account_status="ACTIVE",
            is_active=True,
        )
        db.add(u_sowmiya)
        db.commit()

    c_sowmiya = db.query(Customer).filter(Customer.customer_id == "CUST_SOWMIYA_003").first()
    if not c_sowmiya:
        c_sowmiya = Customer(
            customer_id="CUST_SOWMIYA_003",
            name="Sowmiya",
            email="sowmiya@fraudlens.ai",
            account_age_days=45,
            simulated_balance=215000.0,
            currency="INR",
            risk_segment="High Threat Watch",
        )
        db.add(c_sowmiya)
        db.commit()

    # 6. Seed Premium User 4 (Ajay - Dedicated Enterprise Premium)
    u_premium = db.query(User).filter(User.email.in_(["ajay@fraudlens.ai", "premium@fraudlens.ai", "vikram.premium@fraudlens.ai"])).first()
    if not u_premium:
        u_premium = User(
            name="Ajay",
            email="ajay@fraudlens.ai",
            password_hash=get_password_hash("Customer@1234"),
            role="customer",
            account_tier="PREMIUM",
            account_status="ACTIVE",
            is_active=True,
        )
        db.add(u_premium)
        db.commit()
        db.refresh(u_premium)
    else:
        u_premium.name = "Ajay"
        u_premium.email = "ajay@fraudlens.ai"
        u_premium.account_tier = "PREMIUM"
        u_premium.account_status = "ACTIVE"
        db.commit()

    # 7. Seed Customer Priya
    u_priya = db.query(User).filter(User.email == "priya@fraudlens.ai").first()
    if not u_priya:
        u_priya = User(
            name="Priya",
            email="priya@fraudlens.ai",
            password_hash=get_password_hash("Customer@1234"),
            role="customer",
            account_tier="STANDARD",
            account_status="ACTIVE",
            is_active=True,
        )
        db.add(u_priya)
        db.commit()
        db.refresh(u_priya)
    else:
        u_priya.name = "Priya"
        u_priya.email = "priya@fraudlens.ai"
        u_priya.account_tier = "STANDARD"
        u_priya.account_status = "ACTIVE"
        db.commit()

    c_priya = db.query(Customer).filter(Customer.customer_id == "CUST_REAL_002").first()
    if not c_priya:
        c_priya = Customer(
            customer_id="CUST_REAL_002",
            name="Priya",
            email="priya@fraudlens.ai",
            account_age_days=120,
            simulated_balance=450000.0,
            currency="INR",
            risk_segment="Standard Active",
        )
        db.add(c_priya)
        db.commit()
    else:
        c_priya.name = "Priya"
        c_priya.email = "priya@fraudlens.ai"
        db.commit()

    # Database Migration: Cleanly migrate any existing CUST_PREMIUM_004 references to CUST_AJAY_004
    try:
        from backend.app.models.transaction import Transaction
        old_bp = db.query(BehavioralProfile).filter(BehavioralProfile.customer_id == "CUST_PREMIUM_004").first()
        new_bp = db.query(BehavioralProfile).filter(BehavioralProfile.customer_id == "CUST_AJAY_004").first()
        if old_bp and new_bp:
            db.delete(old_bp)
            db.commit()
        elif old_bp:
            old_bp.customer_id = "CUST_AJAY_004"
            db.commit()

        db.query(CustomerDevice).filter(CustomerDevice.customer_id == "CUST_PREMIUM_004").update({CustomerDevice.customer_id: "CUST_AJAY_004"}, synchronize_session=False)
        db.query(UserSession).filter(UserSession.customer_id == "CUST_PREMIUM_004").update({UserSession.customer_id: "CUST_AJAY_004"}, synchronize_session=False)
        db.query(Beneficiary).filter(Beneficiary.customer_id == "CUST_PREMIUM_004").update({Beneficiary.customer_id: "CUST_AJAY_004"}, synchronize_session=False)
        db.query(Alert).filter(Alert.customer_id == "CUST_PREMIUM_004").update({Alert.customer_id: "CUST_AJAY_004"}, synchronize_session=False)
        db.query(Transaction).filter(Transaction.customer_id == "CUST_PREMIUM_004").update({Transaction.customer_id: "CUST_AJAY_004"}, synchronize_session=False)
        db.commit()

        old_cust = db.query(Customer).filter(Customer.customer_id == "CUST_PREMIUM_004").first()
        new_cust = db.query(Customer).filter(Customer.customer_id == "CUST_AJAY_004").first()
        if old_cust and new_cust:
            db.delete(old_cust)
            db.commit()
        elif old_cust:
            old_cust.customer_id = "CUST_AJAY_004"
            db.commit()
    except Exception as e:
        logger.error(f"Migration error: {e}")
        db.rollback()

    c_premium = db.query(Customer).filter(Customer.customer_id == "CUST_AJAY_004").first()
    if not c_premium:
        c_premium = Customer(
            customer_id="CUST_AJAY_004",
            name="Ajay",
            email="ajay@fraudlens.ai",
            account_age_days=720,
            simulated_balance=2500000.0,
            currency="INR",
            risk_segment="Enterprise Security",
        )
        db.add(c_premium)
        db.commit()
        db.refresh(c_premium)
    else:
        c_premium.name = "Ajay"
        c_premium.email = "ajay@fraudlens.ai"
        c_premium.risk_segment = "Enterprise Security"
        db.commit()

    # Seed User 4 Devices
    dev1 = db.query(CustomerDevice).filter(CustomerDevice.device_identifier == "dev-mbp-m3").first()
    if not dev1:
        dev1 = CustomerDevice(
            user_id=u_premium.id,
            customer_id="CUST_AJAY_004",
            device_identifier="dev-mbp-m3",
            device_name="MacBook Pro M3 Max",
            device_type="desktop_macos",
            os="macOS Sonoma 14.5",
            browser="Chrome 124.0 (Encrypted Hardware Enclave)",
            browser_or_client="Chrome 124.0",
            location_region="Mumbai / Cyber City",
            is_trusted=True,
            is_compromised=False,
            trust_score=98,
            status="ACTIVE",
        )
        db.add(dev1)

    dev2 = db.query(CustomerDevice).filter(CustomerDevice.device_identifier == "dev-iphone-15pm").first()
    if not dev2:
        dev2 = CustomerDevice(
            user_id=u_premium.id,
            customer_id="CUST_AJAY_004",
            device_identifier="dev-iphone-15pm",
            device_name="iPhone 15 Pro Max",
            device_type="mobile_ios",
            os="iOS 17.5.1",
            browser="Mobile Safari (Biometric Keychain)",
            browser_or_client="Mobile Safari",
            location_region="Mumbai / Cyber City",
            is_trusted=True,
            is_compromised=False,
            trust_score=95,
            status="ACTIVE",
        )
        db.add(dev2)
    db.commit()

    # Seed User 4 Sessions
    s1 = db.query(UserSession).filter(UserSession.session_id == "sess-premium-mumbai-01").first()
    if not s1:
        s1 = UserSession(
            user_id=u_premium.id,
            customer_id="CUST_AJAY_004",
            session_id="sess-premium-mumbai-01",
            device_id="dev-mbp-m3",
            device_name="MacBook Pro M3 Max",
            ip_address="49.37.142.88",
            approximate_location="Mumbai, Maharashtra, India",
            session_status="ACTIVE",
            risk_score=5,
        )
        db.add(s1)

    s2 = db.query(UserSession).filter(UserSession.session_id == "sess-premium-blr-02").first()
    if not s2:
        s2 = UserSession(
            user_id=u_premium.id,
            customer_id="CUST_AJAY_004",
            session_id="sess-premium-blr-02",
            device_id="dev-iphone-15pm",
            device_name="iPhone 15 Pro Max",
            ip_address="106.51.72.19",
            approximate_location="Bangalore Tech Corridor, India",
            session_status="ACTIVE",
            risk_score=8,
        )
        db.add(s2)
    db.commit()

    # Seed User 4 Beneficiaries
    b_cf = db.query(Beneficiary).filter(Beneficiary.customer_id == "CUST_AJAY_004", Beneficiary.beneficiary_name == "Cloudflare Global Services").first()
    if not b_cf:
        b1 = Beneficiary(
            customer_id="CUST_AJAY_004",
            beneficiary_name="Cloudflare Global Services",
            beneficiary_account="ACCT-CF-883921",
            category="Infrastructure & Security",
            trust_score=99,
            is_trusted=True,
            total_transfers=18,
        )
        b2 = Beneficiary(
            customer_id="CUST_AJAY_004",
            beneficiary_name="AWS Enterprise Cloud",
            beneficiary_account="ACCT-AWS-991204",
            category="Cloud Computing",
            trust_score=98,
            is_trusted=True,
            total_transfers=24,
        )
        b3 = Beneficiary(
            customer_id="CUST_AJAY_004",
            beneficiary_name="Silicon Valley Tech Fund",
            beneficiary_account="ACCT-SVB-104928",
            category="Corporate Investments",
            trust_score=94,
            is_trusted=True,
            total_transfers=6,
        )
        b4 = Beneficiary(
            customer_id="CUST_AJAY_004",
            beneficiary_name="Stripe Global Settlement",
            beneficiary_account="ACCT-ST-442019",
            category="Payment Processing",
            trust_score=97,
            is_trusted=True,
            total_transfers=35,
        )
        db.add_all([b1, b2, b3, b4])
        db.commit()

    # Seed User 4 Behavioral Profile
    bp = db.query(BehavioralProfile).filter(BehavioralProfile.customer_id == "CUST_AJAY_004").first()
    if not bp:
        bp = BehavioralProfile(
            user_id=u_premium.id,
            customer_id="CUST_AJAY_004",
            normal_transaction_range="₹5,000 - ₹150,000",
            normal_transaction_frequency="2-4 transactions/day",
            common_transaction_times="08:00 - 22:00 IST",
            common_locations="Mumbai, Bangalore, Singapore",
            trusted_devices="MacBook Pro M3 Max, iPhone 15 Pro Max",
            average_transaction_amount=45000.0,
            security_score=98,
            behavioral_baseline="High-frequency enterprise settlement account with strict biometric authentication and low volatility.",
        )
        db.add(bp)
        db.commit()

    # Seed initial security alert for User 4 if none exist
    p_alert = db.query(Alert).filter(Alert.customer_id == "CUST_AJAY_004").first()
    if not p_alert:
        p_alert = Alert(
            alert_id="ALT-PREM-INIT-001",
            user_id=u_premium.id,
            customer_id="CUST_AJAY_004",
            alert_type="NEW_ENVIRONMENT_INITIALIZED",
            severity="INFO",
            title="Premium Security Environment Activated",
            message="Your account has been upgraded to Premium Tier with Real-Time Adaptive Risk Engine and Hardware Enclave Protection enabled.",
            status="ACKNOWLEDGED",
            is_acknowledged=True,
        )
        db.add(p_alert)
        db.commit()


if __name__ == "__main__":
    db = SessionLocal()
    try:
        init_db(db)
        print("Database initialized, synced and all 4 accounts verified.")
    finally:
        db.close()

