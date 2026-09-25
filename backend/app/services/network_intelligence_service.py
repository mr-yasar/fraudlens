"""
Fraud Network & Relationship Graph Intelligence Service.
Part D & E: Fraud Intelligence Fabric.

Extracts relationship topologies, entity links, shared device clusters,
and collusive merchant/mule rings using the existing SQLite database.
"""

from collections import defaultdict
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple
from sqlalchemy import func, desc, or_
from sqlalchemy.orm import Session

from backend.app.models.customer import Customer
from backend.app.models.transaction import Transaction
from backend.app.models.payment_intent import PaymentIntent
from backend.app.models.investigation import Investigation


@dataclass
class NetworkGraphNode:
    """Node representation in relationship graph."""
    id: str
    label: str
    node_type: str                     # customer | device | merchant | investigation
    risk_level: str                    # LOW | MEDIUM | HIGH | CRITICAL
    risk_score: float                  # 0 - 100
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class NetworkGraphEdge:
    """Directed/undirected edge in relationship graph."""
    id: str
    source: str
    target: str
    relationship: str                  # USES_DEVICE | TRANSACTS_WITH | FLAGGED_IN | SHARED_HARDWARE_LINK | SHARED_BENEFICIARY_LINK
    weight: float                      # 0.0 - 1.0
    is_suspicious: bool
    evidence: str


