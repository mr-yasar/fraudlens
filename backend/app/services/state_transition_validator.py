"""Payment and Transaction Lifecycle State Transition Validator.

Enforces legal state machine transitions for payment intents and transaction flows,
preventing illegal jumps (e.g. BLOCKED -> SUCCEEDED, EXPIRED -> AUTHORIZED, REJECTED -> APPROVED).
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
    """State machine validator governing permissible transitions for PaymentIntents and Transactions."""

    # Authoritative map of permissible next states
    _VALID_TRANSITIONS: Dict[PaymentLifecycleStatus, Set[PaymentLifecycleStatus]] = {
        PaymentLifecycleStatus.CREATED: {
            PaymentLifecycleStatus.INITIATED,
            PaymentLifecycleStatus.ANALYZING,
            PaymentLifecycleStatus.RISK_EVALUATING,
            PaymentLifecycleStatus.CANCELLED,
            PaymentLifecycleStatus.EXPIRED,
        },
        PaymentLifecycleStatus.INITIATED: {
            PaymentLifecycleStatus.ANALYZING,
            PaymentLifecycleStatus.RISK_EVALUATING,
            PaymentLifecycleStatus.APPROVED,
            PaymentLifecycleStatus.PENDING_APPROVAL,
            PaymentLifecycleStatus.PENDING_VERIFICATION,
            PaymentLifecycleStatus.REVIEW_REQUIRED,
            PaymentLifecycleStatus.BLOCKED,
            PaymentLifecycleStatus.FAILED,
            PaymentLifecycleStatus.CANCELLED,
        },
        PaymentLifecycleStatus.ANALYZING: {
            PaymentLifecycleStatus.RISK_EVALUATING,
            PaymentLifecycleStatus.APPROVED,
            PaymentLifecycleStatus.PENDING_APPROVAL,
            PaymentLifecycleStatus.PENDING_VERIFICATION,
            PaymentLifecycleStatus.REVIEW_REQUIRED,
            PaymentLifecycleStatus.BLOCKED,
            PaymentLifecycleStatus.FAILED,
            PaymentLifecycleStatus.CANCELLED,
        },
        PaymentLifecycleStatus.RISK_EVALUATING: {
            PaymentLifecycleStatus.APPROVED,
            PaymentLifecycleStatus.PENDING_APPROVAL,
            PaymentLifecycleStatus.PENDING_VERIFICATION,
            PaymentLifecycleStatus.REVIEW_REQUIRED,
            PaymentLifecycleStatus.BLOCKED,
            PaymentLifecycleStatus.FAILED,
            PaymentLifecycleStatus.CANCELLED,
        },
        PaymentLifecycleStatus.APPROVED: {
            PaymentLifecycleStatus.SUBMITTED,
            PaymentLifecycleStatus.AUTHORIZED,
            PaymentLifecycleStatus.PROCESSING,
            PaymentLifecycleStatus.SUCCEEDED,
            PaymentLifecycleStatus.SUCCESS,
            PaymentLifecycleStatus.COMPLETED,
            PaymentLifecycleStatus.FAILED,
            PaymentLifecycleStatus.CANCELLED,
        },
        PaymentLifecycleStatus.PENDING_APPROVAL: {
            PaymentLifecycleStatus.APPROVED,   # User / Step-up verification approval
            PaymentLifecycleStatus.REJECTED,   # User rejection
            PaymentLifecycleStatus.BLOCKED,    # Automatic block
            PaymentLifecycleStatus.EXPIRED,    # Timeout
            PaymentLifecycleStatus.CANCELLED,
        },
        PaymentLifecycleStatus.PENDING_VERIFICATION: {
            PaymentLifecycleStatus.APPROVED,
            PaymentLifecycleStatus.REJECTED,
            PaymentLifecycleStatus.BLOCKED,
            PaymentLifecycleStatus.EXPIRED,
            PaymentLifecycleStatus.CANCELLED,
        },
        PaymentLifecycleStatus.REVIEW_REQUIRED: {
            PaymentLifecycleStatus.APPROVED,   # Investigator manual approval
            PaymentLifecycleStatus.REJECTED,
            PaymentLifecycleStatus.BLOCKED,    # Investigator manual block
            PaymentLifecycleStatus.CANCELLED,
            PaymentLifecycleStatus.EXPIRED,
        },
        PaymentLifecycleStatus.SUBMITTED: {
            PaymentLifecycleStatus.PROCESSING,
            PaymentLifecycleStatus.AUTHORIZED,
            PaymentLifecycleStatus.SUCCEEDED,
            PaymentLifecycleStatus.SUCCESS,
            PaymentLifecycleStatus.COMPLETED,
            PaymentLifecycleStatus.FAILED,
            PaymentLifecycleStatus.CANCELLED,
        },
        PaymentLifecycleStatus.PROCESSING: {
            PaymentLifecycleStatus.AUTHORIZED,
            PaymentLifecycleStatus.SUCCEEDED,
            PaymentLifecycleStatus.SUCCESS,
            PaymentLifecycleStatus.COMPLETED,
            PaymentLifecycleStatus.FAILED,
            PaymentLifecycleStatus.CANCELLED,
        },
        PaymentLifecycleStatus.AUTHORIZED: {
            PaymentLifecycleStatus.SUCCEEDED,
            PaymentLifecycleStatus.SUCCESS,
            PaymentLifecycleStatus.COMPLETED,
            PaymentLifecycleStatus.FAILED,
            PaymentLifecycleStatus.CANCELLED,
        },
        # Terminal states (No forward transitions allowed except audit cancellation)
        PaymentLifecycleStatus.REJECTED: {PaymentLifecycleStatus.BLOCKED},
        PaymentLifecycleStatus.BLOCKED: set(),
        PaymentLifecycleStatus.SUCCEEDED: {PaymentLifecycleStatus.CANCELLED},  # Refund/chargeback
        PaymentLifecycleStatus.SUCCESS: {PaymentLifecycleStatus.CANCELLED},
        PaymentLifecycleStatus.COMPLETED: {PaymentLifecycleStatus.CANCELLED},
        PaymentLifecycleStatus.FAILED: set(),
        PaymentLifecycleStatus.CANCELLED: set(),
        PaymentLifecycleStatus.EXPIRED: {PaymentLifecycleStatus.BLOCKED},
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

        # Normalize equivalent statuses
        equiv_map = {
            PaymentLifecycleStatus.SUCCESS: PaymentLifecycleStatus.SUCCEEDED,
            PaymentLifecycleStatus.COMPLETED: PaymentLifecycleStatus.SUCCEEDED,
            PaymentLifecycleStatus.PENDING_APPROVAL: PaymentLifecycleStatus.REVIEW_REQUIRED,
            PaymentLifecycleStatus.PENDING_VERIFICATION: PaymentLifecycleStatus.REVIEW_REQUIRED,
        }

        norm_current = equiv_map.get(current, current)
        norm_target = equiv_map.get(target, target)

        if norm_current == norm_target:
            return True, "Equivalent state transition."

        allowed = cls._VALID_TRANSITIONS.get(current, set()) | cls._VALID_TRANSITIONS.get(norm_current, set())
        if target not in allowed and norm_target not in allowed:
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
