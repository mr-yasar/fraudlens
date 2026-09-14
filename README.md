# Explainable AI-Based Financial Fraud and Risk Detection System

An enterprise-grade, explainable AI system for detecting, analyzing, and investigating financial fraud and transaction risks.

## Project Structure

```
fraud-detection-system/
├── backend/            # FastAPI backend service, API endpoints & database models
├── frontend/           # React + Tailwind CSS client dashboard
├── ml/                 # Machine learning models, SHAP explainers & training pipelines
├── data/               # Raw and processed transaction datasets
├── docs/               # Architecture, API & system documentation
├── .env.example        # Environment variable template
├── .gitignore          # Git ignore rules
└── README.md           # Project documentation
```

## Technology Stack

- **Backend**: Python 3.14, FastAPI, SQLAlchemy 2.0, Pydantic v2, Alembic, Uvicorn
- **Frontend**: React 19, Vite, Tailwind CSS
- **Database**: PostgreSQL (with psycopg 3 driver)
- **ML / XAI**: Scikit-Learn, XGBoost, SHAP (configured for subsequent phases)

## Setup & Running

### Backend

1. Navigate to `backend/`
2. Create environment file: `copy .env.example .env`
3. Install dependencies: `pip install -r requirements.txt`
4. Start FastAPI server: `python -m uvicorn app.main:app --reload --port 8000`
5. Access API documentation at: `http://localhost:8000/docs`
6. Health Check: `http://localhost:8000/api/health`

### Frontend

1. Navigate to `frontend/`
2. Install dependencies: `npm install`
3. Start Vite dev server: `npm run dev`
4. Open `http://localhost:5173` in your browser

## Current Status

- **Phase 1 (Project Foundation)**: Completed
- **Phase 2 (Database Architecture)**: Completed
- **Phase 3+ (ML, SHAP, Auth, Dashboard)**: In preparation
