import sqlite3

conn = sqlite3.connect("fraud_detection.db")
cur = conn.cursor()

print("=== 4 CORE DEMO USERS / CUSTOMERS IN DATABASE ===")
core_ids = ['CUST_MONISHA_001', 'CUST_MOHANA_002', 'CUST_SOWMIYA_003', 'CUST_REAL_001']
for cid in core_ids:
    row = cur.execute("SELECT customer_id, name, email, simulated_balance, risk_segment FROM customers WHERE customer_id = ?", (cid,)).fetchone()
    if row:
        bal = row[3] if row[3] is not None else 0.0
        print(f"Customer ID : {row[0]}")
        print(f"Name        : {row[1]}")
        print(f"Email       : {row[2]}")
        print(f"Balance     : Rs.{bal:,.2f}")
        print(f"Risk Segment: {row[4]}")
        print("-" * 50)

print("\n=== ARE TRANSACTIONS ISOLATED PER USER? ===")
for cid in core_ids:
    tx_count = cur.execute("SELECT count(*) FROM transactions WHERE customer_id = ?", (cid,)).fetchone()[0]
    tx_sum = cur.execute("SELECT sum(amount) FROM transactions WHERE customer_id = ?", (cid,)).fetchone()[0] or 0.0
    fraud_count = cur.execute("SELECT count(*) FROM transactions WHERE customer_id = ? AND is_fraud = 1", (cid,)).fetchone()[0]
    dev_count = cur.execute("SELECT count(*) FROM customer_devices WHERE customer_id = ?", (cid,)).fetchone()[0]
    ben_count = cur.execute("SELECT count(*) FROM beneficiaries WHERE customer_id = ?", (cid,)).fetchone()[0]
    print(f"[{cid}]")
    print(f"  • Total Transactions : {tx_count} records (Fraudulent: {fraud_count})")
    print(f"  • Total Volume       : Rs.{tx_sum:,.2f}")
    print(f"  • Enrolled Devices   : {dev_count} unique devices")
    print(f"  • Beneficiaries      : {ben_count} saved beneficiaries")
    print()
