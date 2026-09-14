import pandas as pd
from backend.app.services.prediction_service import FraudPredictionService
from backend.app.schemas.prediction import TransactionPredictionInput

df = pd.read_csv('data/raw/financial_fraud_customer_transactions.csv')
sample_fraud = df[df['Fraud_Label'] == 1].iloc[0].to_dict()
sample_genuine = df[df['Fraud_Label'] == 0].iloc[0].to_dict()

svc = FraudPredictionService.get_instance()
print("Service active model:", svc.model_name, "version:", svc.model_version, "threshold:", svc.threshold)

print("\n--- Testing Genuine Sample from CSV ---")
input_gen = TransactionPredictionInput(**sample_genuine)
res_gen = svc.predict_transaction(input_gen)
print(f"TxID: {res_gen.transaction_id}")
print(f"Prediction: {res_gen.prediction}")
print(f"Fraud Probability: {res_gen.fraud_probability}")
print(f"Risk Score: {res_gen.risk_score} ({res_gen.risk_level})")
print(f"Risk Factors Count: {len(res_gen.risk_factors)}")
if res_gen.top_shap_factors:
    print(f"Top SHAP Factors ({len(res_gen.top_shap_factors)}):")
    for f in res_gen.top_shap_factors:
        print(f"  - {f['feature_name']}: SHAP={f['shap_value']:.4f} ({f['impact']})")

print("\n--- Testing Fraud Sample from CSV ---")
input_fraud = TransactionPredictionInput(**sample_fraud)
res_fraud = svc.predict_transaction(input_fraud)
print(f"TxID: {res_fraud.transaction_id}")
print(f"Prediction: {res_fraud.prediction}")
print(f"Fraud Probability: {res_fraud.fraud_probability}")
print(f"Risk Score: {res_fraud.risk_score} ({res_fraud.risk_level})")
print(f"Risk Factors Count: {len(res_fraud.risk_factors)}")
if res_fraud.top_shap_factors:
    print(f"Top SHAP Factors ({len(res_fraud.top_shap_factors)}):")
    for f in res_fraud.top_shap_factors:
        print(f"  - {f['feature_name']}: SHAP={f['shap_value']:.4f} ({f['impact']})")

print("\n--- Testing Full Local SHAP Explanation ---")
exp = svc.explain_transaction(input_fraud, top_k=3)
print(f"Base value: {exp.base_value}")
print(f"Top Risk Increasing: {len(exp.top_risk_increasing_factors)}")
for f in exp.top_risk_increasing_factors:
    print(f"  + {f['feature_name']}: {f['shap_value']} ({f['detail']})")
print(f"Top Risk Decreasing: {len(exp.top_risk_decreasing_factors)}")
for f in exp.top_risk_decreasing_factors:
    print(f"  - {f['feature_name']}: {f['shap_value']} ({f['detail']})")
