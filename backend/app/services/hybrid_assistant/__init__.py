"""FraudLens Hybrid Fraud Investigation and Knowledge Assistant Package.

Exposes the core policy router, normalizer, and telemetry services.
"""

from backend.app.services.hybrid_assistant.router import route_and_execute_query
from backend.app.services.hybrid_assistant.taxonomy import (
    AssistantResponseEnvelope,
    RouteType,
    ResponseCardType,
    ConfidenceBand,
)
from backend.app.services.hybrid_assistant.telemetry import telemetry_service

__all__ = [
    "route_and_execute_query",
    "AssistantResponseEnvelope",
    "RouteType",
    "ResponseCardType",
    "ConfidenceBand",
    "telemetry_service",
]
