"""Canonical Database Seed Script: Ingest 29 Master Merchants and 20,000 Synthetic Transactions."""

import os
import sys
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timezone

from backend.app.core.database import SessionLocal, engine, Base
from backend.app.core.security import get_password_hash
from backend.app.models import (
    User,
    Customer,
    Merchant,
    Transaction,
    CustomerDevice,
    Beneficiary,
    Investigation,
    AuditLog,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

CSV_PATH = os.path.join("data", "raw", "fraudlens_master_synthetic_transactions_29_merchants.csv")


def seed_database():
    logger.info("Dropping and recreating clean database schema...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # 1. Seed System Users
        logger.info("Seeding system users (Admin & Customer)...")
        users_to_seed = [
            {
                "name": "Fraud Operations Admin",
                "email": "admin@fraudlens.ai",
                "password_hash": get_password_hash("Admin@1234"),
                "role": "admin",
                "is_active": True,
            },
            {
                "name": "Senior Fraud Investigator",
                "email": "investigator@fraudlens.ai",
                "password_hash": get_password_hash("Investigator@1234"),
                "role": "fraud_investigator",
                "is_active": True,
            },
            {
                "name": "Demo Customer",
                "email": "user@fraudlens.ai",
                "password_hash": get_password_hash("User@1234"),
                "role": "customer",
                "is_active": True,
            },
            {
                "name": "Rajesh Kumar",
                "email": "customer@fraudlens.ai",
                "password_hash": get_password_hash("Customer@1234"),
                "role": "customer",
                "is_active": True,
            },
        ]

        for u_data in users_to_seed:
            existing = db.query(User).filter(User.email == u_data["email"]).first()
            if not existing:
                user = User(**u_data)
                db.add(user)
            else:
                existing.password_hash = u_data["password_hash"]
                existing.role = u_data["role"]
                existing.is_active = True
        db.commit()

        # 2. Read Canonical Dataset
        logger.info("Reading canonical dataset from: %s", CSV_PATH)
        if not os.path.exists(CSV_PATH):
            raise FileNotFoundError(f"Dataset not found at {CSV_PATH}")

        df = pd.read_csv(CSV_PATH)
        logger.info("Read %d records from CSV.", len(df))

        # 3. Seed 29 Master Merchants
        logger.info("Seeding 29 Master Merchants...")
        merchant_group = df.groupby("merchant_id").first().reset_index()
        for _, row in merchant_group.iterrows():
            m_id = str(row["merchant_id"])
            existing_m = db.query(Merchant).filter(Merchant.merchant_id == m_id).first()
            m_payload = {
                "merchant_id": m_id,
                "merchant_name": str(row["merchant_name"]),
                "category": str(row["merchant_category"]),
                "subcategory": str(row.get("merchant_subcategory", "")),
                "city": str(row["merchant_city"]),
                "area": str(row["merchant_area"]),
                "state": str(row["merchant_state"]),
                "pincode": str(row["merchant_pincode"]),
                "latitude": float(row["merchant_latitude"]),
                "longitude": float(row["merchant_longitude"]),
                "business_age": int(row["merchant_business_age_years"]),
                "average_ticket": float(row["merchant_average_ticket"]),
                "operating_hours": str(row["merchant_operating_hours"]),
                "business_type": str(row["merchant_category"]),
                "payment_channel": str(row["merchant_payment_channels"]),
                "historical_fraud_rate": float(row["merchant_historical_fraud_rate"]),
                "historical_fraud_count": int(row["merchant_historical_fraud_count"]),
                "historical_fraud_pattern": str(row["merchant_historical_fraud_pattern"]),
                "historical_fraud_summary": f"Synthetic historical fraud pattern: {row['merchant_historical_fraud_pattern']} with rate {float(row['merchant_historical_fraud_rate'])*100:.1f}%.",
            }

            if not existing_m:
                db.add(Merchant(**m_payload))
            else:
                for k, v in m_payload.items():
                    setattr(existing_m, k, v)
        db.commit()
        merchant_count = db.query(Merchant).count()
        logger.info("Successfully synced %d merchants in DB.", merchant_count)

        # 4. Seed Customers (10 Male & 5 Female Tamil Names)
        logger.info("Seeding Exactly 15 Defined Customers (10 Male, 5 Female Tamil Names)...")
        customer_names = {
            # 10 Male
            "CUST_001": ("Murugan Velan", "murugan.velan@customer.fraudlens.ai"),
            "CUST_002": ("Senthil Kumar", "senthil.kumar@customer.fraudlens.ai"),
            "CUST_003": ("Karthik Narayanan", "karthik.n@customer.fraudlens.ai"),
            "CUST_004": ("Saravanan Thangavel", "saravanan.t@customer.fraudlens.ai"),
            "CUST_005": ("Manoj Balaji", "manoj.balaji@customer.fraudlens.ai"),
            "CUST_006": ("Arunachalam Swaminathan", "arunachalam.s@customer.fraudlens.ai"),
            "CUST_007": ("Vijay Raghavan", "vijay.raghavan@customer.fraudlens.ai"),
            "CUST_008": ("Prakash Natarajan", "prakash.n@customer.fraudlens.ai"),
            "CUST_009": ("Dinesh Chandran", "dinesh.c@customer.fraudlens.ai"),
            "CUST_010": ("Suresh Pandian", "suresh.pandian@customer.fraudlens.ai"),
            # 5 Female
            "CUST_011": ("Kavitha Mohan", "kavitha.mohan@customer.fraudlens.ai"),
            "CUST_012": ("Deepa Sundaram", "deepa.sundaram@customer.fraudlens.ai"),
            "CUST_013": ("Dr. Ananya Ramaswamy", "ananya.r@customer.fraudlens.ai"),
            "CUST_014": ("Meenakshi Krishnan", "meenakshi.k@customer.fraudlens.ai"),
            "CUST_015": ("Revathi Soundararajan", "revathi.s@customer.fraudlens.ai"),
        }

        customer_group = df.groupby("customer_id").first().reset_index()
        for _, row in customer_group.iterrows():
            c_id = str(row["customer_id"])
            c_name, c_email = customer_names.get(c_id, (f"Customer {c_id}", f"{c_id.lower()}@customer.fraudlens.ai"))
            c = Customer(
                customer_id=c_id,
                account_age_days=int(row["customer_account_age_days"]),
                simulated_balance=1600000.0,
                currency="INR",
                name=c_name,
                email=c_email,
                risk_segment="Standard",
            )
            db.add(c)
        db.commit()
        logger.info("Synced %d customers in DB.", db.query(Customer).count())

        # 5. Ingest Transactions
        logger.info("Checking existing transactions in DB...")
        existing_tx_count = db.query(Transaction).count()
        if existing_tx_count < len(df):
            logger.info("Ingesting %d transactions into DB...", len(df))
            # Delete old test transactions to avoid ID collisions
            db.query(Transaction).delete()
            db.commit()

            tx_objects = []
            for i, row in df.iterrows():
                is_fraud_val = int(row["is_fraud"])
                fraud_prob = 0.95 if is_fraud_val == 1 else round(float(np.random.uniform(0.01, 0.12)), 4)
                risk_score_val = 94.0 if is_fraud_val == 1 else round(float(np.random.uniform(5.0, 35.0)), 1)
                risk_level_val = "HIGH" if is_fraud_val == 1 or risk_score_val >= 70 else ("MEDIUM" if risk_score_val >= 40 else "LOW")
                status_val = "BLOCKED" if is_fraud_val == 1 else ("REVIEW_REQUIRED" if risk_level_val == "MEDIUM" else "SUCCESS")

                dt_obj = pd.to_datetime(row["transaction_datetime"]).to_pydatetime()
                if dt_obj.tzinfo is None:
                    dt_obj = dt_obj.replace(tzinfo=timezone.utc)

                tx = Transaction(
                    transaction_id=str(row["transaction_id"]),
                    customer_id=str(row["customer_id"]),
                    merchant_id=str(row["merchant_id"]),
                    merchant_name=str(row["merchant_name"]),
                    merchant_category=str(row["merchant_category"]),
                    amount=float(row["amount"]),
                    currency="INR",
                    transaction_hour=int(row["transaction_hour"]),
                    day_of_week=int(row["day_of_week"]),
                    transaction_type=str(row["transaction_type"]),
                    payment_channel=str(row["merchant_payment_channels"]),
                    transaction_country="IN",
                    geo_location_region=str(row["merchant_city"]),
                    current_location=str(row["current_location"]),
                    usual_location=str(row["customer_usual_location"]),
                    location_changed=bool(row["is_location_changed"]),
                    location_distance=float(row["location_distance_km"]),
                    device_id=str(row["device_id"]),
                    device_type=str(row["device_type"]),
                    is_new_device=bool(row["is_new_device"]),
                    is_trusted_device=bool(row["is_trusted_device"]),
                    beneficiary=str(row.get("beneficiary_name", "")),
                    beneficiary_id=str(row.get("beneficiary_id", "")),
                    is_new_beneficiary=bool(row["is_new_beneficiary"]),
                    transactions_last_1h=int(row["transactions_last_1h"]),
                    transactions_last_24h=int(row["transactions_last_24h"]),
                    transactions_last_7d=int(row["transactions_last_7d"]),
                    amount_deviation=float(row["amount_deviation_zscore"]),
                    amount_ratio=float(row["amount_to_avg_ratio"]),
                    failed_transaction_attempts=int(row["failed_transaction_attempts_24h"]),
                    failed_login_attempts=int(row["failed_login_attempts_24h"]),
                    recent_password_change=bool(row["recent_password_change"]),
                    is_fraud=is_fraud_val,
                    fraud_type=str(row.get("fraud_type", "")) if pd.notna(row.get("fraud_type")) else None,
                    fraud_stage=str(row.get("fraud_stage", "")) if pd.notna(row.get("fraud_stage")) else None,
                    fraud_scenario=str(row.get("fraud_scenario", "")) if pd.notna(row.get("fraud_scenario")) else None,
                    fraud_probability=fraud_prob,
                    prediction=is_fraud_val,
                    risk_score=risk_score_val,
                    risk_level=risk_level_val,
                    status=status_val,
                    created_at=dt_obj,
                )
                tx_objects.append(tx)

                # Batch insert in chunks of 2000
                if len(tx_objects) >= 2000:
                    db.bulk_save_objects(tx_objects)
                    db.commit()
                    tx_objects = []
                    logger.info("Inserted batch up to row %d...", i + 1)

            if tx_objects:
                db.bulk_save_objects(tx_objects)
                db.commit()

        total_tx = db.query(Transaction).count()
        total_fraud = db.query(Transaction).filter(Transaction.is_fraud == 1).count()
        logger.info("Total Transactions in DB: %d | Total Fraud Cases: %d", total_tx, total_fraud)

        # 6. Seed Sample Open Investigations for High-Risk Cases
        logger.info("Seeding initial investigation cases...")
        existing_cases = db.query(Investigation).count()
        if existing_cases < 10:
            admin_user = db.query(User).filter(User.role.in_(["admin", "fraud_investigator"])).first()
            high_risk_txs = (
                db.query(Transaction)
                .filter(Transaction.is_fraud == 1)
                .order_by(Transaction.created_at.desc())
                .limit(25)
                .all()
            )
            for idx, tx in enumerate(high_risk_txs):
                case_id = f"CASE-{tx.transaction_id}"
                case = db.query(Investigation).filter(Investigation.case_id == case_id).first()
                if not case:
                    status_choice = "open" if idx < 15 else ("under_review" if idx < 20 else "resolved")
                    decision_choice = "CONFIRMED_FRAUD" if status_choice == "resolved" else None
                    inv = Investigation(
                        case_id=case_id,
                        transaction_id=tx.transaction_id,
                        investigator_id=admin_user.id if admin_user else None,
                        status=status_choice,
                        decision=decision_choice,
                        notes=f"Automated case opened for high-risk pattern: {tx.fraud_scenario or 'High fraud probability detected'}.",
                    )
                    db.add(inv)
            db.commit()

        # 7. Add Audit Log Entry
        admin_u = db.query(User).filter(User.email == "admin@fraudlens.ai").first()
        log = AuditLog(
            user_id=admin_u.id if admin_u else None,
            action="DATABASE_SEEDED_29_MERCHANTS",
            resource_type="SYSTEM",
            resource_id="INITIAL_SEED",
            details=f"Successfully seeded {merchant_count} merchants, {total_tx} transactions ({total_fraud} fraud cases).",
        )
        db.add(log)
        db.commit()

        logger.info("Database seeding completed successfully!")

    except Exception as e:
        logger.exception("Database seeding failed: %s", e)
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
