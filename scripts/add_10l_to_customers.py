import os
import sys

# Add the project root to the python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.app.core.database import SessionLocal
from backend.app.models.customer import Customer
from sqlalchemy import update

def add_10_lakh_to_customers():
    db = SessionLocal()
    try:
        # Add 10,00,000 (10 Lakh) to simulated_balance for all customers
        customers = db.query(Customer).all()
        count = 0
        for customer in customers:
            customer.simulated_balance += 1000000.0
            count += 1
            
        db.commit()
        print(f"Successfully added 10 Lakh (1,000,000) to {count} customers' balances.")
    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    add_10_lakh_to_customers()
