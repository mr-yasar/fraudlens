# 🛡️ FraudLens AI (v2.1) — Explainable Financial Fraud Detection & AI Intelligence Platform

[![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13%20%7C%203.14-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-19.2+-61DAFB.svg)](https://react.dev)
[![Vite](https://img.shields.io/badge/Vite-8.3+-646CFF.svg)](https://vite.dev)
[![TailwindCSS](https://img.shields.io/badge/Tailwind-v4.3+-38B2AC.svg)](https://tailwindcss.com)
[![XGBoost](https://img.shields.io/badge/ML-XGBoost%20%2B%20TreeSHAP-orange.svg)](https://xgboost.readthedocs.io)

**FraudLens AI** is an enterprise-grade Explainable AI (XAI) financial fraud and risk detection platform. It evaluates high-frequency digital payments (UPI, IMPS, Cards) in **under 4 milliseconds**, delivers sub-second TreeSHAP feature attributions, and features an **autonomous Multi-LLM AI Investigation Command Center** (Google Gemini 3.6/3.7, xAI Grok-2, Mistral AI, and an offline Domain Engine).

---

## 🚀 Key Features in Version 2.1

* **⚡ Ultra-Low Latency Inference (<4ms):** Pre-authorization payment gateway scoring transactions against our active ML model suite.
* **🌲 4-Model ML Suite with XGBoost Champion:**
  * **XGBoost (Champion):** ROC-AUC `0.998`, Precision `99.4%`
  * **Random Forest:** Ensemble bagging for variance stability
  * **Logistic Regression:** Linear probabilistic baseline
  * **Stacking Classifier:** Meta-learner combining probability outputs
* **🔍 Explainable AI (TreeSHAP):** Real-time waterfall feature attributions explaining the exact mathematical influence of amount abnormalities, velocity bursts, and geolocation shifts.
* **🤖 Light Frosted Glass AI Workspace (Exact 1:1 Video Match):**
  * 3-Panel Forensic Command Center (`Case Workspace` | `Conversation Stream` | `Live Evidence Dashboard`)
  * Iridescent Holographic **AI Orb** with scanning telemetry
  * Latency radar, 5-node relationship graph, and transaction cluster map
  * FinCEN Suspicious Activity Report (SAR) auto-drafting
* **🧠 Autonomous Multi-LLM Intelligence Engine:**
  * **AUTO Mode:** Automatic failover cascade (Gemini 3.6 Flash primary ➔ Gemini 3.7 Deep Reasoning ➔ xAI Grok / Mistral ➔ Safe Domain Engine)
  * **Direct Modes:** One-click toggle between `[GEMINI]`, `[GROK]`, `[MISTRAL]`, and `[AUTO]`
  * **Built-in Offline Resilience:** Answers every fraud analysis query with 100% domain accuracy even when external API keys or cloud connections are absent.
* **🔒 Strict Multi-Tenant Persona Privacy:** Zero-leak customer isolation complying with PCI-DSS & GDPR. Customers only access their own records, while Admins/Investigators retain full SOC telemetry.
* **🎬 6-Module Google Veo Master Video Scripts:** Complete scene-by-scene Tanglish video walkthroughs available in [Interactive HTML](FRAUDLENS_AI_VEO_VIDEO_SCRIPTS.html), [PDF](FRAUDLENS_AI_VEO_VIDEO_SCRIPTS.pdf), and [Markdown](FRAUDLENS_AI_VEO_VIDEO_SCRIPTS.md).

---

## ⚡ Quick Start (Run Locally in 2 Minutes)

### Prerequisites
* **Python**: 3.10 or higher
* **Node.js**: v18 or higher (with npm)
* **Git** (or downloaded ZIP)

---

### Step 1: Backend Setup (Terminal 1)

Open a terminal in the project root folder (`fraudlens`):

```powershell
# 1. Create and activate a Python virtual environment
python -m venv .venv

# Windows (PowerShell):
.\.venv\Scripts\Activate.ps1
# Mac / Linux:
# source .venv/bin/activate

# 2. Install backend dependencies
pip install -r requirements.txt

# 3. Seed demo database (29 Master Merchants & Canonical Transactions)
python scripts/seed_canonical_database.py

# 4. Start the FastAPI backend server
python -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

* **Backend Health Check:** `http://127.0.0.1:8000/api/v1/health`
* **Interactive Swagger API Docs:** `http://127.0.0.1:8000/docs`

---

### Step 2: Frontend Setup (Terminal 2)

Open a **second terminal** in the project root folder:

```powershell
# 1. Navigate to the frontend directory
cd frontend

# 2. Install node dependencies
npm install

# 3. Start the Vite React development server
npm run dev
```

* **Frontend Application:** Open **`http://localhost:5173`** in your browser!

---

## 🔑 Demo Login Accounts

| Role | Email | Password | Access Level |
|---|---|---|---|
| **Admin** | `admin@fraudlens.ai` | `Admin@1234` | Full SOC command, Model Lab, Retrain Triggers, Global Audit |
| **Fraud Investigator** | `investigator@fraudlens.ai` | `Investigator@1234` | Case Management, Forensic Command Center, SAR Filing |
| **Monisha** | `monisha@fraudlens.ai` | `Customer@1234` | Safe user profile (3% risk, Instant Green Pass) |
| **Mohana** | `mohana@fraudlens.ai` | `Customer@1234` | Edge-case user (12% risk, Step-up OTP Challenge) |
| **Sowmiya** | `sowmiya@fraudlens.ai` | `Customer@1234` | Velocity attack victim (26% risk, Instant Account Freeze) |

*(Guest access is also available without logging in — visitors can freely ask the AI Assistant about platform architecture, models, and fraud detection mechanisms).*

---

## 🧪 Automated Test Suite

FraudLens AI includes a comprehensive regression and orchestrator test suite:

```powershell
# Run the autonomous AI orchestrator & security tests
$env:PYTHONPATH="."
python -m pytest tests/test_autonomous_orchestrator.py -v

# Run the full regression test suite
python -m pytest -v
```

---

## 📁 Repository Structure

```text
fraudlens/
├── backend/
│   ├── app/
│   │   ├── api/v1/endpoints/  # AI assistant, auth, transactions, models, analytics
│   │   ├── core/              # Config, SQLite engine, security, JWT
│   │   ├── models/            # SQLAlchemy 2.0 ORM models (User, Customer, Txn, etc.)
│   │   └── services/          # Multi-LLM adapters, ML predictor, XAI TreeSHAP
│   └── main.py                # FastAPI ASGI application entrypoint
├── frontend/
│   ├── src/
│   │   ├── components/        # Dashboard, Analyzer, Payment Gateway, Live Monitor
│   │   │   └── ai/            # Light Frosted Glass AI Workspace & AI Orb
│   │   ├── context/           # AuthContext & role state
│   │   └── services/          # Axios/Fetch API client bindings
│   └── vite.config.js         # Vite proxy configuration (/api -> :8000)
├── ml/
│   └── artifacts/             # Serialized joblib pipelines & active model metadata
├── scripts/
│   └── seed_canonical_database.py # Zero-config database initialization script
├── FRAUDLENS_AI_VEO_VIDEO_SCRIPTS.md   # Master Google Veo video scripts
├── FRAUDLENS_AI_VEO_VIDEO_SCRIPTS.html # Interactive 1-click copy & print viewer
├── FRAUDLENS_AI_VEO_VIDEO_SCRIPTS.pdf  # Compiled 912 KB PDF video guide
├── requirements.txt           # Python dependencies
└── README.md                  # Project documentation
```

---

## 📄 License
This project is licensed under the MIT License — see the LICENSE file for details.
