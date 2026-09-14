import pandas as pd
import json

df = pd.read_csv('e:/fraudinvestigation/data/raw/financial_fraud_customer_transactions.csv')
print(f"=== DATASET OVERVIEW ===")
print(f"Total Rows: {len(df)}")
print(f"Total Columns: {len(df.columns)}")
print(f"Columns: {list(df.columns)}")

print(f"\n=== MISSING VALUES ===")
nulls = df.isnull().sum()
print(nulls[nulls > 0] if (nulls > 0).any() else "No missing values!")

print(f"\n=== TARGET DISTRIBUTION (Fraud_Label) ===")
counts = df['Fraud_Label'].value_counts()
pcts = df['Fraud_Label'].value_counts(normalize=True) * 100
for val, count in counts.items():
    print(f"Label {val}: {count} rows ({pcts[val]:.2f}%)")

print(f"\n=== REFERENCE COLUMNS SUMMARY ===")
if 'Risk_Level' in df.columns:
    print("Risk_Level:", df['Risk_Level'].value_counts().to_dict())
if 'Risk_Score' in df.columns:
    print(f"Risk_Score: min={df['Risk_Score'].min()}, max={df['Risk_Score'].max()}, mean={df['Risk_Score'].mean():.2f}")
if 'Fraud_Probability' in df.columns:
    print(f"Fraud_Probability: min={df['Fraud_Probability'].min()}, max={df['Fraud_Probability'].max()}, mean={df['Fraud_Probability'].mean():.4f}")

print(f"\n=== CATEGORICAL FEATURES ===")
for col in ['Transaction_Type', 'Location', 'Usual_Location', 'Device_Type']:
    print(f"{col} ({df[col].nunique()} unique): {df[col].unique().tolist()}")

print(f"\n=== BINARY / COUNT FEATURES ===")
for col in ['New_Device', 'Unusual_Location', 'International_Transaction', 'Failed_Attempts', 'Transactions_Last_24H']:
    print(f"{col}: {df[col].value_counts().to_dict()}")

print(f"\n=== NUMERICAL FEATURES STATS ===")
num_cols = ['Amount', 'Transaction_Hour', 'Account_Age_Days', 'Previous_Transaction_Amount', 'Average_Previous_Amount', 'Amount_Deviation', 'Amount_Ratio']
print(df[num_cols].describe().T[['min', 'mean', '50%', 'max']])
