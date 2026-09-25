"""
Real-Time Transaction Stream Simulation CLI for FraudLens AI.

Simulates live incoming transactions for any of the 3 customer logins,
evaluating them through the pre-authorization risk engine and broadcasting
real-time alerts to the investigator and customer dashboards.
"""

import sys
import os
import io
import time
import random
import argparse
import datetime
import json

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.core.database import SessionLocal
from backend.app.models.user import User
from backend.app.models.customer import Customer
from backend.app.models.merchant import Merchant
from backend.app.services.risk_decision_orchestrator import RiskDecisionOrchestrator
from backend.app.schemas.payment import PaymentInitiateRequest
from scripts.generate_canonical_29_merchants_dataset import MERCHANTS_MASTER

CUSTOMER_LOGINS = {
    "1": {"id": "CUST_MONISHA_001", "name": "Monisha (3% Fraud Rate - Low Risk)", "email": "monisha@fraudlens.ai", "device": "DEV-MONISHA-IPHONE-15", "loc": "Chennai"},
    "2": {"id": "CUST_MOHANA_002", "name": "Mohana (12% Fraud Rate - Medium Risk / Review)", "email": "mohana@fraudlens.ai", "device": "DEV-MOHANA-SAMSUNG-S23", "loc": "Coimbatore"},
    "3": {"id": "CUST_SOWMIYA_003", "name": "Sowmiya (26% Fraud Rate - High Risk / Block)", "email": "sowmiya@fraudlens.ai", "device": "DEV-SOWMIYA-ONEPLUS-11", "loc": "Bengaluru"},
}


def run_realtime_simulation(customer_choice: str = "1", count: int = 5, delay: float = 1.5):
    target = CUSTOMER_LOGINS.get(customer_choice, CUSTOMER_LOGINS["1"])
    print("\n========================================================")
    print(f" Starting Real-Time Simulation for: {target['name']}")
    print(f" Customer ID: {target['id']} | Email: {target['email']}")
    print(f" Firing {count} live transactions (interval: {delay}s)...")
    print("========================================================\n")

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == target["email"]).first()
        cust = db.query(Customer).filter(Customer.customer_id == target["id"]).first()
        
        if not cust:
            print(f"[!] Customer {target['id']} not found in DB. Run generate_3_customer_realtime_datasets.py first.")
            return

        for i in range(1, count + 1):
            now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
            
            # Determine scenario based on customer profile
            if target["id"] == "CUST_MONISHA_001":
                # Safe purchase (3% fraud baseline)
                merchant = MERCHANTS_MASTER[0]  # NovaMart Fresh
                amount = round(random.uniform(500.0, 1800.0), 2)
                device_id = target["device"]
                device_type = "mobile_ios"
                current_loc = target["loc"]
                loc_dist = float(random.randint(1, 5))
                ben_name = merchant["merchant_name"]
                scenario = "Habitual Grocery Purchase at NovaMart Fresh in Chennai (Low Risk - 3% Baseline)"
            elif target["id"] == "CUST_MOHANA_002":
                # Suspicious purchase (12% fraud baseline)
                merchant = random.choice(MERCHANTS_MASTER[5:15])
                amount = round(random.uniform(18000.0, 38000.0), 2)
                device_id = "DEV-MOHANA-NEW-MACBOOK"
                device_type = "web_browser"
                current_loc = random.choice(["Mumbai", "Delhi", "Hyderabad"])
                loc_dist = float(random.randint(450, 950))
                ben_name = "Luxury International Travel Hub"
                scenario = "High-Ticket Cross-State Purchase via New Browser (Medium Risk - 12% Baseline)"
            else:
                # Attack scenario (26% fraud baseline)
                merchant = random.choice(MERCHANTS_MASTER[15:])
                amount = round(random.uniform(45000.0, 95000.0), 2)
                device_id = f"DEV-ROGUE-BOTNET-{random.randint(100, 999)}"
                device_type = "unknown_bot"
                current_loc = random.choice(["Dubai", "Lagos", "Moscow"])
                loc_dist = float(random.randint(2800, 5200))
                ben_name = f"QuickMule-Cashout-{random.randint(10, 99)}"
                scenario = "Account Takeover / Foreign Velocity Burst (High Risk - 26% Baseline)"

            req = PaymentInitiateRequest(
                customer_id=target["id"],
                amount=amount,
                currency="INR",
                merchant_name=merchant["merchant_name"],
                merchant_category=merchant["merchant_category"],
                payment_method="upi" if "UPI" in merchant["merchant_payment_channels"] else "credit_card",
                device_type=device_type,
                location=current_loc,
                transaction_country="IN" if target["id"] != "CUST_SOWMIYA_003" else "AE",
                transaction_type="online_payment",
                beneficiary_name=ben_name,
                idempotency_key=f"LIVE-TXN-{int(time.time()*1000)}-{i}",
            )

            print(f"[{i}/{count}] [{datetime.datetime.now().strftime('%H:%M:%S')}] Sending Live Txn: INR {amount:,.2f} at {merchant['merchant_name']} ({merchant['merchant_city']})")
            print(f"       Scenario: {scenario} | Location: {current_loc} ({loc_dist} km)")

            # Execute real-time risk decision
            result = RiskDecisionOrchestrator.evaluate_and_process_payment(
                db=db,
                request=req,
                current_user=user,
            )

            status_icon = "[ALLOW]" if result.decision.value == "ALLOW" else ("[REVIEW]" if result.decision.value == "REVIEW" else "[BLOCK]")
            print(f"       => Result: {status_icon} Decision: {result.decision.value:<6} | Risk Score: {result.risk_score:5.1f}/100 | ML Prob: {result.fraud_probability*100:4.1f}%")
            if result.triggered_rules:
                rules_str = ", ".join([r.rule_name for r in result.triggered_rules])
                print(f"       => Triggered Rules: {rules_str}")
            if result.top_risk_factors:
                factors_str = "; ".join([f"{f.factor}: {f.detail}" for f in result.top_risk_factors[:2]])
                print(f"       => Key Explanations: {factors_str}")
            print("----------------------------------------------------------------------")
            
            if i < count:
                time.sleep(delay)

        print("\n[OK] Real-Time Stream Simulation completed successfully.")

    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Simulate Real-Time Transactions for FraudLens AI")
    parser.add_argument("--customer", choices=["1", "2", "3"], default="1", help="1=Monisha (3%% Safe), 2=Mohana (12%% Review/OTP), 3=Sowmiya (26%% Attack/Block)")
    parser.add_argument("--count", type=int, default=5, help="Number of real-time transactions to fire")
    parser.add_argument("--delay", type=float, default=1.0, help="Delay between transactions in seconds")
    args = parser.parse_args()

    run_realtime_simulation(customer_choice=args.customer, count=args.count, delay=args.delay)
