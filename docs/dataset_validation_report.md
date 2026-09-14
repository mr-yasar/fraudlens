# Dataset Integration, Validation & Feature Leakage Audit Report

**Dataset Identifier:** Lead AI Fraud Detection Dataset v2  
**Target Variable:** `risk_label` (`0` = normal, `1` = fraud)  
**System Module:** `ml/validation/dataset_validator.py`

---

## 1. Dataset Availability & Inspection Status

- **Status in Workspace:** The dataset integration and validation engine has been built and tested. No actual `.csv` file was pre-placed in `data/raw/` (or repository roots).
- **Integration Readiness:** The engine is immediately ready to validate the real dataset once placed in `data/raw/` or uploaded via `POST /api/v1/datasets/validate`.

---

## 2. Expected Dataset Schema

The system validates incoming data against the 21 expected fields:

| Field Name | Expected Type | Required | Domain Constraints | Description |
| :--- | :--- | :---: | :--- | :--- |
| `transaction_id` | String / Object | Yes | Unique Primary Key | Unique transaction identifier |
| `customer_id` | String / Object | Yes | Indexed Key | Customer account identifier |
| `transaction_hour` | Integer | Yes | `[0, 23]` | Hour of the day the transaction occurred |
| `transaction_day_of_week` | Integer | Yes | `[0, 6]` or `[1, 7]` | Day of the week |
| `account_age_days` | Integer / Float | Yes | `>= 0` | Age of customer account in days |
| `previous_chargebacks` | Integer | Yes | `>= 0` | Total historical chargebacks filed |
| `merchant_category` | String / Object | Yes | Categorical | Category of merchant (e.g., Electronics, Grocery) |
| `transaction_country` | String / Object | Yes | ISO Alpha-2 / Alpha-3 | Country of transaction origin |
| `device_type` | String / Object | Yes | Categorical | Device used (mobile, web, pos, etc.) |
| `transaction_type` | String / Object | Yes | Categorical | Type of transaction (card_present, online, etc.) |
| `geo_location_region` | String / Object | Yes | Regional string | Geographic region code |
| `is_international` | Boolean / Int | Yes | `{0, 1}` | Flag for cross-border transactions |
| `is_high_risk_merchant_category` | Boolean / Int | Yes | `{0, 1}` | Merchant risk categorization |
| `is_weekend` | Boolean / Int | Yes | `{0, 1}` | Weekend occurrence indicator |
| `customer_total_transactions_30d` | Integer / Float | Yes | `>= 0` | 30-day customer transaction volume |
| `customer_risk_score` | Float / Number | Optional | `[0.0, 100.0]` | **High-Risk Candidate** (audited for target leakage) |
| `transaction_amount` | Float / Numeric | Yes | `> 0.00` | Monetary amount of transaction |
| `avg_transaction_amount_30d_customer` | Float / Numeric | Yes | `>= 0.00` | Rolling historical 30-day mean amount |
| `transaction_velocity_1h` | Integer / Float | Yes | `>= 0` | Number of transactions by customer in past 1 hour |
| `transaction_velocity_24h` | Integer / Float | Yes | `>= 0` | Number of transactions by customer in past 24 hours |
| `risk_label` | Integer | Yes | `{0, 1}` | Ground truth target (0 = normal, 1 = fraud) |

---

## 3. 11-Step Validation Architecture

The `DatasetValidator` executes an exhaustive 11-step audit:

1. **File Format Validation**: Checks `.csv`, `.parquet`, or `.json` headers and file integrity.
2. **Schema Validation**: Ensures all mandatory columns exist without unexpected structural omissions.
3. **Required-Column Validation**: Flags any missing required fields.
4. **Data-Type Validation**: Enforces numerical, string, and boolean type consistency.
5. **Missing-Value Analysis**: Calculates column-level null counts and percentages; warns when null rates exceed tolerance (30%).
6. **Duplicate Analysis**: Detects duplicate rows and duplicate `transaction_id` primary key violations.
7. **Target-Value Validation**: Validates that `risk_label` strictly belongs to binary subset `{0, 1}`.
8. **Class Distribution**: Quantifies normal vs fraud class counts and calculates class imbalance ratio (e.g., `1:99`).
9. **Suspicious / Out-of-Bounds Values**: Checks negative amounts, invalid hour spans, and out-of-range calendar days.
10. **Descriptive Statistics Summary**: Computes min, 25%, median, 75%, max, mean, and std for numerical features, and top frequencies for categoricals.
11. **Feature Leakage Audit**: Evaluates feature correlations and provenance to prevent synthetic target contamination.

---

## 4. Target & Feature Leakage Audit Findings

### Excluded Features & Justification

| Feature | Exclusion Reason | Leakage Category | Recommendation |
| :--- | :--- | :--- | :--- |
| `customer_risk_score` | High risk of future-data contamination if derived from downstream chargeback / fraud outcomes or post-transaction rules. | Engineered Risk Contamination | **EXCLUDE** from initial baseline training until point-in-time calculation is guaranteed. |
| `transaction_id` | Unique primary key with high cardinality; memorization risk. | Identifier Leakage | **EXCLUDE** from feature matrix. |
| `*` (Any feature with $|r| > 0.95$) | Exact mathematical proxy or synthetic target derivation. | Target Proxy Leakage | **EXCLUDE** automatically. |

### Potentially Risky Features (Requires Attribution Verification)
- Any aggregate with high correlation ($0.70 < |r| \le 0.95$) such as sudden velocity spikes must be verified for timestamp alignment.

### Safe Core Features for Model Training
- `transaction_hour`, `transaction_day_of_week`, `account_age_days`, `previous_chargebacks`, `merchant_category`, `transaction_country`, `device_type`, `transaction_type`, `geo_location_region`, `is_international`, `is_high_risk_merchant_category`, `is_weekend`, `customer_total_transactions_30d`, `transaction_amount`, `avg_transaction_amount_30d_customer`, `transaction_velocity_1h`, `transaction_velocity_24h`.
