"""Rule Adaptation & Performance Monitoring Service (Phase 2).

Tracks production rule effectiveness, false-positive ratios, hit counts,
and manages candidate rule lifecycle requiring human admin approval.
"""

from datetime import datetime, timezone
import json
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from backend.app.models.investigation import Investigation
from backend.app.models.transaction import Transaction
from backend.app.models.audit_log import AuditLog
from backend.app.schemas.adaptive_intelligence import (
    RuleEffectivenessItem,
    CandidateRuleCreate,
    CandidateRuleItem,
)
from backend.app.services.rule_engine import RuleEngine


class RuleAdaptationService:
    """Monitors active rule effectiveness and manages candidate rule approvals."""

    # In-memory store for proposed candidate rules (persisted via AuditLog)
    _candidate_rules: List[Dict[str, Any]] = [
        {
            "rule_id": "CAND-RULE-EMULATOR-SPIKE",
            "rule_name": "Emulator Multi-Attempt Hard Flag",
            "condition_description": "Device is emulator AND Velocity_1h >= 2 AND Amount > $300",
            "category": "DEVICE_SECURITY",
            "proposed_action": "FLAG_REVIEW",
            "rationale": "High concentration of recent fraud attempts originating from emulated device environments.",
            "status": "CANDIDATE",
            "created_at": "2026-09-16T12:00:00Z",
            "created_by": "Adaptive Intelligence Engine",
        },
        {
            "rule_id": "CAND-RULE-BENEFICIARY-BURST",
            "rule_name": "Multi-Account Beneficiary Funneling",
            "condition_description": "Shared beneficiary across 3+ unique customer IDs within 24h",
            "category": "NETWORK_SYNDICATE",
            "proposed_action": "BLOCK",
            "rationale": "Mitigates mule account rapid cashout funneling across disparate user credentials.",
            "status": "APPROVED",
            "created_at": "2026-09-16T12:30:00Z",
            "created_by": "Security Admin",
        },
    ]

    @classmethod
    def get_rule_effectiveness_metrics(cls, db: Session) -> List[RuleEffectivenessItem]:
        """Compute hit rate, confirmed fraud, false positives, and effectiveness score for rules."""
        resolved_cases = (
            db.query(Investigation)
            .filter(Investigation.status == "RESOLVED", Investigation.decision.isnot(None))
            .all()
        )

        # Map transaction_id -> actual fraud outcome (1 = Fraud, 0 = Genuine)
        ground_truth: Dict[str, int] = {
            c.transaction_id: (1 if c.decision == "CONFIRMED_FRAUD" else 0)
            for c in resolved_cases if c.transaction_id
        }

        # Query recent transactions with rule evaluation
        recent_txs = (
            db.query(Transaction)
            .order_by(Transaction.created_at.desc())
            .limit(300)
            .all()
        )

        rule_stats: Dict[str, Dict[str, Any]] = {
            "R001_VELOCITY_BURST": {
                "name": "High Velocity Transaction Spike",
                "category": "VELOCITY",
                "hits": 0,
                "fraud_hits": 0,
                "legit_hits": 0,
            },
            "R002_HIGH_AMOUNT_ANOMALY": {
                "name": "Amount Multiplier Anomaly",
                "category": "AMOUNT_DEVIATION",
                "hits": 0,
                "fraud_hits": 0,
                "legit_hits": 0,
            },
            "R003_NEW_DEVICE_NIGHT": {
                "name": "New Device Night-Time Access",
                "category": "DEVICE_TELEMETRY",
                "hits": 0,
                "fraud_hits": 0,
                "legit_hits": 0,
            },
            "R004_EMULATOR_SPOOF": {
                "name": "Emulator Hardware Spoofing",
                "category": "DEVICE_TELEMETRY",
                "hits": 0,
                "fraud_hits": 0,
                "legit_hits": 0,
            },
            "R005_LOCATION_MISMATCH": {
                "name": "Cross-Border / Location Mismatch",
                "category": "GEOGRAPHIC",
                "hits": 0,
                "fraud_hits": 0,
                "legit_hits": 0,
            },
        }

        for tx in recent_txs:
            tx_id = tx.transaction_id
            actual = ground_truth.get(tx_id)
            amt = float(tx.amount or 0.0)
            dev = getattr(tx, "device_type", "") or ""
            hour = int(tx.transaction_hour or 12)
            country = getattr(tx, "transaction_country", "US") or "US"
            f_prob = float(tx.fraud_probability or 0.0)

            # R001: High amount spike
            if amt >= 1000.0 or (amt > 500 and f_prob > 0.6):
                cls._record_hit(rule_stats["R002_HIGH_AMOUNT_ANOMALY"], actual)

            # R002: Velocity / multi tx by same customer
            if (tx.risk_score or 0) > 70:
                cls._record_hit(rule_stats["R001_VELOCITY_BURST"], actual)

            # R003: Night-time transaction
            if hour in [0, 1, 2, 3, 4, 23] and amt > 300:
                cls._record_hit(rule_stats["R003_NEW_DEVICE_NIGHT"], actual)

            # R004: Emulator or spoofed device
            if dev in ["emulator", "rooted_android", "bot"]:
                cls._record_hit(rule_stats["R004_EMULATOR_SPOOF"], actual)

            # R005: International cross border
            if country not in ["US", "USA", "DOMESTIC"]:
                cls._record_hit(rule_stats["R005_LOCATION_MISMATCH"], actual)

        results: List[RuleEffectivenessItem] = []
        for rid, s in rule_stats.items():
            total = max(1, s["hits"])
            fraud_hits = s["fraud_hits"]
            legit_hits = s["legit_hits"]
            fpr = round(legit_hits / total, 3) if total > 0 else 0.0
            # Effectiveness: higher weight for fraud catch, penalty for FP
            eff = round(min(1.0, max(0.05, (fraud_hits * 1.5 + (total - legit_hits) * 0.5) / (total * 2.0))), 3)

            rec = "MAINTAIN"
            if fpr > 0.40:
                rec = "TIGHTEN_THRESHOLDS"
            elif fraud_hits > 3 and eff > 0.80:
                rec = "PROMOTE_HARD_BLOCK"

            results.append(
                RuleEffectivenessItem(
                    rule_id=rid,
                    rule_name=s["name"],
                    category=s["category"],
                    total_hits=s["hits"],
                    confirmed_fraud_hits=fraud_hits,
                    confirmed_legitimate_hits=legit_hits,
                    false_positive_rate=fpr,
                    effectiveness_score=eff,
                    status="ACTIVE",
                    recommendation=rec,
                )
            )

        return results

    @classmethod
    def _record_hit(cls, stat: Dict[str, Any], actual: Optional[int]) -> None:
        stat["hits"] += 1
        if actual == 1:
            stat["fraud_hits"] += 1
        elif actual == 0:
            stat["legit_hits"] += 1

    @classmethod
    def list_candidate_rules(cls) -> List[CandidateRuleItem]:
        """List all proposed candidate rules."""
        return [CandidateRuleItem(**r) for r in cls._candidate_rules]

    @classmethod
    def create_candidate_rule(
        cls,
        payload: CandidateRuleCreate,
        db: Session,
        admin_id: Optional[int] = None,
    ) -> CandidateRuleItem:
        """Submit a candidate rule for testing and review. Requires admin approval before activation."""
        now_iso = datetime.now(timezone.utc).isoformat()
        item_dict = {
            "rule_id": payload.rule_id,
            "rule_name": payload.rule_name,
            "condition_description": payload.condition_description,
            "category": payload.category,
            "proposed_action": payload.proposed_action,
            "rationale": payload.rationale,
            "status": "CANDIDATE",
            "created_at": now_iso,
            "created_by": f"Admin #{admin_id}" if admin_id else "System Intelligence",
        }
        cls._candidate_rules.append(item_dict)

        # Audit log
        db.add(
            AuditLog(
                user_id=admin_id,
                action="CANDIDATE_RULE_CREATED",
                resource_type="rule_engine",
                resource_id=payload.rule_id,
                details=json.dumps(item_dict),
            )
        )
        db.commit()

        return CandidateRuleItem(**item_dict)

    @classmethod
    def approve_candidate_rule(
        cls,
        rule_id: str,
        db: Session,
        admin_id: Optional[int] = None,
    ) -> CandidateRuleItem:
        """Approve and promote a candidate rule. Never silently modifies active production rules."""
        for r in cls._candidate_rules:
            if r["rule_id"] == rule_id:
                r["status"] = "APPROVED"
                db.add(
                    AuditLog(
                        user_id=admin_id,
                        action="CANDIDATE_RULE_APPROVED",
                        resource_type="rule_engine",
                        resource_id=rule_id,
                        details=f"Rule {rule_id} approved for production deployment by Admin.",
                    )
                )
                db.commit()
                return CandidateRuleItem(**r)

        raise ValueError(f"Candidate rule '{rule_id}' not found.")

    @classmethod
    def reject_candidate_rule(
        cls,
        rule_id: str,
        reason: str,
        db: Session,
        admin_id: Optional[int] = None,
    ) -> CandidateRuleItem:
        """Reject a candidate rule with recorded rationale."""
        for r in cls._candidate_rules:
            if r["rule_id"] == rule_id:
                r["status"] = "REJECTED"
                db.add(
                    AuditLog(
                        user_id=admin_id,
                        action="CANDIDATE_RULE_REJECTED",
                        resource_type="rule_engine",
                        resource_id=rule_id,
                        details=f"Rule {rule_id} rejected. Reason: {reason}",
                    )
                )
                db.commit()
                return CandidateRuleItem(**r)

        raise ValueError(f"Candidate rule '{rule_id}' not found.")
