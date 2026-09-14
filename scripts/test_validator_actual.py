from ml.validation.dataset_validator import DatasetValidator

validator = DatasetValidator()
res = validator.validate_file('data/raw/financial_fraud_customer_transactions.csv')
print('Is Valid:', res.is_valid)
print('Errors:', res.errors)
print('Warnings:', res.warnings[:5])
print('Target Analysis:', res.target_analysis)
print(f"Excluded Features count: {len(res.leakage_audit['excluded_features'])}")
for ef in res.leakage_audit['excluded_features']:
    print(f"  - {ef['feature']}: {ef['reason']}")
print(f"Safe Features count: {len(res.leakage_audit['safe_features'])}")
for sf in res.leakage_audit['safe_features']:
    print(f"  + {sf['feature']}")
