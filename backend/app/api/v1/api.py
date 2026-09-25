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
from backend.app.api.v1.endpoints.payment import router as payment_router
from backend.app.api.v1.endpoints.approvals import router as approvals_router
from backend.app.api.v1.endpoints.events import router as events_router


from backend.app.api.v1.endpoints.alerts import router as alerts_router
from backend.app.api.v1.endpoints.network import router as network_router
from backend.app.api.v1.endpoints.intelligence import router as intelligence_router
from backend.app.api.v1.endpoints.adaptive_intelligence import router as adaptive_intelligence_router
from backend.app.api.v1.endpoints.merchants import router as merchants_router
from backend.app.api.v1.endpoints.governance import router as governance_router

api_router = APIRouter()

# Register endpoint routers
api_router.include_router(health_router, tags=["Health"])
api_router.include_router(auth_router, prefix="/auth", tags=["Authentication & Users"])
api_router.include_router(protected_router, tags=["Protected RBAC Operations"])
api_router.include_router(merchants_router, prefix="/merchants", tags=["Merchant Intelligence"])
api_router.include_router(payment_router, prefix="/payment", tags=["Transaction Risk Simulation"])
api_router.include_router(approvals_router, prefix="/approvals", tags=["Step-Up Verification Approvals"])
api_router.include_router(network_router, prefix="/network", tags=["Fraud Network & Relationship Graph"])

api_router.include_router(intelligence_router, prefix="/intelligence", tags=["Continuous Intelligence Fabric"])
api_router.include_router(adaptive_intelligence_router, prefix="/adaptive", tags=["Adaptive Threat Intelligence & Federated Learning"])
api_router.include_router(governance_router, prefix="/governance", tags=["System Governance, Drift & Model Promotion"])
api_router.include_router(events_router, prefix="/events", tags=["Live Event Streaming"])
api_router.include_router(events_router, prefix="/ws", tags=["WebSocket Alert Pipeline"])
api_router.include_router(alerts_router, prefix="/alerts", tags=["In-App Security Alerts"])
api_router.include_router(datasets_router, prefix="/datasets", tags=["Dataset Management & Validation"])
api_router.include_router(prediction_router, tags=["Fraud Prediction Engine"])
api_router.include_router(prediction_router, prefix="/predictions", tags=["Fraud Prediction Engine"])
api_router.include_router(customers_router, prefix="/customers", tags=["Customer Management"])
api_router.include_router(transactions_router, prefix="/transactions", tags=["Transaction Management & Real-Time Evaluation"])
api_router.include_router(investigations_router, prefix="/investigations", tags=["Investigation & Case Management"])
api_router.include_router(admin_ml_router, prefix="/admin", tags=["Admin ML & Dataset Management"])
api_router.include_router(dashboard_router, prefix="/dashboard", tags=["Dashboard & Analytics"])
api_router.include_router(audit_logs_router, prefix="/audit-logs", tags=["Audit Logging"])


