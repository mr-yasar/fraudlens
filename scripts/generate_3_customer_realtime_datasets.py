"""
Generate 3 Distinct Real-Time Customer Datasets & Seed Live Logins for FraudLens AI.

Creates 3 realistic, 55-column datasets representing 3 different risk personas:
  1. Arun Sharma (Normal / Clean baseline user)
  2. Priya Sundaram (Suspicious / Step-Up Review user)
  3. Vikram Rajan (Compromised / High-Risk Attack user)

Also seeds database logins and provides real-time streaming capability.
"""

import os
import sys
import random
import argparse
import datetime
import numpy as np
import pandas as pd

# Set path for backend imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

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

# Import Merchants master from canonical generator
from scripts.generate_canonical_29_merchants_dataset import MERCHANTS_MASTER

# Deterministic seed for initial generation
np.random.seed(42)
random.seed(42)

# Define 3 Exact Customer Personas requested by User
CUSTOMER_PERSONAS = [
    {
        "customer_id": "CUST_MONISHA_001",
        "name": "Monisha",
        "email": "monisha@fraudlens.ai",
        "password": "Customer@1234",
        "role": "customer",
        "risk_segment": "Low Risk / 3% Fraud Rate",
        "usual_location": "Chennai",
        "usual_state": "Tamil Nadu",
        "device_id": "DEV-MONISHA-IPHONE-15",
        "device_type": "mobile_ios",
        "account_age_days": 420,
        "simulated_balance": 120000.0,
        "avg_ticket": 1950.0,
        "fraud_rate": 0.03,  # Exact 3% fraud rate
        "behavior_desc": "Standard daily consumer transactions in Chennai with rare anomaly triggers (3% fraud rate).",
        "filename": "dataset_customer_monisha_3pct.csv",
    },
    {
        "customer_id": "CUST_MOHANA_002",
        "name": "Mohana",
        "email": "mohana@fraudlens.ai",
        "password": "Customer@1234",
        "role": "customer",
        "risk_segment": "Medium Risk / 12% Fraud Rate",
        "usual_location": "Coimbatore",
        "usual_state": "Tamil Nadu",
        "device_id": "DEV-MOHANA-SAMSUNG-S23",
        "device_type": "mobile_android",
        "account_age_days": 180,
        "simulated_balance": 220000.0,
        "avg_ticket": 8500.0,
        "fraud_rate": 0.12,  # Exact 12% fraud rate
        "behavior_desc": "Frequent cross-city purchases, occasional unverified beneficiaries and travel spikes (12% fraud rate).",
        "filename": "dataset_customer_mohana_12pct.csv",
    },
    {
        "customer_id": "CUST_SOWMIYA_003",
        "name": "Sowmiya",
        "email": "sowmiya@fraudlens.ai",
        "password": "Customer@1234",
        "role": "customer",
        "risk_segment": "High Risk / 26% Fraud Rate",
        "usual_location": "Bengaluru",
        "usual_state": "Karnataka",
        "device_id": "DEV-SOWMIYA-ONEPLUS-11",
        "device_type": "mobile_android",
        "account_age_days": 55,
        "simulated_balance": 45000.0,
        "avg_ticket": 28500.0,
        "fraud_rate": 0.26,  # Exact 26% fraud rate
        "behavior_desc": "High-velocity off-hours bursts, proxy IPs, bot device hops, and rapid multi-merchant draining (26% fraud rate).",
        "filename": "dataset_customer_sowmiya_26pct.csv",
    },
]


