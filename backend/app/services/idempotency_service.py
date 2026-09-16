"""Idempotency Management Service.

Guarantees exact-once semantics for payment initiation requests across
retries, double-clicks, and network disruptions.
"""

import hashlib
import json
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, Optional, Tuple
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from backend.app.models.idempotency import IdempotencyRecord


class IdempotencyService:
    """Provides request fingerprinting, key locking, and cached response retrieval."""

    DEFAULT_EXPIRY_HOURS = 24

    @staticmethod
    def compute_fingerprint(payload: Dict[str, Any]) -> str:
        """Compute deterministic SHA-256 hash of canonical JSON request payload."""
        canonical_json = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
        return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()

    @classmethod
    def check_idempotency(
        cls,
        db: Session,
        idempotency_key: str,
        request_payload: Dict[str, Any],
    ) -> Tuple[Optional[IdempotencyRecord], bool]:
        """
        Check if an idempotency key exists.

        Returns:
            (record, is_cached_replay):
                - If record exists and payload fingerprint matches: (record, True)
                - If record does not exist: (None, False)
        Raises:
            HTTPException 409 if key exists but payload fingerprint does not match.
        """
        if not idempotency_key:
            return None, False

        fingerprint = cls.compute_fingerprint(request_payload)
        record = (
            db.query(IdempotencyRecord)
            .filter(IdempotencyRecord.idempotency_key == idempotency_key)
            .first()
        )

        if record:
            if record.request_fingerprint != fingerprint:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=(
                        f"Idempotency conflict: key '{idempotency_key}' was previously used "
                        "with a different request payload fingerprint."
                    ),
                )
            return record, True

        return None, False

    @classmethod
    def store_idempotency(
        cls,
        db: Session,
        idempotency_key: str,
        request_payload: Dict[str, Any],
        resource_id: str,
        status_code: int,
        response_data: Dict[str, Any],
        expiry_hours: int = DEFAULT_EXPIRY_HOURS,
    ) -> IdempotencyRecord:
        """Persist request fingerprint and JSON response for replay protection."""
        if not idempotency_key:
            return None

        fingerprint = cls.compute_fingerprint(request_payload)
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(hours=expiry_hours)

        record = IdempotencyRecord(
            idempotency_key=idempotency_key,
            request_fingerprint=fingerprint,
            resource_id=resource_id,
            status_code=status_code,
            response_json=json.dumps(response_data, default=str),
            created_at=now,
            expires_at=expires_at,
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return record
