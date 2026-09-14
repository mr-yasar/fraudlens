"""Seed database with real records from financial_fraud_customer_transactions.csv without deleting any existing data."""

import json
from pathlib import Path
import pandas as pd
from sqlalchemy.orm import Session

from backend.app.core.database import SessionLocal
from backend.app.models.customer import Customer
from backend.app.models.transaction import Transaction
from backend.app.models.model_version import ModelVersion
from backend.app.models.shap_explanation import ShapExplanation
from backend.app.services.prediction_service import FraudPredictionService
from backend.app.schemas.prediction import TransactionPredictionInput


def seed_real_dataset():
    db: Session = SessionLocal()
    try:
        csv_path = Path("data/raw/financial_fraud_customer_transactions.csv")
        if not csv_path.exists():
            print("[ERROR] CSV not found at", csv_path)
            return

        df = pd.read_csv(csv_path)
        print(f"[INFO] Loaded CSV with {len(df)} records.")

        # 1. Seed Model Versions if empty
        if db.query(ModelVersion).count() == 0:
            reg_path = Path("ml/artifacts/model_registry.json")
            if reg_path.exists():
                with open(reg_path, "r", encoding="utf-8") as f:
                    reg_data = json.load(f)
                active_model_name = reg_data.get("active_model", "logistic_regression")
                for m_name, m_info in reg_data.get("models", {}).items():
                    mv = ModelVersion(
                        model_name=m_name,
                        version=m_info.get("model_version", "v1.0.0"),
                        accuracy=m_info.get("test_accuracy"),
                        precision=m_info.get("test_precision"),
                        recall=m_info.get("test_recall"),
                        f1_score=m_info.get("test_f1"),
                        roc_auc=m_info.get("test_roc_auc"),
                        pr_auc=m_info.get("test_pr_auc"),
                        model_path=f"ml/artifacts/{m_name}.joblib",
                        is_active=(m_name == active_model_name),
                    )
                    db.add(mv)
                db.commit()
                print("[INFO] Seeded model_versions into database.")

        # 2. Seed Customers from CSV (top 50 distinct customers)
        distinct_custs = df.drop_duplicates(subset=["Customer_ID"])
        existing_cust_ids = set(r[0] for r in db.query(Customer.customer_id).all())
        new_cust_count = 0

        for _, row in distinct_custs.head(50).iterrows():
            cid = str(row["Customer_ID"])
            if cid not in existing_cust_ids:
                c = Customer(
                    customer_id=cid,
                    account_age_days=int(row["Account_Age_Days"]) if pd.notnull(row["Account_Age_Days"]) else 365,
                )
                db.add(c)
                existing_cust_ids.add(cid)
                new_cust_count += 1

        db.commit()
        print(f"[INFO] Added {new_cust_count} new customer records from CSV.")

        # 3. Seed Transactions from CSV (e.g. first 150 rows, preserving existing transactions)
        existing_tx_ids = set(r[0] for r in db.query(Transaction.transaction_id).all())
        new_tx_count = 0

        prediction_service = FraudPredictionService.get_instance()

        for _, row in df.head(150).iterrows():
            tx_id = str(row["Transaction_ID"])
            cust_id = str(row["Customer_ID"])

            # Ensure customer is in DB
            if cust_id not in existing_cust_ids:
                c = Customer(
                    customer_id=cust_id,
                    account_age_days=int(row["Account_Age_Days"]) if pd.notnull(row["Account_Age_Days"]) else 365,
                )
                db.add(c)
                existing_cust_ids.add(cust_id)
                db.flush()

            if tx_id not in existing_tx_ids:
                # Score with active model & risk engine
                row_dict = row.to_dict()
                pred_input = TransactionPredictionInput(**row_dict)
                pred_res = prediction_service.predict_transaction(pred_input, include_shap_summary=True)

                t = Transaction(
                    transaction_id=tx_id,
                    customer_id=cust_id,
                    amount=float(row["Amount"]),
                    transaction_hour=int(row["Transaction_Hour"]),
                    merchant_category=str(row.get("Transaction_Type", "Purchase")),
                    transaction_country="IN" if int(row.get("International_Transaction", 0)) == 0 else "INTL",
                    geo_location_region=str(row.get("Location", "Unknown")),
                    device_type=str(row.get("Device_Type", "Unknown")),
                    transaction_type=str(row.get("Transaction_Type", "Purchase")),
                    fraud_probability=pred_res.fraud_probability,
                    prediction=1 if pred_res.prediction == "FRAUD" else 0,
                    risk_score=float(pred_res.risk_score),
                    risk_level=pred_res.risk_level,
                )
                db.add(t)
                existing_tx_ids.add(tx_id)
                new_tx_count += 1

                # Add SHAP explanations if any
                if pred_res.top_shap_factors:
                    for sf in pred_res.top_shap_factors:
                        shap_entry = ShapExplanation(
                            transaction_id=tx_id,
                            feature_name=sf.get("feature_name", "unknown"),
                            shap_value=float(sf.get("shap_value", 0.0)),
                            impact=sf.get("impact", "neutral"),
                        )
                        db.add(shap_entry)

        db.commit()
        print(f"[INFO] Added {new_tx_count} real scored transactions from CSV to database.")
        print(f"[INFO] Total transactions in DB now: {db.query(Transaction).count()}")

    finally:
        db.close()


if __name__ == "__main__":
    seed_real_dataset()
