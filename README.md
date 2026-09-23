# FraudLens AI — Explainable AI-Based Financial Fraud & Risk Detection System

FraudLens AI is an explainable machine-learning-based financial fraud and risk detection system. The system learns fraud-related patterns from historical transaction data (`financial_fraud_customer_transactions.csv`) and evaluates newly submitted transactions immediately through an application/API-based workflow.

> **Scope Note:** FraudLens AI evaluates application-level transaction fraud risk and provides human-interpretable SHAP explanations. It does not claim direct integration with banking authorization infrastructure or guaranteed fraud prevention.

---

## 🚀 Key Features

* **Real-Time Transaction Evaluation:** Immediate scoring of newly submitted transactions against active ML models and multi-factor risk engines.
* **Calibrated Fraud Probability:** Continuous model probability ($0.0 \rightarrow 1.0$) with cost-sensitive decision thresholding.
* **Independent 0–100 Risk Scoring:** Deterministic risk scoring combining behavioral velocity, amount abnormalities, geolocation signals, failed attempts, and ML probabilities into clear tiers:
  * `0 – 30` : **LOW**
  * `31 – 70` : **MEDIUM**
  * `71 – 100` : **HIGH**
* **Explainable AI (SHAP):** Local feature attribution via TreeSHAP/LinearSHAP, explaining exactly why each transaction was flagged, plus cached global feature importances.
* **Investigation & Case Management:** End-to-end investigation lifecycle (`OPEN` → `UNDER_REVIEW` → `RESOLVED`) with analyst decision recording (`CONFIRMED_FRAUD` / `GENUINE`) and audit logging.
* **Model Benchmarking & Selection:** Comparative evaluation across **Logistic Regression**, **Random Forest**, **XGBoost**, and an **Ensemble Stacking** classifier with one-click champion promotion.
* **Dashboard & Security Analytics:** Real-time KPIs, transaction volume trends, risk distributions, and dynamic top risk factor visualizations.

---

## 🏗️ Architecture & Workflow

```text
Historical Dataset (financial_fraud_customer_transactions.csv)
        ↓
Dataset Validation & Leakage Audit
        ↓
Preprocessing & Feature Engineering (FullFraudPreprocessor)
        ↓
Model Training & Benchmarking (LR / RF / XGBoost / Ensemble)
        ↓
Validated Active Model
        ↓
New Transaction Submission
        ↓
Pydantic Input Validation
        ↓
Identical Fitted Preprocessing Pipeline
        ↓
ML Prediction (Fraud Probability)
        ↓
Independent Risk Scoring Engine (0–100 Score & Tier)
        ↓
SHAP Feature Attribution (Local Explanation)
        ↓
High-Risk Trigger → Fraud Alert → Investigation Case
        ↓
Analyst Review & Resolution Decision
        ↓
Dashboard Monitoring & Audit Trail
```

---

## 🛠️ Technology Stack

* **Backend:** Python 3.14, FastAPI, SQLAlchemy 2.0, Pydantic v2, Alembic, PyJWT, Passlib (Bcrypt)
* **Database:** SQLite (`fraud_detection.db`) with Write-Ahead Logging (`WAL` mode)
* **ML & Explainability:** Scikit-Learn, XGBoost, SHAP (TreeExplainer & LinearExplainer), Joblib, Pandas, NumPy
* **Frontend:** React 19, Vite, Tailwind CSS v4, Lucide React, Recharts
* **Testing:** Pytest, AnyIO, Starlette TestClient (163 automated unit/integration tests)

---

## 👥 Role-Based Access Control (RBAC)

* **`ADMIN`:** Full administrative control over dataset validation, model training, candidate model benchmarking, model promotion, threshold overrides, and audit inspection.
* **`FRAUD_INVESTIGATOR`:** Operational access to real-time transaction scoring, case investigation workflows, notes/decision recording, SHAP explanations, and dashboard monitoring.

---

## 📁 Repository Structure

```text
fraudinvestigation/
├── backend/
│   ├── alembic/          # Alembic database migrations
│   ├── app/
│   │   ├── api/          # FastAPI routers & RBAC dependencies
│   │   ├── core/         # Settings, database engine, security
│   │   ├── models/       # SQLAlchemy 2.0 ORM models
│   │   ├── schemas/      # Pydantic v2 validation contracts
│   │   ├── services/     # Business logic & prediction singleton
│   │   └── main.py       # FastAPI application entrypoint
│   ├── tests/            # 33 test modules (163 automated tests)
│   └── requirements.txt  # Backend Python dependencies
├── data/
│   └── raw/              # financial_fraud_customer_transactions.csv (4,582 rows)
├── ml/
│   ├── artifacts/        # Serialized models (.joblib), preprocessor & registry metadata
│   ├── evaluation/       # ModelSelector & threshold optimizer
│   ├── explainability/   # FraudShapExplainer & CounterfactualEngine
│   ├── features/         # FraudFeatureEngineer
│   ├── models/           # Model interfaces & candidate adapters
│   ├── preprocessing/    # FullFraudPreprocessor pipeline
│   ├── training/         # FraudModelTrainer engine
│   └── validation/       # DatasetValidator engine
├── frontend/             # React 19 + Tailwind CSS v4 Single Page Application
├── docs/                 # Architecture and evaluation documentation
└── fraud_detection.db    # Primary SQLite persistent database
```

---

## ⚡ Quick Start

### 1. Backend Service
```bash
# From repository root
cd backend
python -m uvicorn app.main:app --reload --port 8000
```
* Interactive API Documentation: `http://localhost:8000/docs`
* Health Endpoint: `http://localhost:8000/api/health`

### 2. Frontend Dashboard
```bash
# From repository root
cd frontend
npm install
npm run dev
```
* Dashboard URL: `http://localhost:5173`

### 3. Running Automated Tests
```bash
# From repository root (PowerShell / Bash)
$env:PYTHONPATH="."
.venv\Scripts\pytest backend/tests
```
