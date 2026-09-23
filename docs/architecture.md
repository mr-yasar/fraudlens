# FraudLens AI — System Architecture & Workflow Specification

## 1. System Overview

FraudLens AI is an explainable machine-learning-based financial fraud and risk detection system. The platform evaluates newly submitted financial transactions immediately through an application/API-based workflow, assigning calibrated fraud probabilities, independent 0–100 risk scores, risk levels (LOW / MEDIUM / HIGH), and human-interpretable SHAP feature attributions.

```text
[ Client Applications / User Interface ]
                   │
                   ▼ (HTTP REST / WebSocket)
       [ FastAPI Backend Service ]
       ├── CORS, GZip & Lifespan Pre-Warming
       ├── API Routes (/api/v1/transactions, /predictions, /investigations, /admin)
       ├── Authentication & RBAC (JWT + Bcrypt)
       └── Database Session Manager (SQLAlchemy 2.0)
                   │
       ┌───────────┴───────────────────────────────┐
       ▼                                           ▼
[ SQLite Database (WAL Mode) ]          [ Machine Learning & XAI Engine ]
- users                                 - FullFraudPreprocessor (Fitted ColumnTransformer)
- customers                             - Candidate Models (Logistic Reg, RF, XGBoost, Stacking)
- transactions                          - RiskScoringEngine (Independent 0–100 Risk Metric)
- investigations                        - FraudShapExplainer (TreeSHAP & LinearSHAP)
- shap_explanations                     - Anomaly & Counterfactual Engines
- model_versions                        - ModelSelector & Benchmark Registry
- audit_logs & alerts
```

---

## 2. End-to-End Workflow

```text
Historical Dataset (financial_fraud_customer_transactions.csv)
        ↓
Dataset Validation & Leakage Audit
        ↓
Preprocessing & Feature Engineering (FullFraudPreprocessor)
        ↓
Model Training & Benchmarking (LR / RF / XGBoost / Ensemble)
        ↓
Validated Active Champion Model
        ↓
New Transaction Submission
        ↓
Pydantic Input Validation
        ↓
Identical Fitted Preprocessing Pipeline
        ↓
ML Inference (Fraud Probability [0.0, 1.0])
        ↓
Independent Multi-Factor Risk Scoring (0–100 Score & Tier)
        ↓
SHAP Feature Attribution (Local Explanation)
        ↓
High-Risk Trigger → Fraud Alert → Investigation Case
        ↓
Fraud Investigator Review & Decision (CONFIRMED_FRAUD / GENUINE)
        ↓
Case Resolution & Audit Trail
        ↓
Dashboard Monitoring & Compliance Reporting
```

---

## 3. Database Schema Design

1. **`users`**: System accounts for `ADMIN` and `FRAUD_INVESTIGATOR` users with hashed credentials and active status flags.
2. **`customers`**: Customer profiles tracking unique identifiers, account age in days, and historical tenure.
3. **`transactions`**: Evaluated financial transaction records with amounts, categories, geolocations, devices, fraud probabilities, risk scores, and classifications.
4. **`investigations`**: Case management records linking flagged transactions to investigator determinations, status progression, and notes.
5. **`shap_explanations`**: Feature-level SHAP values explaining why individual transactions were flagged.
6. **`model_versions`**: Audit trail and metric records for candidate and active ML models.
7. **`audit_logs`**: Immutable security and administrative compliance event trail.
8. **`alerts`**: Real-time security triggers and high-risk notifications.
9. **`payment_intents` & `payment_attempts`**: Operational transaction simulation and verification records.

---

## 4. Key Design Principles

* **Real Functionality:** All ML inference and SHAP explainability calculations are computed against real fitted pipelines.
* **Risk Score Independence:** Model fraud probability ($[0.0, 1.0]$) and composite business risk score ($[0, 100]$) are strictly separated.
* **Scope Integrity:** The platform serves as an explainable risk and fraud evaluation engine, without claiming direct banking gateway authorization or funds settlement.
