import sys
import os

from backend.app.core.database import SessionLocal
from backend.app.models.customer import Customer

def main():
    db = SessionLocal()
    try:
        customers = db.query(Customer).all()
        for c in customers:
            c.simulated_balance += 1000000.0
        db.commit()
        print(f"Added 10 Lakh (1,000,000) to {len(customers)} customers.")
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    main()