def generate_customer_dataset(persona: dict, num_records: int = 1500) -> pd.DataFrame:
    """Generates a high-fidelity 55-column dataset tailored to a specific customer persona."""
    records = []
    
    # Generate realistic timestamps leading right up to 3 hours ago (September 2026)
    end_date = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=3)
    start_date = end_date - datetime.timedelta(days=90)
    current_time = start_date
    delta_minutes = (90 * 24 * 60) / num_records

    # Select exact fraud indices to guarantee exact percentage (3%, 12%, 26%)
    num_fraud_records = int(round(num_records * persona["fraud_rate"]))
    fraud_indices = set(random.sample(range(1, num_records + 1), num_fraud_records))

    for idx in range(1, num_records + 1):
        tx_id = f"TXN-{persona['customer_id']}-{10000 + idx}"
        jitter = random.uniform(-3.0, 3.0)
        current_time += datetime.timedelta(minutes=max(delta_minutes + jitter, 1.0))
        
        tx_hour = current_time.hour
        tx_dow = current_time.weekday()
        is_weekend = 1 if tx_dow >= 5 else 0
        is_night = 1 if (tx_hour >= 23 or tx_hour <= 5) else 0

        # Choose Merchant
        merchant = random.choice(MERCHANTS_MASTER)
        
        # Fraud determination (exact set match)
        is_fraud = 1 if idx in fraud_indices else 0

        if is_fraud:
            # Fraudulent / Anomaly dynamics
            if persona["customer_id"] == "CUST_SOWMIYA_003":
                # High-risk account takeover scenario
                fraud_type = random.choice(["Account takeover", "Card testing", "Credential compromise", "Mule-account behavior"])
                fraud_stage = "Pre-auth Block"
                fraud_scenario = "Automated high-velocity attack from unknown device"
                amount = float(round(merchant["merchant_average_ticket"] * random.uniform(2.2, 5.0), 2))
                is_new_dev = 1
                is_trusted_dev = 0
                dev_id = f"DEV-ROGUE-EMULATOR-{random.randint(100, 999)}"
                dev_type = "unknown_bot"
                curr_loc = random.choice(["Dubai", "Lagos", "Singapore", "Moscow", "Unknown Proxy"])
                loc_dist = float(random.randint(1200, 5500))
                tx_1h = random.randint(4, 12)
                tx_24h = random.randint(12, 35)
                failed_logins = random.randint(2, 6)
                failed_txs = random.randint(1, 4)
                pw_changed = 1 if random.random() < 0.6 else 0
                is_new_ben = 1
                ben_id = f"BEN-MULE-{random.randint(1000, 9999)}"
                ben_name = f"QuickMule Transfer {random.randint(10, 99)}"
                ben_count = 0
            else:
                # Review / Suspicious scenario
                fraud_type = "Geographic Anomaly / High Ticket Spike"
                fraud_stage = "Review Required"
                fraud_scenario = "Sudden location velocity jump with new merchant"
                amount = float(round(merchant["merchant_average_ticket"] * random.uniform(1.8, 3.2), 2))
                is_new_dev = 1 if random.random() < 0.5 else 0
                is_trusted_dev = 0 if is_new_dev else 1
                dev_id = f"DEV-LAPTOP-CHROME-{random.randint(100, 999)}" if is_new_dev else persona["device_id"]
                dev_type = "web_browser" if is_new_dev else persona["device_type"]
                curr_loc = random.choice(["Mumbai", "Delhi", "Hyderabad"])
                loc_dist = float(random.randint(300, 1100))
                tx_1h = random.randint(2, 4)
                tx_24h = random.randint(4, 10)
                failed_logins = 1
                failed_txs = 0
                pw_changed = 0
                is_new_ben = 1 if random.random() < 0.6 else 0
                ben_id = f"BEN-NEW-{random.randint(100, 999)}" if is_new_ben else f"BEN-{persona['customer_id']}-01"
                ben_name = "Global Flight Booking" if is_new_ben else "Self Family Transfer"
                ben_count = 0 if is_new_ben else 3
        else:
            # Genuine transaction
            fraud_type = "None"
            fraud_stage = "Resolved Genuine"
            fraud_scenario = "Standard Habitual Purchase"
            amount = float(round(persona["avg_ticket"] * random.uniform(0.4, 1.6), 2))
            is_new_dev = 0
            is_trusted_dev = 1
            dev_id = persona["device_id"]
            dev_type = persona["device_type"]
            curr_loc = persona["usual_location"]
            loc_dist = float(random.randint(1, 15))
            tx_1h = 1 if random.random() < 0.2 else 0
            tx_24h = random.randint(1, 4)
            failed_logins = 0
            failed_txs = 0
            pw_changed = 0
            is_new_ben = 0
            ben_id = f"BEN-{persona['customer_id']}-TRUSTED"
            ben_name = "Trusted Household Vendor"
            ben_count = random.randint(3, 15)

        # Build complete 55-column dictionary
        record = {
            "transaction_id": tx_id,
            "transaction_datetime": current_time.strftime("%Y-%m-%d %H:%M:%S"),
            "transaction_date": current_time.strftime("%Y-%m-%d"),
            "transaction_time": current_time.strftime("%H:%M:%S"),
            "transaction_hour": tx_hour,
            "day_of_week": tx_dow,
            "is_weekend": is_weekend,
            "is_night_transaction": is_night,
            "customer_id": persona["customer_id"],
            "customer_account_age_days": persona["account_age_days"],
            "customer_usual_location": persona["usual_location"],
            "customer_usual_state": persona["usual_state"],
            "customer_risk_segment": persona["risk_segment"],
            "merchant_id": merchant["merchant_id"],
            "merchant_name": merchant["merchant_name"],
            "merchant_category": merchant["merchant_category"],
            "merchant_subcategory": merchant["merchant_subcategory"],
            "merchant_city": merchant["merchant_city"],
            "merchant_area": merchant["merchant_area"],
            "merchant_state": merchant["merchant_state"],
            "merchant_pincode": merchant["merchant_pincode"],
            "merchant_latitude": merchant["merchant_latitude"],
            "merchant_longitude": merchant["merchant_longitude"],
            "merchant_business_age_years": merchant["merchant_business_age_years"],
            "merchant_average_ticket": merchant["merchant_average_ticket"],
            "merchant_operating_hours": merchant["merchant_operating_hours"],
            "merchant_payment_channels": merchant["merchant_payment_channels"],
            "merchant_historical_fraud_pattern": merchant["historical_fraud_pattern"],
            "merchant_historical_fraud_rate": merchant["base_fraud_rate"],
            "merchant_historical_fraud_count": int(merchant["base_fraud_rate"] * 2500),
            "amount": amount,
            "currency": "INR",
            "transaction_type": "PURCHASE" if is_new_ben == 0 else "P2P_TRANSFER",
            "payment_channel": random.choice(merchant["merchant_payment_channels"].split(",")),
            "transaction_channel": "MOBILE_APP" if "mobile" in dev_type else "WEB_PORTAL",
            "card_present": 1 if "POS" in merchant["merchant_payment_channels"] and loc_dist < 20 else 0,
            "is_international": 1 if curr_loc in ["Dubai", "Lagos", "Singapore", "Moscow", "London", "Nairobi"] else 0,
            "current_location": curr_loc,
            "location_distance_km": loc_dist,
            "is_location_changed": 1 if loc_dist > 50 else 0,
            "is_new_device": is_new_dev,
            "is_trusted_device": is_trusted_dev,
            "device_id": dev_id,
            "device_type": dev_type,
            "is_new_beneficiary": is_new_ben,
            "beneficiary_id": ben_id,
            "beneficiary_name": ben_name,
            "beneficiary_prior_transaction_count": ben_count,
            "customer_tx_count_last_1h": tx_1h,
            "customer_tx_count_last_24h": tx_24h,
            "customer_tx_count_last_7d": tx_24h * 4 + random.randint(2, 10),
            "failed_login_attempts_last_24h": failed_logins,
            "failed_transaction_attempts_last_24h": failed_txs,
            "recent_password_reset_flag": pw_changed,
            "fraud_scenario_type": fraud_type,
            "fraud_lifecycle_stage": fraud_stage,
            "synthetic_fraud_scenario_description": fraud_scenario,
            "is_fraud": is_fraud,
        }
        records.append(record)
        
    df = pd.DataFrame(records)
    return df


