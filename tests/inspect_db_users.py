import sys
sys.path.insert(0, '.')
from backend.app.core.database import SessionLocal
from backend.app.models.user import User
from backend.app.models.customer import Customer
from backend.app.models.transaction import Transaction
from sqlalchemy import func

db = SessionLocal()
users = db.query(User).all()
print("=== USERS IN DATABASE ===")
for u in users:
    print(f"ID: {u.id}, Name: {u.name}, Email: {u.email}, Role: {u.role}")

print("\n=== PERSONA CUSTOMER IDS IN TRANSACTIONS ===")
tx_custs = db.query(Transaction.customer_id, func.count(Transaction.id)).group_by(Transaction.customer_id).all()
for c, cnt in tx_custs:
    if any(k in str(c).upper() for k in ["MONISHA", "MOHANA", "MOGANA", "SOWMIYA", "AJAY"]):
        print(f"{c}: {cnt} transactions")

print(f"Total distinct customer_ids in Transactions: {len(tx_custs)}")

customers = db.query(Customer).all()
print("\n=== CUSTOMERS TABLE ===")
for cust in customers:
    print(f"ID: {cust.id}, Customer_ID: {cust.customer_id}, Email: {cust.email}")
