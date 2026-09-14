"""Main API v1 router combining all sub-routers."""

from fastapi import APIRouter
from backend.app.api.v1.endpoints.health import router as health_router
from backend.app.api.v1.endpoints.auth import router as auth_router
from backend.app.api.v1.endpoints.protected_examples import router as protected_router
from backend.app.api.v1.endpoints.datasets import router as datasets_router
from backend.app.api.v1.endpoints.prediction import router as prediction_router

from backend.app.api.v1.endpoints.customers import router as customers_router
from backend.app.api.v1.endpoints.transactions import router as transactions_router
from backend.app.api.v1.endpoints.investigations import router as investigations_router
from backend.app.api.v1.endpoints.admin_ml import router as admin_ml_router
from backend.app.api.v1.endpoints.dashboard import router as dashboard_router
from backend.app.api.v1.endpoints.audit_logs import router as audit_logs_router

api_router = APIRouter()

# Register endpoint routers
api_router.include_router(health_router, tags=["Health"])
api_router.include_router(auth_router, prefix="/auth", tags=["Authentication & Users"])
api_router.include_router(protected_router, tags=["Protected RBAC Operations"])
api_router.include_router(datasets_router, prefix="/datasets", tags=["Dataset Management & Validation"])
api_router.include_router(prediction_router, tags=["Fraud Prediction Engine"])
api_router.include_router(customers_router, prefix="/customers", tags=["Customer Management"])
api_router.include_router(transactions_router, prefix="/transactions", tags=["Transaction Management & Real-Time Evaluation"])
api_router.include_router(investigations_router, prefix="/investigations", tags=["Investigation & Case Management"])
api_router.include_router(admin_ml_router, prefix="/admin", tags=["Admin ML & Dataset Management"])
api_router.include_router(dashboard_router, prefix="/dashboard", tags=["Dashboard & Analytics"])
api_router.include_router(audit_logs_router, prefix="/audit-logs", tags=["Audit Logging"])

