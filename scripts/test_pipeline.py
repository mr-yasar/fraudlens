import pandas as pd
from ml.features.feature_engineer import FraudFeatureEngineer
from ml.preprocessing.pipeline import FullFraudPreprocessor

df = pd.read_csv('data/raw/financial_fraud_customer_transactions.csv')
X = df.drop(columns=['Fraud_Label'])
y = df['Fraud_Label']

fe = FraudFeatureEngineer()
X_eng = fe.fit_transform(X)
print("Input shape:", X.shape)
print("Engineered shape:", X_eng.shape)
print("Engineered columns:", list(X_eng.columns))
print("Leakage columns in X_eng:", [c for c in ['Fraud_Probability', 'Risk_Score', 'Risk_Level', 'Fraud_Label', 'Transaction_ID', 'Customer_ID', 'Transaction_Number'] if c in X_eng.columns])

preprocessor = FullFraudPreprocessor()
X_trans = preprocessor.fit_transform(X)
print("\nPreprocessor output shape:", X_trans.shape)
feature_names = preprocessor.get_feature_names_out()
print(f"Total features after preprocessor: {len(feature_names)}")
print("Sample feature names:", feature_names[:10])
