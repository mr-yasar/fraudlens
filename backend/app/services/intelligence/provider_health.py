"""Provider Health & Intelligent Failover State Tracker.

Monitors real-time API availability, rate limits, quota exhaustion, and billing issues.
Ensures AUTO mode makes zero unnecessary calls while intelligently routing around
temporary provider outages.
"""

import time
import logging
from typing import Dict, Any, List, Optional
from enum import Enum

logger = logging.getLogger("fraudlens.intelligence.health")


class ProviderStatus(str, Enum):
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    RATE_LIMITED = "RATE_LIMITED"
    CREDIT_EXHAUSTED = "CREDIT_EXHAUSTED"
    UNCONFIGURED = "UNCONFIGURED"


class ProviderHealthTracker:
    """In-memory health and cooldown registry for all AI providers."""

    # Provider status dictionaries
    _cooldowns: Dict[str, float] = {}
    _statuses: Dict[str, ProviderStatus] = {
        "gemini": ProviderStatus.HEALTHY,
        "grok": ProviderStatus.CREDIT_EXHAUSTED,  # xAI key has 0 prepaid credits
        "mistral": ProviderStatus.HEALTHY,
    }
    _last_errors: Dict[str, str] = {}
    _failure_counts: Dict[str, int] = {}
    _success_counts: Dict[str, int] = {}
    _last_success: Dict[str, float] = {}

    @classmethod
    def record_success(cls, provider: str) -> None:
        """Mark provider as fully healthy and reset cooldowns."""
        prov = provider.lower().strip()
        cls._statuses[prov] = ProviderStatus.HEALTHY
        cls._cooldowns.pop(prov, None)
        cls._last_errors.pop(prov, None)
        cls._failure_counts[prov] = 0
        cls._success_counts[prov] = cls._success_counts.get(prov, 0) + 1
        cls._last_success[prov] = time.time()
        logger.debug("Provider %s marked HEALTHY after successful call", prov)

    @classmethod
    def record_failure(cls, provider: str, error: Exception) -> None:
        """Analyze error to set appropriate cooldown and health status."""
        prov = provider.lower().strip()
        err_str = str(error)
        err_lower = err_str.lower()
        now = time.time()

        cls._failure_counts[prov] = cls._failure_counts.get(prov, 0) + 1
        cls._last_errors[prov] = err_str[:250]

        if "429" in err_lower or "rate limit" in err_lower or "quota" in err_lower or "resource_exhausted" in err_lower:
            cls._statuses[prov] = ProviderStatus.RATE_LIMITED
            # 60s backoff for standard rate limit
            cls._cooldowns[prov] = now + 60.0
            logger.warning("Provider %s rate-limited/quota exceeded (cooldown 60s): %s", prov, err_str[:120])

        elif "credit" in err_lower or "billing" in err_lower or "402" in err_lower or "payment" in err_lower or "team_blocked" in err_lower:
            cls._statuses[prov] = ProviderStatus.CREDIT_EXHAUSTED
            # 300s cooldown for billing/credit issues
            cls._cooldowns[prov] = now + 300.0
            logger.warning("Provider %s credit/billing exhausted (cooldown 300s): %s", prov, err_str[:120])

        elif "401" in err_lower or "unauthorized" in err_lower or "invalid api key" in err_lower:
            cls._statuses[prov] = ProviderStatus.UNCONFIGURED
            cls._cooldowns[prov] = now + 600.0
            logger.error("Provider %s authentication invalid: %s", prov, err_str[:120])

        else:
            cls._statuses[prov] = ProviderStatus.DEGRADED
            # 20s cooldown for transient connection/internal errors
            cls._cooldowns[prov] = now + 20.0
            logger.warning("Provider %s degraded (cooldown 20s): %s", prov, err_str[:120])

    @classmethod
    def is_available(cls, provider: str) -> bool:
        """Check if provider is configured and not currently in cooldown."""
        prov = provider.lower().strip()
        now = time.time()

        # Check cooldown timer
        if now < cls._cooldowns.get(prov, 0):
            return False

        # If cooldown expired, restore from temporary rate limit/degraded
        current_status = cls._statuses.get(prov, ProviderStatus.HEALTHY)
        if current_status in (ProviderStatus.RATE_LIMITED, ProviderStatus.DEGRADED):
            cls._statuses[prov] = ProviderStatus.HEALTHY

        return current_status in (ProviderStatus.HEALTHY, ProviderStatus.DEGRADED)

    @classmethod
    def get_best_fallback(cls, preferred_order: Optional[List[str]] = None) -> Optional[str]:
        """Return the highest priority fallback provider that is currently available."""
        order = preferred_order or ["mistral", "grok"]
        for candidate in order:
            if cls.is_available(candidate):
                return candidate
        return None

    @classmethod
    def get_health_summary(cls) -> Dict[str, Any]:
        """Return current health states for telemetry and diagnostics."""
        now = time.time()
        return {
            "gemini": {
                "status": cls._statuses.get("gemini", ProviderStatus.HEALTHY).value,
                "available": cls.is_available("gemini"),
                "cooldown_remaining": max(0, int(cls._cooldowns.get("gemini", 0) - now)),
                "success_count": cls._success_counts.get("gemini", 0),
            },
            "grok": {
                "status": cls._statuses.get("grok", ProviderStatus.CREDIT_EXHAUSTED).value,
                "available": cls.is_available("grok"),
                "cooldown_remaining": max(0, int(cls._cooldowns.get("grok", 0) - now)),
                "note": "xAI team has 0 credits on console.x.ai",
            },
            "mistral": {
                "status": cls._statuses.get("mistral", ProviderStatus.HEALTHY).value,
                "available": cls.is_available("mistral"),
                "cooldown_remaining": max(0, int(cls._cooldowns.get("mistral", 0) - now)),
                "model": "open-mistral-7b",
                "success_count": cls._success_counts.get("mistral", 0),
            },
        }
