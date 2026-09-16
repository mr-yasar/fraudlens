"""Payment Lifecycle State Transition Validator (Phase 28).

Enforces legal state machine transitions for payment intents and prevents
illegal jumps (e.g. BLOCKED -> SUCCEEDED, EXPIRED -> AUTHORIZED).
"""

from typing import Dict, Set, Tuple
from backend.app.models.payment_intent import PaymentLifecycleStatus


class StateTransitionError(Exception):
    """Raised when an illegal lifecycle state transition is attempted."""
    def __init__(self, current_state: str, target_state: str, reason: str = ""):
        message = f"Illegal payment lifecycle transition: '{current_state}' -> '{target_state}'. {reason}".strip()
        super().__init__(message)
        self.current_state = current_state
        self.target_state = target_state


class StateTransitionValidator:
    """State machine validator governing permissible transitions for PaymentIntents."""

    # Authoritative map of permissible next states
    _VALID_TRANSITIONS: Dict[PaymentLifecycleStatus, Set[PaymentLifecycleStatus]] = {
        PaymentLifecycleStatus.CREATED: {
            PaymentLifecycleStatus.RISK_EVALUATING,
            PaymentLifecycleStatus.CANCELLED,
            PaymentLifecycleStatus.EXPIRED,
        },
        PaymentLifecycleStatus.RISK_EVALUATING: {
            PaymentLifecycleStatus.APPROVED,
            PaymentLifecycleStatus.REVIEW_REQUIRED,
            PaymentLifecycleStatus.BLOCKED,
            PaymentLifecycleStatus.FAILED,
        },
        PaymentLifecycleStatus.APPROVED: {
            PaymentLifecycleStatus.SUBMITTED,
            PaymentLifecycleStatus.AUTHORIZED,
            PaymentLifecycleStatus.SUCCEEDED,
            PaymentLifecycleStatus.FAILED,
            PaymentLifecycleStatus.CANCELLED,
        },
        PaymentLifecycleStatus.REVIEW_REQUIRED: {
            PaymentLifecycleStatus.APPROVED,  # Investigator manual approval
            PaymentLifecycleStatus.BLOCKED,   # Investigator manual block
            PaymentLifecycleStatus.CANCELLED,
            PaymentLifecycleStatus.EXPIRED,
        },
        PaymentLifecycleStatus.SUBMITTED: {
            PaymentLifecycleStatus.PROCESSING,
            PaymentLifecycleStatus.AUTHORIZED,
            PaymentLifecycleStatus.SUCCEEDED,
            PaymentLifecycleStatus.FAILED,
            PaymentLifecycleStatus.CANCELLED,
        },
        PaymentLifecycleStatus.PROCESSING: {
            PaymentLifecycleStatus.AUTHORIZED,
            PaymentLifecycleStatus.SUCCEEDED,
            PaymentLifecycleStatus.FAILED,
            PaymentLifecycleStatus.CANCELLED,
        },
        PaymentLifecycleStatus.AUTHORIZED: {
            PaymentLifecycleStatus.SUCCEEDED,
            PaymentLifecycleStatus.FAILED,
            PaymentLifecycleStatus.CANCELLED,
        },
        # Terminal states (No forward transitions allowed except audit cancellation)
        PaymentLifecycleStatus.BLOCKED: set(),
        PaymentLifecycleStatus.SUCCEEDED: {PaymentLifecycleStatus.CANCELLED},  # Refund/chargeback
        PaymentLifecycleStatus.FAILED: set(),
        PaymentLifecycleStatus.CANCELLED: set(),
        PaymentLifecycleStatus.EXPIRED: set(),
    }

    @classmethod
    def validate_transition(
        cls,
        current_status_str: str,
        target_status_str: str,
    ) -> Tuple[bool, str]:
        """
        Validate whether transitioning from current_status to target_status is permissible.
        Returns (is_valid: bool, error_message: str).
        """
        try:
            current = PaymentLifecycleStatus(current_status_str.upper())
            target = PaymentLifecycleStatus(target_status_str.upper())
        except ValueError as e:
            return False, f"Unknown lifecycle state: {e}"

        if current == target:
            return True, "No state change required (idempotent transition)."

        allowed = cls._VALID_TRANSITIONS.get(current, set())
        if target not in allowed:
            return False, (
                f"Transition from '{current.value}' to '{target.value}' is prohibited. "
                f"Allowed target states: {[s.value for s in allowed]}."
            )

        return True, "Transition valid."

    @classmethod
    def enforce_transition(cls, current_status_str: str, target_status_str: str) -> None:
        """Enforce transition, raising StateTransitionError if prohibited."""
        valid, msg = cls.validate_transition(current_status_str, target_status_str)
        if not valid:
            raise StateTransitionError(current_status_str, target_status_str, msg)
