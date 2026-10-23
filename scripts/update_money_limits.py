"""Update money limits / available balances for Monisha, Mohana, Sowmiya, and Ajay."""
import sqlite3
import os

BALANCE_MAP = {
    "CUST_MONISHA_001": 45000.0,
    "CUST_MOHANA_002": 60000.0,
    "CUST_SOWMIYA_003": 80000.0,
    "CUST_AJAY_004": 300000.0,
    "CUST_PREMIUM_004": 300000.0,
}

DB_PATHS = [
    "fraud_detection.db",
    "backend/fraud_detection.db",
    "backend/fraudlens.db",
]

def main():
    for db_path in DB_PATHS:
        if not os.path.exists(db_path):
            continue
        try:
            con = sqlite3.connect(db_path)
            cur = con.cursor()
            tables = [r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
            if "customers" not in tables:
                con.close()
                continue
            
            for cid, bal in BALANCE_MAP.items():
                cur.execute("UPDATE customers SET simulated_balance = ? WHERE customer_id = ?", (bal, cid))
            
            cur.execute("UPDATE customers SET simulated_balance = 45000.0 WHERE name = 'Monisha'")
            cur.execute("UPDATE customers SET simulated_balance = 60000.0 WHERE name = 'Mohana'")
            cur.execute("UPDATE customers SET simulated_balance = 80000.0 WHERE name = 'Sowmiya'")
            cur.execute("UPDATE customers SET simulated_balance = 300000.0 WHERE name = 'Ajay'")
            con.commit()

            rows = cur.execute(
                "SELECT customer_id, name, email, simulated_balance FROM customers "
                "WHERE customer_id IN ('CUST_MONISHA_001', 'CUST_MOHANA_002', 'CUST_SOWMIYA_003', 'CUST_AJAY_004', 'CUST_PREMIUM_004')"
            ).fetchall()
            print(f"[OK] Database '{db_path}' updated successfully:")
            for r in rows:
                print(f"  - {r[0]} ({r[1]}): INR {r[3]:,.2f}")
            con.close()
        except Exception as exc:
            print(f"[ERROR] updating {db_path}: {exc}")

if __name__ == "__main__":
    main()
