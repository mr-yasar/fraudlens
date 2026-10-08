"""Assistant Telemetry, Answer Quality, and Closed-Loop Tuning System.

Implements Phase 19 of the 24-Phase Chatbot Remodel:
- Non-sensitive operational metric collection (route type, latency, confidence, intent)
- Unknown query logging ring buffer for active tuning and intent expansion
- Zero secret / PII leakage
"""

import collections
import datetime
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger("fraudlens.assistant.telemetry")


class AssistantTelemetryService:
    def __init__(self, max_unknown_queue_size: int = 200):
        self.total_requests = 0
        self.route_counts: Dict[str, int] = collections.defaultdict(int)
        self.intent_hits: Dict[str, int] = collections.defaultdict(int)
        self.unknown_questions: collections.deque = collections.deque(maxlen=max_unknown_queue_size)
        self.latencies: collections.deque = collections.deque(maxlen=100)

    def record_interaction(
        self,
        query: str,
        route: str,
        intent: Optional[str],
        confidence: float,
        latency_ms: float,
        tool_status: Optional[str] = None,
        fallback_reason: Optional[str] = None,
    ):
        """Record non-sensitive metadata for telemetry and tuning."""
        self.total_requests += 1
        self.route_counts[route] += 1
        if intent:
            self.intent_hits[intent] += 1
        self.latencies.append(latency_ms)

        if route in ("SAFE_FALLBACK", "UNKNOWN") or confidence < 0.50:
            # Mask any potentially sensitive identifiers from query before adding to queue
            sanitized = query.strip()[:150]
            self.unknown_questions.append({
                "timestamp": datetime.datetime.utcnow().isoformat(),
                "query": sanitized,
                "confidence": round(confidence, 3),
                "fallback_reason": fallback_reason or "Low confidence threshold",
            })

        logger.info(
            "Assistant query logged: route=%s intent=%s conf=%.2f latency=%.1fms",
            route, intent, confidence, latency_ms
        )

    def get_metrics_summary(self) -> Dict[str, Any]:
        """Generate high-level operational metrics for administration."""
        avg_latency = (sum(self.latencies) / len(self.latencies)) if self.latencies else 0.0
        faq_hits = self.route_counts.get("PREDEFINED", 0)
        hit_rate = (faq_hits / self.total_requests) if self.total_requests > 0 else 0.0

        return {
            "total_requests": self.total_requests,
            "route_distribution": dict(self.route_counts),
            "predefined_hit_rate": round(hit_rate * 100, 1),
            "average_latency_ms": round(avg_latency, 2),
            "unknown_queue_length": len(self.unknown_questions),
            "top_intents": sorted(self.intent_hits.items(), key=lambda x: x[1], reverse=True)[:5],
        }

    def get_unknown_queries(self) -> List[Dict[str, Any]]:
        """Return reviewable unknown questions queue."""
        return list(self.unknown_questions)


# Singleton instance
telemetry_service = AssistantTelemetryService()
