import sqlite3

conn = sqlite3.connect('fraud_detection.db')
cur = conn.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [r[0] for r in cur.fetchall()]
print("Tables found in fraud_detection.db:")
for t in tables:
    if not t.startswith("sqlite"):
        cur.execute(f"SELECT COUNT(*) FROM {t}")
        cnt = cur.fetchone()[0]
        cur.execute(f"PRAGMA table_info({t})")
        cols = [c[1] for c in cur.fetchall()]
        print(f"  {t} ({cnt} rows): {cols}")
cur.close()
conn.close()
