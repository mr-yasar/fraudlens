"""
Update User 4 to Ajay, remove all VIP labels, generate Ajay Pure Dataset,
and populate rich Fleet Devices & Sessions for all 4 users (Monisha, Mohana, Sowmiya, Ajay).
"""

import os
import sys
import random
import datetime
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.core.database import SessionLocal
from backend.app.core.security import get_password_hash
from backend.app.models.user import User
from backend.app.models.customer import Customer
from backend.app.models.device import CustomerDevice
from backend.app.models.session import UserSession
from backend.app.models.behavioral_profile import BehavioralProfile
from backend.app.models.beneficiary import Beneficiary
from scripts.generate_canonical_29_merchants_dataset import MERCHANTS_MASTER

def run():
    db = SessionLocal()
    try:
        # 1. Update User 4 in Database to Ajay
        u = db.query(User).filter(User.email.in_(["premium@fraudlens.ai", "ajay@fraudlens.ai"])).first()
        if not u:
            u = User(
                name="Ajay",
                email="ajay@fraudlens.ai",
                password_hash=get_password_hash("Customer@1234"),
                role="customer",
                account_tier="PREMIUM",
                account_status="ACTIVE",
                is_active=True,
            )
            db.add(u)
            db.commit()
            db.refresh(u)
        else:
            u.name = "Ajay"
            u.email = "ajay@fraudlens.ai"
            u.account_tier = "PREMIUM"
            u.account_status = "ACTIVE"
            db.commit()
        print(f"[OK] User updated: ID={u.id}, Name={u.name}, Email={u.email}")

        # 2. Update Customer 4 in Database to Ajay without VIP
        c = db.query(Customer).filter(Customer.customer_id.in_(["CUST_PREMIUM_004", "CUST_AJAY_004"])).first()
        if not c:
            c = Customer(
                customer_id="CUST_PREMIUM_004",
                name="Ajay",
                email="ajay@fraudlens.ai",
                account_age_days=730,
                simulated_balance=2500000.0,
                currency="INR",
                risk_segment="Enterprise Security",
            )
            db.add(c)
            db.commit()
            db.refresh(c)
        else:
            c.name = "Ajay"
            c.email = "ajay@fraudlens.ai"
            c.risk_segment = "Enterprise Security"
            db.commit()
        print(f"[OK] Customer updated: ID={c.customer_id}, Name={c.name}, Segment={c.risk_segment}")

        # Update Behavioral Profile for Ajay
        bp = db.query(BehavioralProfile).filter(BehavioralProfile.customer_id == "CUST_PREMIUM_004").first()
        if bp:
            bp.behavioral_baseline = "High-ticket enterprise settlements with hardware enclave biometric security and zero-loss protection."
            bp.trusted_devices = "MacBook Pro M3 Max, iPhone 15 Pro Max, Apple Watch Ultra 2"
            db.commit()

        # 3. Seed / Enrich Fleet Devices for ALL 4 Users
        all_devices = [
            # User 1: Monisha
            {
                "customer_id": "CUST_MONISHA_001",
                "device_identifier": "dev-monisha-ios",
                "device_name": "iPhone 15 Pro",
                "device_type": "mobile_ios",
                "os": "iOS 17.5.1",
                "browser": "Mobile Safari (Biometric Keychain)",
                "browser_or_client": "Mobile Safari",
                "location_region": "Chennai / Adyar",
                "is_trusted": True,
                "is_compromised": False,
                "trust_score": 98,
                "status": "ACTIVE",
            },
            {
                "customer_id": "CUST_MONISHA_001",
                "device_identifier": "dev-monisha-ipad",
                "device_name": "iPad Pro 11-inch M2",
                "device_type": "tablet_ios",
                "os": "iPadOS 17.5",
                "browser": "Mobile Safari",
                "browser_or_client": "Mobile Safari",
                "location_region": "Chennai / Adyar",
                "is_trusted": True,
                "is_compromised": False,
                "trust_score": 92,
                "status": "ACTIVE",
            },
            # User 2: Mohana
            {
                "customer_id": "CUST_MOHANA_002",
                "device_identifier": "dev-mohana-samsung",
                "device_name": "Samsung Galaxy S24 Ultra",
                "device_type": "mobile_android",
                "os": "Android 14 (OneUI 6.1)",
                "browser": "Chrome Mobile 125.0",
                "browser_or_client": "Chrome Mobile",
                "location_region": "Coimbatore / RS Puram",
                "is_trusted": True,
                "is_compromised": False,
                "trust_score": 94,
                "status": "ACTIVE",
            },
            {
                "customer_id": "CUST_MOHANA_002",
                "device_identifier": "dev-mohana-laptop",
                "device_name": "ThinkPad X1 Carbon Gen 11",
                "device_type": "desktop_windows",
                "os": "Windows 11 Pro 23H2",
                "browser": "Chrome 125.0 (Windows Hello)",
                "browser_or_client": "Chrome 125.0",
                "location_region": "Coimbatore / RS Puram",
                "is_trusted": True,
                "is_compromised": False,
                "trust_score": 90,
                "status": "ACTIVE",
            },
            # User 3: Sowmiya
            {
                "customer_id": "CUST_SOWMIYA_003",
                "device_identifier": "dev-sowmiya-pixel",
                "device_name": "Google Pixel 8 Pro",
                "device_type": "mobile_android",
                "os": "Android 14",
                "browser": "Chrome Mobile 125.0",
                "browser_or_client": "Chrome Mobile",
                "location_region": "Bengaluru / Indiranagar",
                "is_trusted": True,
                "is_compromised": False,
                "trust_score": 88,
                "status": "ACTIVE",
            },
            {
                "customer_id": "CUST_SOWMIYA_003",
                "device_identifier": "dev-sowmiya-mac",
                "device_name": "MacBook Air M2",
                "device_type": "desktop_macos",
                "os": "macOS Sonoma 14.4",
                "browser": "Safari 17.4",
                "browser_or_client": "Safari",
                "location_region": "Bengaluru / Indiranagar",
                "is_trusted": True,
                "is_compromised": False,
                "trust_score": 86,
                "status": "ACTIVE",
            },
            {
                "customer_id": "CUST_SOWMIYA_003",
                "device_identifier": "dev-sowmiya-rogue",
                "device_name": "Unknown Android Emulator",
                "device_type": "unknown_bot",
                "os": "Android 11 (Rooted Hooked)",
                "browser": "Generic Webview (Automated Puppeteer)",
                "browser_or_client": "Generic Webview",
                "location_region": "Frankfurt / VPN Proxy",
                "is_trusted": False,
                "is_compromised": True,
                "trust_score": 15,
                "status": "SUSPICIOUS",
            },
            # User 4: Ajay
            {
                "customer_id": "CUST_PREMIUM_004",
                "device_identifier": "dev-mbp-m3",
                "device_name": "MacBook Pro M3 Max",
                "device_type": "desktop_macos",
                "os": "macOS Sonoma 14.5",
                "browser": "Chrome 125.0 (Hardware Enclave)",
                "browser_or_client": "Chrome 125.0",
                "location_region": "Mumbai / Cyber City",
                "is_trusted": True,
                "is_compromised": False,
                "trust_score": 99,
                "status": "ACTIVE",
            },
            {
                "customer_id": "CUST_PREMIUM_004",
                "device_identifier": "dev-iphone-15pm",
                "device_name": "iPhone 15 Pro Max",
                "device_type": "mobile_ios",
                "os": "iOS 17.5.1",
                "browser": "Mobile Safari (Biometric Keychain)",
                "browser_or_client": "Mobile Safari",
                "location_region": "Mumbai / Cyber City",
                "is_trusted": True,
                "is_compromised": False,
                "trust_score": 98,
                "status": "ACTIVE",
            },
            {
                "customer_id": "CUST_PREMIUM_004",
                "device_identifier": "dev-watch-u2",
                "device_name": "Apple Watch Ultra 2",
                "device_type": "wearable_watchos",
                "os": "watchOS 10.5",
                "browser": "Apple Pay Biometric Pass",
                "browser_or_client": "WatchOS Client",
                "location_region": "Mumbai / Cyber City",
                "is_trusted": True,
                "is_compromised": False,
                "trust_score": 96,
                "status": "ACTIVE",
            },
        ]

        for dev_data in all_devices:
            existing_dev = db.query(CustomerDevice).filter(
                CustomerDevice.customer_id == dev_data["customer_id"],
                CustomerDevice.device_identifier == dev_data["device_identifier"],
            ).first()
            if not existing_dev:
                new_dev = CustomerDevice(
                    customer_id=dev_data["customer_id"],
                    device_identifier=dev_data["device_identifier"],
                    device_name=dev_data["device_name"],
                    device_type=dev_data["device_type"],
                    os=dev_data["os"],
                    browser=dev_data["browser"],
                    browser_or_client=dev_data["browser_or_client"],
                    location_region=dev_data["location_region"],
                    is_trusted=dev_data["is_trusted"],
                    is_compromised=dev_data["is_compromised"],
                    trust_score=dev_data["trust_score"],
                    status=dev_data["status"],
                )
                db.add(new_dev)
            else:
                existing_dev.device_name = dev_data["device_name"]
                existing_dev.device_type = dev_data["device_type"]
                existing_dev.os = dev_data["os"]
                existing_dev.browser = dev_data["browser"]
                existing_dev.browser_or_client = dev_data["browser_or_client"]
                existing_dev.location_region = dev_data["location_region"]
                existing_dev.is_trusted = dev_data["is_trusted"]
                existing_dev.is_compromised = dev_data["is_compromised"]
                existing_dev.trust_score = dev_data["trust_score"]
                existing_dev.status = dev_data["status"]
        db.commit()
        print(f"[OK] Fleet Devices seeded & enriched for all 4 users.")

        # 4. Seed / Enrich Fleet Sessions for ALL 4 Users
        all_sessions = [
            # Monisha
            {
                "customer_id": "CUST_MONISHA_001",
                "session_id": "sess-monisha-chennai-01",
                "device_id": "dev-monisha-ios",
                "device_name": "iPhone 15 Pro",
                "ip_address": "49.37.102.14",
                "approximate_location": "Chennai, Tamil Nadu, India",
                "session_status": "ACTIVE",
                "risk_score": 3,
            },
            {
                "customer_id": "CUST_MONISHA_001",
                "session_id": "sess-monisha-ipad-02",
                "device_id": "dev-monisha-ipad",
                "device_name": "iPad Pro 11-inch",
                "ip_address": "49.37.102.14",
                "approximate_location": "Chennai, Tamil Nadu, India",
                "session_status": "ACTIVE",
                "risk_score": 5,
            },
            # Mohana
            {
                "customer_id": "CUST_MOHANA_002",
                "session_id": "sess-mohana-cbe-01",
                "device_id": "dev-mohana-samsung",
                "device_name": "Samsung Galaxy S24 Ultra",
                "ip_address": "117.216.48.91",
                "approximate_location": "Coimbatore, Tamil Nadu, India",
                "session_status": "ACTIVE",
                "risk_score": 12,
            },
            {
                "customer_id": "CUST_MOHANA_002",
                "session_id": "sess-mohana-laptop-02",
                "device_id": "dev-mohana-laptop",
                "device_name": "ThinkPad X1 Carbon Gen 11",
                "ip_address": "117.216.48.91",
                "approximate_location": "Coimbatore, Tamil Nadu, India",
                "session_status": "ACTIVE",
                "risk_score": 8,
            },
            # Sowmiya
            {
                "customer_id": "CUST_SOWMIYA_003",
                "session_id": "sess-sowmiya-blr-01",
                "device_id": "dev-sowmiya-pixel",
                "device_name": "Google Pixel 8 Pro",
                "ip_address": "106.51.98.24",
                "approximate_location": "Bengaluru, Karnataka, India",
                "session_status": "ACTIVE",
                "risk_score": 22,
            },
            {
                "customer_id": "CUST_SOWMIYA_003",
                "session_id": "sess-sowmiya-rogue-02",
                "device_id": "dev-sowmiya-rogue",
                "device_name": "Unknown Android Emulator",
                "ip_address": "185.220.101.5",
                "approximate_location": "Frankfurt, Germany (Tor/Proxy)",
                "session_status": "FLAGGED",
                "risk_score": 82,
            },
            # Ajay
            {
                "customer_id": "CUST_PREMIUM_004",
                "session_id": "sess-ajay-mumbai-01",
                "device_id": "dev-mbp-m3",
                "device_name": "MacBook Pro M3 Max",
                "ip_address": "49.37.142.88",
                "approximate_location": "Mumbai / Cyber City, India",
                "session_status": "ACTIVE",
                "risk_score": 4,
            },
            {
                "customer_id": "CUST_PREMIUM_004",
                "session_id": "sess-ajay-blr-02",
                "device_id": "dev-iphone-15pm",
                "device_name": "iPhone 15 Pro Max",
                "ip_address": "106.51.72.19",
                "approximate_location": "Bangalore Tech Corridor, India",
                "session_status": "ACTIVE",
                "risk_score": 7,
            },
        ]

        # Look up user IDs for all 4 accounts
        u_monisha = db.query(User).filter(User.email == "monisha@fraudlens.ai").first()
        u_mohana = db.query(User).filter(User.email == "mohana@fraudlens.ai").first()
        u_sowmiya = db.query(User).filter(User.email == "sowmiya@fraudlens.ai").first()
        u_ajay = db.query(User).filter(User.email.in_(["ajay@fraudlens.ai", "premium@fraudlens.ai"])).first()

        user_id_map = {
            "CUST_MONISHA_001": u_monisha.id if u_monisha else 11,
            "CUST_MOHANA_002": u_mohana.id if u_mohana else 12,
            "CUST_SOWMIYA_003": u_sowmiya.id if u_sowmiya else 13,
            "CUST_PREMIUM_004": u_ajay.id if u_ajay else 15,
        }

        for s_data in all_sessions:
            uid = user_id_map.get(s_data["customer_id"], 15)
            existing_s = db.query(UserSession).filter(
                UserSession.customer_id == s_data["customer_id"],
                UserSession.session_id == s_data["session_id"],
            ).first()
            if not existing_s:
                new_s = UserSession(
                    user_id=uid,
                    customer_id=s_data["customer_id"],
                    session_id=s_data["session_id"],
                    device_id=s_data["device_id"],
                    device_name=s_data["device_name"],
                    ip_address=s_data["ip_address"],
                    approximate_location=s_data["approximate_location"],
                    session_status=s_data["session_status"],
                    risk_score=s_data["risk_score"],
                )
                db.add(new_s)
            else:
                existing_s.user_id = uid
                existing_s.session_status = s_data["session_status"]
                existing_s.risk_score = s_data["risk_score"]
                existing_s.approximate_location = s_data["approximate_location"]
                existing_s.device_name = s_data["device_name"]
        db.commit()
        print(f"[OK] Fleet Sessions seeded & active for all 4 users.")

        # 5. Generate Pure Dataset for Ajay (dataset_customer_ajay_pure.csv)
        num_records = 1500
        end_date = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=2)
        start_date = end_date - datetime.timedelta(days=90)
        current_time = start_date
        delta_minutes = (90 * 24 * 60) / num_records

        # Ajay Pure Dataset: 0.2% fraud rate (only 3 anomalous test records out of 1500)
        num_fraud_records = 3
        fraud_indices = {145, 680, 1290}

        ajay_records = []
        for idx in range(1, num_records + 1):
            tx_id = f"TXN-CUST_PREMIUM_004-{10000 + idx}"
            jitter = random.uniform(-2.5, 2.5)
            current_time += datetime.timedelta(minutes=max(delta_minutes + jitter, 1.0))
            
            tx_hour = current_time.hour
            tx_dow = current_time.weekday()
            is_weekend = 1 if tx_dow >= 5 else 0
            is_night = 1 if (tx_hour >= 23 or tx_hour <= 5) else 0

            merchant = random.choice(MERCHANTS_MASTER)
            is_fraud = 1 if idx in fraud_indices else 0

            if is_fraud:
                fraud_type = "Unusual Off-Hours Cloud Compute Surge"
                fraud_stage = "Step-Up OTP Intercept"
                fraud_scenario = "Off-hours burst from secondary IP requiring biometric step-up"
                amount = float(round(merchant["merchant_average_ticket"] * random.uniform(1.8, 2.5), 2))
                is_new_dev = 0
                is_trusted_dev = 1
                dev_id = "dev-iphone-15pm"
                dev_type = "mobile_ios"
                curr_loc = "Delhi NCR"
                loc_dist = float(random.randint(900, 1200))
                tx_1h = 3
                tx_24h = 6
                failed_logins = 1
                failed_txs = 0
                pw_changed = 0
                is_new_ben = 0
                ben_id = "BEN-CUST_PREMIUM_004-CF"
                ben_name = "Cloudflare Global Services"
                ben_count = 14
            else:
                fraud_type = "None"
                fraud_stage = "Resolved Genuine"
                fraud_scenario = "Standard Enterprise Settlement"
                amount = float(round(random.choice([12500, 24000, 38500, 45000, 62000, 85000]) * random.uniform(0.7, 1.3), 2))
                is_new_dev = 0
                is_trusted_dev = 1
                dev_id = "dev-mbp-m3" if random.random() < 0.75 else "dev-iphone-15pm"
                dev_type = "desktop_macos" if dev_id == "dev-mbp-m3" else "mobile_ios"
                curr_loc = "Mumbai"
                loc_dist = float(random.randint(1, 12))
                tx_1h = 1 if random.random() < 0.15 else 0
                tx_24h = random.randint(1, 4)
                failed_logins = 0
                failed_txs = 0
                pw_changed = 0
                is_new_ben = 0
                ben_id = "BEN-CUST_PREMIUM_004-TRUSTED"
                ben_name = random.choice(["Cloudflare Global Services", "AWS Enterprise Cloud", "Stripe Global Settlement"])
                ben_count = random.randint(10, 40)

            record = {
                "transaction_id": tx_id,
                "transaction_datetime": current_time.strftime("%Y-%m-%d %H:%M:%S"),
                "transaction_date": current_time.strftime("%Y-%m-%d"),
                "transaction_time": current_time.strftime("%H:%M:%S"),
                "transaction_hour": tx_hour,
                "day_of_week": tx_dow,
                "is_weekend": is_weekend,
                "is_night_transaction": is_night,
                "customer_id": "CUST_PREMIUM_004",
                "customer_account_age_days": 730,
                "customer_usual_location": "Mumbai",
                "customer_usual_state": "Maharashtra",
                "customer_risk_segment": "Enterprise Security / 0.2% Clean Baseline",
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
                "transaction_type": "TRANSFER",
                "payment_channel": random.choice(["TRANSFER", "ONLINE", "NETBANKING"]),
                "transaction_channel": "WEB_PORTAL" if dev_type == "desktop_macos" else "MOBILE_APP",
                "card_present": 0,
                "is_international": 0,
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
                "customer_tx_count_last_7d": tx_24h * 3 + random.randint(1, 5),
                "failed_login_attempts_last_24h": failed_logins,
                "failed_transaction_attempts_last_24h": failed_txs,
                "recent_password_reset_flag": pw_changed,
                "fraud_scenario_type": fraud_type,
                "fraud_lifecycle_stage": fraud_stage,
                "synthetic_fraud_scenario_description": fraud_scenario,
                "is_fraud": is_fraud,
            }
            ajay_records.append(record)

        df_ajay = pd.DataFrame(ajay_records)
        ajay_csv_path = "data/raw/dataset_customer_ajay_pure.csv"
        df_ajay.to_csv(ajay_csv_path, index=False)
        print(f"[OK] Ajay Pure Dataset saved: {ajay_csv_path} with {len(df_ajay)} records (Fraud Rate: {df_ajay['is_fraud'].mean():.1%})")

    finally:
        db.close()

if __name__ == "__main__":
    run()
