"""Payment Provider Factory.

Instantiates and supplies configured payment provider adapters based on environment/settings.
"""

from typing import Dict, Optional
from backend.app.providers.base import PaymentProviderAdapter
from backend.app.providers.mock_provider import MockPaymentProvider
from backend.app.providers.sandbox_provider import SandboxPaymentProvider


class PaymentProviderFactory:
    """Factory to retrieve singleton or named payment provider adapters."""

    _instances: Dict[str, PaymentProviderAdapter] = {}

    @classmethod
    def get_provider(cls, name: str = "sandbox", **kwargs) -> PaymentProviderAdapter:
        """Get or initialize the specified provider adapter."""
        name_clean = name.lower().strip()
        if name_clean in cls._instances and not kwargs:
            return cls._instances[name_clean]

        if name_clean in ("mock", "mock_provider"):
            provider = MockPaymentProvider(
                provider_name=name_clean,
                webhook_secret=kwargs.get("webhook_secret", "mock_secret_key_fraudlens_test_12345"),
                simulate_fault=kwargs.get("simulate_fault"),
            )
        elif name_clean in ("sandbox", "sandbox_gateway", "default"):
            provider = SandboxPaymentProvider(
                provider_name="sandbox_gateway",
                webhook_secret=kwargs.get("webhook_secret", "whsec_sandbox_fraudlens_demo_secret_998877"),
                simulated_latency_ms=kwargs.get("simulated_latency_ms", 15.0),
            )
        else:
            # Fallback to sandbox provider for demo safety
            provider = SandboxPaymentProvider(provider_name=name_clean)

        if not kwargs:
            cls._instances[name_clean] = provider
        return provider

    @classmethod
    def reset(cls):
        """Clear cached provider instances."""
        cls._instances.clear()
