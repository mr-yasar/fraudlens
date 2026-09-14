import sqlite3

conn = sqlite3.connect('e:/fraudinvestigation/fraud_detection.db')
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
print('Tables:', cursor.fetchall())
for table in ['users', 'customers', 'transactions', 'investigations', 'shap_explanations', 'model_versions', 'audit_logs']:
    try:
        cursor.execute(f"SELECT count(*) FROM {table}")
        print(f"{table}: {cursor.fetchone()[0]} rows")
    except Exception as e:
        print(f"{table}: {e}")

cursor.execute("SELECT email, role, is_active FROM users")
print("\nUsers:", cursor.fetchall())
conn.close()
