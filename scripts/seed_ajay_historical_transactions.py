"""
Seed 1,500 historical transactions for Ajay from dataset_customer_ajay_pure.csv into SQLite database.
Ensures ML models, charts, velocity calculations, and transaction tables have complete historical records.
"""

import os
import sys
import pandas as pd
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.core.database import SessionLocal
from backend.app.models.transaction import Transaction
from backend.app.models.customer import Customer
from backend.app.models.user import User

def seed_ajay_transactions():
    csv_path = "data/raw/dataset_customer_ajay_pure.csv"
    if not os.path.exists(csv_path):
        print(f"Error: {csv_path} not found.")
        return

    df = pd.read_csv(csv_path)
    print(f"Loaded {len(df)} transactions from {csv_path}")

    db = SessionLocal()
    try:
        # Verify Customer CUST_PREMIUM_004 exists
        customer = db.query(Customer).filter(Customer.customer_id == "CUST_PREMIUM_004").first()
        if not customer:
            print("Creating customer CUST_PREMIUM_004 for Ajay...")
            customer = Customer(
                customer_id="CUST_PREMIUM_004",
                name="Ajay",
                email="ajay@fraudlens.ai",
                simulated_balance=2500000.0,
                currency="INR",
                risk_segment="Enterprise Security",
                account_age_days=730,
            )
            db.add(customer)
            db.commit()

        # Ingest records in chunks
        existing_tx_ids = set(
            row[0] for row in db.query(Transaction.transaction_id).filter(
                Transaction.customer_id == "CUST_PREMIUM_004"
            ).all()
        )
        print(f"Found {len(existing_tx_ids)} existing transactions for Ajay in database.")

        new_transactions = []
        for _, row in df.iterrows():
            tx_id = str(row["transaction_id"])
            if tx_id in existing_tx_ids:
                continue

            try:
                created_dt = datetime.strptime(str(row["transaction_datetime"]), "%Y-%m-%d %H:%M:%S")
            except Exception:
                created_dt = datetime.utcnow()

            amount_val = float(row["amount"])
            is_fraud = int(row.get("is_fraud", 0))

            # Calibrated AI score based on pure dataset
            if is_fraud:
                fraud_prob = 0.88
                risk_score = 88.0
                risk_level = "HIGH"
                status = "HELD"
            else:
                fraud_prob = 0.02
                risk_score = 4.0
                risk_level = "LOW"
                status = "SUCCESS"

            t = Transaction(
                transaction_id=tx_id,
                customer_id="CUST_PREMIUM_004",
                merchant_id=str(row.get("merchant_id", "M029")),
                merchant_name=str(row.get("merchant_name", "CloudDesk Digital")),
                merchant_category=str(row.get("merchant_category", "Software / Digital Services")),
                amount=amount_val,
                currency=str(row.get("currency", "INR")),
                transaction_hour=int(row.get("transaction_hour", 12)),
                day_of_week=int(row.get("day_of_week", 1)),
                transaction_type=str(row.get("transaction_type", "TRANSFER")),
                payment_channel=str(row.get("payment_channel", "TRANSFER")),
                transaction_country="IN",
                geo_location_region=str(row.get("customer_usual_state", "Maharashtra")),
                current_location=str(row.get("current_location", "Mumbai")),
                usual_location=str(row.get("customer_usual_location", "Mumbai")),
                location_changed=bool(row.get("is_location_changed", 0)),
                location_distance=float(row.get("location_distance_km", 0.0)),
                device_id=str(row.get("device_id", "dev-mbp-m3")),
                device_type=str(row.get("device_type", "desktop_macos")),
                is_new_device=bool(row.get("is_new_device", 0)),
                is_trusted_device=bool(row.get("is_trusted_device", 1)),
                beneficiary=str(row.get("beneficiary_name", "Cloudflare Global Services")),
                beneficiary_id=str(row.get("beneficiary_id", "BEN-CF-01")),
                is_new_beneficiary=bool(row.get("is_new_beneficiary", 0)),
                transactions_last_1h=int(row.get("customer_tx_count_last_1h", 0)),
                transactions_last_24h=int(row.get("customer_tx_count_last_24h", 1)),
                transactions_last_7d=int(row.get("customer_tx_count_last_7d", 4)),
                amount_deviation=float(row.get("amount_deviation_zscore", 0.0) if "amount_deviation_zscore" in row else 0.0),
                amount_ratio=float(row.get("amount_to_avg_ratio", 1.0) if "amount_to_avg_ratio" in row else 1.0),
                failed_transaction_attempts=int(row.get("failed_transaction_attempts_last_24h", 0)),
                failed_login_attempts=int(row.get("failed_login_attempts_last_24h", 0)),
                recent_password_change=bool(row.get("recent_password_reset_flag", 0)),
                fraud_probability=fraud_prob,
                prediction=is_fraud,
                risk_score=risk_score,
                risk_level=risk_level,
                is_fraud=is_fraud,
                fraud_type=str(row.get("fraud_scenario_type", "None")),
                fraud_stage=str(row.get("fraud_lifecycle_stage", "Resolved Genuine")),
                fraud_scenario=str(row.get("synthetic_fraud_scenario_description", "Standard Enterprise Settlement")),
                status=status,
                created_at=created_dt,
            )
            new_transactions.append(t)

        if new_transactions:
            db.bulk_save_objects(new_transactions)
            db.commit()
            print(f"[SUCCESS] Successfully seeded {len(new_transactions)} historical transactions for Ajay!")
        else:
            print("All transactions already present in database.")

        total_tx = db.query(Transaction).filter(Transaction.customer_id == "CUST_PREMIUM_004").count()
        print(f"Total transactions for Ajay in DB now: {total_tx}")

    finally:
        db.close()

if __name__ == "__main__":
    seed_ajay_transactions()