@dataclass
class NetworkIntelligenceReport:
    """Network risk diagnostic assessment for a transaction."""
    customer_id: str
    network_risk_score: float          # 0.0 - 100.0
    risk_level: str                    # LOW | MEDIUM | HIGH
    connected_entity_count: int
    suspicious_connection_count: int
    shared_device_count: int           # Number of other customers sharing same device
    shared_beneficiary_count: int      # Number of other customers sharing same merchant
    cluster_indicators: List[str]      # List of detected cluster tags
    associated_case_ids: List[str]
    evidence: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class FraudNetworkIntelligenceService:
    """Extracts entity connection graphs, multi-hop links, and syndicated fraud rings."""

    @classmethod
    def evaluate_network_risk(
        cls,
        db: Session,
        customer_id: str,
        device_type: Optional[str] = "web",
        device_id: Optional[str] = None,
        merchant_name: Optional[str] = None,
        amount: Optional[float] = None,
    ) -> NetworkIntelligenceReport:
        """
        Evaluate customer and transaction relationship topology for synthetic rings and shared devices.
        Uses non-blocking indexed queries over existing SQLite tables.
        """
        effective_merchant = (merchant_name or "").strip().lower()
        shared_device_customers: Set[str] = set()
        generic_platforms = {"web", "mobile", "pos", "mobile_ios", "mobile_android", "web_browser", "desktop_windows", "desktop_mac", "ios", "android"}
        target_device = device_id or device_type
        effective_device = target_device or "unknown"
        if target_device and target_device.strip().lower() not in generic_platforms:
            dev_val = target_device.strip().lower()
            device_txs = (
                db.query(Transaction.customer_id)
                .filter(
                    or_(
                        func.lower(Transaction.device_id) == dev_val,
                        func.lower(Transaction.device_type) == dev_val,
                    ),
                    Transaction.customer_id != customer_id,
                )
                .distinct()
                .limit(20)
                .all()
            )
            for (c_id,) in device_txs:
                if c_id:
                    shared_device_customers.add(c_id)

        # 2. Find other customers transacting with the same merchant / beneficiary
        shared_beneficiary_customers: Set[str] = set()
        if effective_merchant:
            merchant_intents = (
                db.query(PaymentIntent.customer_id)
                .filter(
                    func.lower(PaymentIntent.merchant_name) == effective_merchant,
                    PaymentIntent.customer_id != customer_id,
                )
                .distinct()
                .limit(30)
                .all()
            )
            for (c_id,) in merchant_intents:
                if c_id:
                    shared_beneficiary_customers.add(c_id)

        # 3. Check for historical fraud investigations linked to customer
        customer_cases = (
            db.query(Investigation)
            .join(Transaction, Investigation.transaction_id == Transaction.transaction_id)
            .filter(Transaction.customer_id == customer_id)
            .all()
        )
        case_ids = [c.case_id for c in customer_cases if c.case_id]
        has_fraud_history = any(c.decision == "CONFIRMED_FRAUD" for c in customer_cases)

        # 4. Check if shared device customers have confirmed fraud cases
        shared_fraud_entities: Set[str] = set()
        if shared_device_customers:
            shared_cases = (
                db.query(Transaction.customer_id, Investigation.decision)
                .join(Investigation, Transaction.transaction_id == Investigation.transaction_id)
                .filter(Transaction.customer_id.in_(list(shared_device_customers)))
                .all()
            )
            for cust_id, decision in shared_cases:
                if decision in ["CONFIRMED_FRAUD", "BLOCK"]:
                    shared_fraud_entities.add(cust_id)

        # Compute Network Risk Metrics
        shared_dev_count = len(shared_device_customers)
        shared_ben_count = len(shared_beneficiary_customers)
        connected_entities = 1 + shared_dev_count + (1 if effective_merchant else 0) + len(case_ids)

        net_score = 0.0
        suspicious_connections = 0
        clusters: List[str] = []
        evidence: List[str] = []

        # Ring / Shared Device Penalties
        if len(shared_fraud_entities) > 0:
            net_score += 60.0
            suspicious_connections += len(shared_fraud_entities)
            clusters.append("KNOWN_FRAUD_RING_LINK")
            evidence.append(f"Device profile '{effective_device}' is linked to {len(shared_fraud_entities)} account(s) with confirmed fraud history.")
        elif shared_dev_count >= 3:
            net_score += 45.0
            suspicious_connections += shared_dev_count
            clusters.append("SHARED_DEVICE_CLUSTER")
            evidence.append(f"Elevated hardware sharing: Device associated with {shared_dev_count} distinct customer accounts.")
        elif shared_dev_count >= 1:
            net_score += 15.0
            suspicious_connections += 1
            clusters.append("MULTI_ACCOUNT_DEVICE")
            evidence.append(f"Device is shared with {shared_dev_count} other customer account.")

        # Merchant / Mule Concentration
        if effective_merchant in ["crypto_exchange", "offshore_wire", "darknet_market", "unregulated_fx"]:
            net_score += 35.0
            suspicious_connections += 1
            clusters.append("HIGH_RISK_MERCHANT_HUB")
            evidence.append(f"Beneficiary '{merchant_name}' is classified as a high-risk settlement hub.")

        if has_fraud_history:
            net_score += 25.0
            suspicious_connections += len(case_ids)
            clusters.append("PRIOR_INVESTIGATION_HISTORY")
            evidence.append(f"Customer has {len(case_ids)} prior investigation case(s) on record.")

        final_net_score = min(100.0, max(0.0, round(net_score, 2)))

        if final_net_score >= 70.0:
            tier = "HIGH"
        elif final_net_score >= 35.0:
            tier = "MEDIUM"
        else:
            tier = "LOW"

        return NetworkIntelligenceReport(
            customer_id=customer_id,
            network_risk_score=final_net_score,
            risk_level=tier,
            connected_entity_count=connected_entities,
            suspicious_connection_count=suspicious_connections,
            shared_device_count=shared_dev_count,
            shared_beneficiary_count=shared_ben_count,
            cluster_indicators=clusters,
            associated_case_ids=case_ids,
            evidence=evidence,
        )

    @classmethod
    def build_relationship_subgraph(
        cls,
        db: Session,
        customer_id: str,
        depth: int = 2,
    ) -> Dict[str, Any]:
        """
        Generate lightweight nodes and edges for frontend relationship visualization.
        """
        nodes: Dict[str, Dict[str, Any]] = {}
        edges: List[Dict[str, Any]] = []

        # 1. Target Customer Root Node
        customer = db.query(Customer).filter(Customer.customer_id == customer_id).first()
        cust_tenure = customer.account_age_days if customer else 90

        nodes[f"cust_{customer_id}"] = {
            "id": f"cust_{customer_id}",
            "label": f"Customer: {customer_id}",
            "node_type": "customer",
            "risk_level": "LOW",
            "risk_score": 10.0,
            "metadata": {"account_age_days": cust_tenure, "is_root": True},
        }

        # 2. Historical Transactions & Devices
        transactions = (
            db.query(Transaction)
            .filter(Transaction.customer_id == customer_id)
            .order_by(Transaction.created_at.desc())
            .limit(25)
            .all()
        )

        devices_seen: Set[str] = set()
        merchants_seen: Set[str] = set()

        for tx in transactions:
            tx_id = tx.transaction_id
            tx_risk = tx.risk_level or "LOW"
            tx_score = float(tx.risk_score or 15.0)

            # Transaction Node
            nodes[f"tx_{tx_id}"] = {
                "id": f"tx_{tx_id}",
                "label": f"${float(tx.amount):,.2f}",
                "node_type": "transaction",
                "risk_level": tx_risk,
                "risk_score": tx_score,
                "metadata": {
                    "amount": float(tx.amount),
                    "created_at": tx.created_at.isoformat() if tx.created_at else None,
                },
            }

            # Customer -> Transaction Edge
            edges.append({
                "id": f"e_c_{customer_id}_tx_{tx_id}",
                "source": f"cust_{customer_id}",
                "target": f"tx_{tx_id}",
                "relationship": "INITIATED_PAYMENT",
                "weight": 1.0,
                "is_suspicious": (tx_risk in ["HIGH", "CRITICAL"]),
                "evidence": f"Transaction of ${float(tx.amount):,.2f}",
            })

            # Device Node & Edge
            if tx.device_type:
                dev_key = tx.device_type.lower().strip()
                dev_node_id = f"dev_{dev_key}"
                if dev_key not in devices_seen:
                    devices_seen.add(dev_key)
                    nodes[dev_node_id] = {
                        "id": dev_node_id,
                        "label": f"Device: {dev_key}",
                        "node_type": "device",
                        "risk_level": "MEDIUM" if dev_key in ["tor", "proxy", "android_emulator"] else "LOW",
                        "risk_score": 50.0 if dev_key in ["tor", "proxy"] else 15.0,
                        "metadata": {"device_type": dev_key},
                    }

                edges.append({
                    "id": f"e_tx_{tx_id}_{dev_node_id}",
                    "source": f"tx_{tx_id}",
                    "target": dev_node_id,
                    "relationship": "EXECUTED_ON_DEVICE",
                    "weight": 0.8,
                    "is_suspicious": (dev_key in ["tor", "proxy"]),
                    "evidence": f"Hardware channel: {dev_key}",
                })

            # Merchant Node & Edge
            if tx.merchant_category:
                m_key = tx.merchant_category.lower().strip()
                m_node_id = f"merch_{m_key}"
                if m_key not in merchants_seen:
                    merchants_seen.add(m_key)
                    nodes[m_node_id] = {
                        "id": m_node_id,
                        "label": f"Category: {m_key}",
                        "node_type": "merchant",
                        "risk_level": "HIGH" if "crypto" in m_key else "LOW",
                        "risk_score": 75.0 if "crypto" in m_key else 10.0,
                        "metadata": {"category": m_key},
                    }

                edges.append({
                    "id": f"e_tx_{tx_id}_{m_node_id}",
                    "source": f"tx_{tx_id}",
                    "target": m_node_id,
                    "relationship": "ROUTED_TO_MERCHANT",
                    "weight": 0.7,
                    "is_suspicious": ("crypto" in m_key),
                    "evidence": f"Settlement category: {m_key}",
                })

        # 3. Add Investigation Nodes
        investigations = (
            db.query(Investigation)
            .join(Transaction, Investigation.transaction_id == Transaction.transaction_id)
            .filter(Transaction.customer_id == customer_id)
            .all()
        )

        for inv in investigations:
            inv_id = f"case_{inv.case_id}"
            nodes[inv_id] = {
                "id": inv_id,
                "label": f"Case: {inv.case_id}",
                "node_type": "investigation",
                "risk_level": "HIGH" if inv.decision == "CONFIRMED_FRAUD" else "MEDIUM",
                "risk_score": 85.0 if inv.decision == "CONFIRMED_FRAUD" else 45.0,
                "metadata": {"status": inv.status, "decision": inv.decision},
            }

            edges.append({
                "id": f"e_tx_{inv.transaction_id}_{inv_id}",
                "source": f"tx_{inv.transaction_id}",
                "target": inv_id,
                "relationship": "OPENED_INVESTIGATION",
                "weight": 1.0,
                "is_suspicious": True,
                "evidence": f"Case status: {inv.status} (Decision: {inv.decision})",
            })

        return {
            "root_customer_id": customer_id,
            "total_nodes": len(nodes),
            "total_edges": len(edges),
            "nodes": list(nodes.values()),
            "edges": edges,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    @classmethod
    def get_network_clusters_overview(cls, db: Session) -> Dict[str, Any]:
        """
        Global overview of high-density clusters, shared device nodes, and elevated risk rings.
        """
        # 1. Detect multi-account devices
        shared_devices_q = (
            db.query(Transaction.device_type, func.count(func.distinct(Transaction.customer_id)).label("cust_count"))
            .filter(Transaction.device_type.isnot(None))
            .group_by(Transaction.device_type)
            .having(func.count(func.distinct(Transaction.customer_id)) > 1)
            .order_by(desc("cust_count"))
            .limit(10)
            .all()
        )

        shared_devices = [
            {"device_type": dev, "linked_customers_count": cnt, "risk_tier": "HIGH" if cnt >= 3 else "MEDIUM"}
            for dev, cnt in shared_devices_q
            if dev
        ]

        # 2. Count active investigation clusters
        active_cases_count = db.query(Investigation).filter(Investigation.status.in_(["OPEN", "IN_REVIEW"])).count()
        total_customers = db.query(Customer).count()
        total_transactions = db.query(Transaction).count()

        return {
            "total_monitored_entities": total_customers + total_transactions,
            "shared_hardware_clusters_count": len(shared_devices),
            "shared_hardware_clusters": shared_devices,
            "active_investigation_cases": active_cases_count,
            "network_health_status": "NORMAL" if len(shared_devices) < 5 else "ELEVATED_SYNDICATE_ACTIVITY",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