def seed_database_with_realtime_personas(dfs: dict):
    """Inserts the 3 users, customer records, devices, beneficiaries, and transactions into DB."""
    db = SessionLocal()
    try:
        print("\n========================================================")
        print(" Seeding 3 Real-Time Customer Logins & Transaction Data ")
        print("========================================================")
        
        for persona in CUSTOMER_PERSONAS:
            c_id = persona["customer_id"]
            email = persona["email"]
            name = persona["name"]
            
            # 1. User Login Account
            user = db.query(User).filter(User.email == email).first()
            if not user:
                user = User(
                    name=name,
                    email=email,
                    password_hash=get_password_hash(persona["password"]),
                    role=persona["role"],
                    is_active=True,
                )
                db.add(user)
                db.commit()
                db.refresh(user)
                print(f"[+] Created User Login: {email} (Password: {persona['password']})")
            else:
                user.password_hash = get_password_hash(persona["password"])
                user.is_active = True
                db.commit()
                print(f"[~] Updated User Login: {email}")

            # 2. Customer Profile
            cust = db.query(Customer).filter(Customer.customer_id == c_id).first()
            if not cust:
                cust = Customer(
                    customer_id=c_id,
                    name=name,
                    email=email,
                    account_age_days=persona["account_age_days"],
                    simulated_balance=persona["simulated_balance"],
                    currency="INR",
                    risk_segment=persona["risk_segment"],
                )
                db.add(cust)
            else:
                cust.simulated_balance = persona["simulated_balance"]
                cust.name = name
                cust.email = email
            db.commit()

            # 3. Customer Trusted Device & Beneficiaries
            existing_dev = db.query(CustomerDevice).filter(CustomerDevice.customer_id == c_id).first()
            if not existing_dev:
                dev = CustomerDevice(
                    customer_id=c_id,
                    device_identifier=persona["device_id"],
                    device_type=persona["device_type"],
                    browser_or_client=f"{persona['name']}'s Primary Client",
                    location_region=persona["usual_location"],
                    is_trusted=True if persona["customer_id"] != "CUST_SOWMIYA_003" else False,
                    is_compromised=True if persona["customer_id"] == "CUST_SOWMIYA_003" else False,
                    first_seen_at=datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=persona["account_age_days"]),
                    last_seen_at=datetime.datetime.now(datetime.timezone.utc),
                )
                db.add(dev)
                db.commit()

            # Seed top 5 merchants as trusted beneficiaries for safe/review customers
            if persona["customer_id"] != "CUST_SOWMIYA_003":
                for m in MERCHANTS_MASTER[:5]:
                    existing_ben = db.query(Beneficiary).filter(
                        Beneficiary.customer_id == c_id,
                        Beneficiary.beneficiary_name == m["merchant_name"]
                    ).first()
                    if not existing_ben:
                        ben = Beneficiary(
                            customer_id=c_id,
                            beneficiary_name=m["merchant_name"],
                            category="retail",
                            trust_score=0.95,
                            is_trusted=True,
                            total_transfers=12,
                        )
                        db.add(ben)
                db.commit()

            # 4. Ingest recent transactions for this customer
            df_cust = dfs[c_id]
            print(f"[*] Ingesting {len(df_cust)} transactions for {name} ({c_id})...")
            
            # Remove any old conflicting records for this customer
            db.query(Transaction).filter(Transaction.customer_id == c_id).delete()
            db.commit()

            tx_objs = []
            for _, row in df_cust.iterrows():
                is_f = int(row["is_fraud"])
                fraud_prob = 0.96 if is_f == 1 else round(float(np.random.uniform(0.01, 0.15)), 4)
                risk_score_val = 94.0 if is_f == 1 else (55.0 if persona["customer_id"] == "CUST_MOHANA_002" and random.random() < 0.25 else 12.0)
                risk_level_val = "HIGH" if is_f == 1 or risk_score_val >= 70 else ("MEDIUM" if risk_score_val >= 40 else "LOW")
                status_val = "BLOCKED" if is_f == 1 else ("REVIEW_REQUIRED" if risk_level_val == "MEDIUM" else "SUCCESS")

                dt_obj = pd.to_datetime(row["transaction_datetime"]).to_pydatetime()
                if dt_obj.tzinfo is None:
                    dt_obj = dt_obj.replace(tzinfo=datetime.timezone.utc)

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
                    payment_channel=str(row["payment_channel"]),
                    transaction_country="IN",
                    geo_location_region=str(row["merchant_city"]),
                    current_location=str(row["current_location"]),
                    usual_location=str(row["customer_usual_location"]),
                    location_distance=float(row["location_distance_km"]),
                    location_changed=bool(row["is_location_changed"]),
                    device_id=str(row["device_id"]),
                    device_type=str(row["device_type"]),
                    is_new_device=bool(row["is_new_device"]),
                    is_trusted_device=bool(row["is_trusted_device"]),
                    beneficiary=str(row["beneficiary_name"]),
                    beneficiary_id=str(row["beneficiary_id"]),
                    is_new_beneficiary=bool(row["is_new_beneficiary"]),
                    transactions_last_1h=int(row["customer_tx_count_last_1h"]),
                    transactions_last_24h=int(row["customer_tx_count_last_24h"]),
                    transactions_last_7d=int(row["customer_tx_count_last_7d"]),
                    failed_transaction_attempts=int(row["failed_transaction_attempts_last_24h"]),
                    failed_login_attempts=int(row["failed_login_attempts_last_24h"]),
                    recent_password_change=bool(row["recent_password_reset_flag"]),
                    is_fraud=is_f,
                    fraud_type=str(row["fraud_scenario_type"]),
                    fraud_stage=str(row["fraud_lifecycle_stage"]),
                    fraud_scenario=str(row["synthetic_fraud_scenario_description"]),
                    prediction=is_f,
                    status=status_val,
                    risk_score=risk_score_val,
                    risk_level=risk_level_val,
                    fraud_probability=fraud_prob,
                    created_at=dt_obj,
                )
                tx_objs.append(tx)

            db.bulk_save_objects(tx_objs)
            db.commit()
            print(f"[OK] Successfully synced {len(tx_objs)} transactions for {c_id}.")

    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(description="Generate 3 Real-Time Customer Datasets")
    parser.add_argument("--records-per-customer", type=int, default=1500, help="Number of records per dataset")
    parser.add_argument("--seed-db", action="store_true", default=True, help="Seed DB with customer accounts and transactions")
    args = parser.parse_args()

    os.makedirs("data/raw", exist_ok=True)
    generated_dfs = {}
    master_dfs = []

    print("\n========================================================")
    print(" Generating 3 Real-Time Datasets at Canonical Standards ")
    print("========================================================")

    for persona in CUSTOMER_PERSONAS:
        out_path = os.path.join("data", "raw", persona["filename"])
        df = generate_customer_dataset(persona, num_records=args.records_per_customer)
        df.to_csv(out_path, index=False)
        generated_dfs[persona["customer_id"]] = df
        master_dfs.append(df)
        
        fraud_cnt = int(df["is_fraud"].sum())
        print(f"[+] Generated: {out_path}")
        print(f"    - Total Records: {len(df)} | Columns: {len(df.columns)}")
        print(f"    - Fraud Cases: {fraud_cnt} ({fraud_cnt / len(df) * 100:.2f}%)")
        print(f"    - Persona: {persona['name']} ({persona['risk_segment']})")

    # Combine into unified master dataset
    master_df = pd.concat(master_dfs, ignore_index=True)
    master_df = master_df.sort_values(by="transaction_datetime").reset_index(drop=True)
    master_out_path = os.path.join("data", "raw", "master_3_customer_realtime_profiles.csv")
    master_df.to_csv(master_out_path, index=False)
    print(f"\n[+] Created Master Unified File: {master_out_path} ({len(master_df)} rows, 55 columns)")

    if args.seed_db:
        seed_database_with_realtime_personas(generated_dfs)

    print("\n========================================================")
    print(" SUMMARY OF 3 REAL-TIME LOGINS & VERIFIED DATASETS")
    print("========================================================")
    for persona in CUSTOMER_PERSONAS:
        print(f"Customer: {persona['name']:<22} | ID: {persona['customer_id']:<14}")
        print(f"  - Login Email:    {persona['email']}")
        print(f"  - Login Password: {persona['password']}")
        print(f"  - Dataset CSV:    data/raw/{persona['filename']}")
        print(f"  - Risk Segment:   {persona['risk_segment']}")
        print(f"  - Behavior:       {persona['behavior_desc']}")
        print("--------------------------------------------------------")


if __name__ == "__main__":
    main()
