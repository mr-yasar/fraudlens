# System Architecture: Explainable AI Fraud & Risk Detection

## System Overview

```
[ Financial Transactions / Client Apps ]
                   │
                   ▼
       [ FastAPI Backend Service ]
       ├── CORS & Security Middleware
       ├── API Routes (/api/health, /api/v1/...)
       ├── Session Management (SQLAlchemy 2.0)
       └── Database Migrations (Alembic)
                   │
       ┌───────────┴───────────┐
       ▼                       ▼
[ PostgreSQL Database ]   [ React Frontend (Tailwind CSS) ]
- users                   - Health & System Status
- customers               - Real-time Monitoring (Future)
- transactions            - Explainability Visualizations (Future)
- investigations          - Case Management (Future)
- shap_explanations
- model_versions
- audit_logs
```

## Relational Schema Design

1. **`users`**: Investigators, analysts, and administrators.
2. **`customers`**: Historical customer profiles & account age.
3. **`transactions`**: High-volume financial transaction records with risk scores, probabilities, and classifications.
4. **`investigations`**: Case management tracking investigator decisions, status, and audit notes.
5. **`shap_explanations`**: Feature-level SHAP values explaining why individual transactions were flagged.
6. **`model_versions`**: Audit and tracking for ML models (accuracy, F1, ROC-AUC, PR-AUC, binary paths).
7. **`audit_logs`**: System activity and compliance trail.
