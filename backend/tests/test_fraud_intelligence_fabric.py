"""
Fraud Intelligence Fabric Test Suite (Parts A through K).
Validates Continuous Behaviour Intelligence, Device/Session Risk, Network Graphs, and Risk Engine Integration.
"""

import uuid
from decimal import Decimal
from datetime import datetime, timezone, timedelta
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.core.database import Base, get_db
from backend.app.models.user import User
from backend.app.models.customer import Customer
from backend.app.models.transaction import Transaction
from backend.app.models.investigation import Investigation
from backend.app.schemas.user import UserRole
from backend.app.schemas.payment import PaymentInitiateRequest
from backend.app.services.behavior_intelligence_service import CustomerBehaviourIntelligenceService
from backend.app.services.device_session_service import DeviceSessionRiskService
from backend.app.services.network_intelligence_service import FraudNetworkIntelligenceService
from backend.app.services.risk_decision_orchestrator import RiskDecisionOrchestrator
from backend.app.core.security import get_password_hash, create_access_token

test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="module", autouse=True)
def setup_intelligence_test_env():
    app.dependency_overrides[get_db] = override_get_db
    Base.metadata.create_all(bind=test_engine)
    db = TestingSessionLocal()

    # User
    user = User(
        name="Intelligence Admin",
        email="intel_admin@test.internal",
        password_hash=get_password_hash("IntelAdminPass123!"),
        role=UserRole.ADMIN.value,
        is_active=True,
    )
    db.add(user)

    # Customers
    c1 = Customer(customer_id="CUST-INTEL-01", account_age_days=300)
    c2 = Customer(customer_id="CUST-INTEL-02", account_age_days=150)
    c_cold = Customer(customer_id="CUST-INTEL-COLD", account_age_days=5)
    db.add_all([c1, c2, c_cold])
    db.commit()

    # Baseline transactions for C1 (Known iPhone in California, retail, avg $60)
    past_time = datetime.now(timezone.utc) - timedelta(days=5)
    for i in range(6):
        db.add(Transaction(
            transaction_id=f"TX-INTEL-C1-{i}",
            customer_id="CUST-INTEL-01",
            amount=55.0 + (i * 2.0),
            transaction_hour=14,
            merchant_category="retail",
            transaction_country="US",
            geo_location_region="CA",
            device_type="iphone_shared_01",
            transaction_type="online_payment",
            fraud_probability=0.01,
            risk_score=5.0,
            risk_level="LOW",
            created_at=past_time + timedelta(hours=i * 6),
        ))

    # Baseline transactions for C2 (Also using iphone_shared_01 to create multi-account device link)
    for i in range(3):
        db.add(Transaction(
            transaction_id=f"TX-INTEL-C2-{i}",
            customer_id="CUST-INTEL-02",
            amount=80.0,
            transaction_hour=16,
            merchant_category="electronics",
            transaction_country="US",
            geo_location_region="CA",
            device_type="iphone_shared_01",
            transaction_type="online_payment",
            fraud_probability=0.05,
            risk_score=10.0,
            risk_level="LOW",
            created_at=past_time + timedelta(hours=i * 8),
        ))

    db.commit()
    db.close()
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def auth_headers():
    token = create_access_token(subject="1", role="ADMIN")
    return {"Authorization": f"Bearer {token}"}


def test_continuous_behavior_intelligence_normal_and_anomalous():
    """Validates baseline calculations, amount deviations, and cold-start handling."""
    db = TestingSessionLocal()
    try:
        # 1. Normal transaction for customer with history
        normal_rep = CustomerBehaviourIntelligenceService.evaluate_behavior(
            db=db,
            customer_id="CUST-INTEL-01",
            amount=60.0,
            device_type="iphone_shared_01",
            location="CA",
        )
        assert normal_rep.is_cold_start is False
        assert normal_rep.confidence_level in ["MEDIUM", "HIGH"]
        assert normal_rep.historical_avg_amount > 50.0
        assert normal_rep.behaviour_deviation_score < 30.0
        assert normal_rep.behaviour_risk_level == "LOW"

        # 2. Anomalous transaction (5x amount spike, cross-border, unusual location)
        spike_rep = CustomerBehaviourIntelligenceService.evaluate_behavior(
            db=db,
            customer_id="CUST-INTEL-01",
            amount=900.0,
            device_type="unrecognized_device_99",
            location="London",
            transaction_country="GB",
            failed_attempts=2,
        )
        assert spike_rep.is_cross_border is True
        assert spike_rep.is_new_device is True
        assert spike_rep.is_unusual_location is True
        assert spike_rep.behaviour_deviation_score >= 40.0
        assert len(spike_rep.evidence) >= 2

        # 3. Cold-start customer
        cold_rep = CustomerBehaviourIntelligenceService.evaluate_behavior(
            db=db,
            customer_id="CUST-INTEL-COLD",
            amount=120.0,
        )
        assert cold_rep.is_cold_start is True
        assert cold_rep.confidence_level == "COLD_START"
        assert cold_rep.signals["cold_start"] is True
    finally:
        db.close()


def test_device_and_session_risk_service():
    """Validates device fingerprinting, novelty detection, and spoofing flags."""
    db = TestingSessionLocal()
    try:
        # Known device
        assess_known = DeviceSessionRiskService.evaluate_device_session(
            db=db,
            customer_id="CUST-INTEL-01",
            device_type="iphone_shared_01",
            failed_attempts=0,
        )
        assert assess_known.is_novel_device is False
        assert assess_known.is_spoofed_environment is False
        assert assess_known.device_risk_score < 30.0

        # Spoofed Tor environment with failed attempts
        assess_spoof = DeviceSessionRiskService.evaluate_device_session(
            db=db,
            customer_id="CUST-INTEL-01",
            device_type="tor_exit_node_proxy",
            failed_attempts=3,
            channel="tor_exit_node",
        )
        assert assess_spoof.is_spoofed_environment is True
        assert assess_spoof.device_risk_score >= 60.0
        assert assess_spoof.session_risk_score >= 40.0
        assert assess_spoof.risk_level == "HIGH"
    finally:
        db.close()


def test_fraud_network_intelligence_and_graph_construction():
    """Validates shared hardware detection, multi-account clustering, and graph output."""
    db = TestingSessionLocal()
    try:
        # C1 evaluated on shared device 'iphone_shared_01' (used by C2 as well)
        net_rep = FraudNetworkIntelligenceService.evaluate_network_risk(
            db=db,
            customer_id="CUST-INTEL-01",
            device_type="iphone_shared_01",
            merchant_name="Target Store",
        )
        assert net_rep.shared_device_count >= 1
        assert "MULTI_ACCOUNT_DEVICE" in net_rep.cluster_indicators
        assert net_rep.connected_entity_count >= 2

        # Subgraph construction for visualization
        subgraph = FraudNetworkIntelligenceService.build_relationship_subgraph(
            db=db,
            customer_id="CUST-INTEL-01",
        )
        assert "nodes" in subgraph
        assert "edges" in subgraph
        assert subgraph["total_nodes"] > 0
        assert subgraph["total_edges"] > 0
        assert any(n["node_type"] == "customer" for n in subgraph["nodes"])
        assert any(n["node_type"] == "device" for n in subgraph["nodes"])
    finally:
        db.close()


def test_orchestrator_end_to_end_intelligence_fabric_integration(client, auth_headers):
    """Verifies that PreAuthDecisionResult includes all intelligence fabric outputs."""
    payload = {
        "customer_id": "CUST-INTEL-01",
        "amount": 55.0,
        "currency": "USD",
        "merchant_name": "Target Store",
        "merchant_category": "retail",
        "device_type": "iphone_shared_01",
        "location": "CA",
        "transaction_country": "US",
        "transaction_type": "online_payment",
        "failed_attempts": 0,
        "idempotency_key": f"intel-test-{uuid.uuid4()}",
    }

    resp = client.post("/api/v1/payment/initiate", json=payload, headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()

    # Verify Intelligence Fabric fields in response
    assert "behaviour_intelligence" in data
    assert "device_session_intelligence" in data
    assert "network_intelligence" in data
    assert data["behaviour_intelligence"] is not None
    assert data["device_session_intelligence"] is not None
    assert data["network_intelligence"] is not None
    assert "device_risk_score" in data
    assert "network_risk_score" in data
    assert "connected_entities_count" in data

    # Verify decision integrity
    assert data["decision"] == "ALLOW"
    assert data["ready_for_provider"] is True


def test_network_and_intelligence_api_endpoints(client, auth_headers):
    """Tests GET /api/v1/network/graph, /clusters, and /api/v1/intelligence endpoints."""
    # 1. Network graph
    resp_graph = client.get("/api/v1/network/graph?customer_id=CUST-INTEL-01", headers=auth_headers)
    assert resp_graph.status_code == 200
    graph_data = resp_graph.json()
    assert "nodes" in graph_data
    assert "edges" in graph_data

    # 2. Network clusters
    resp_clusters = client.get("/api/v1/network/clusters", headers=auth_headers)
    assert resp_clusters.status_code == 200
    cluster_data = resp_clusters.json()
    assert "shared_hardware_clusters" in cluster_data

    # 3. Customer behavior intelligence
    resp_intel = client.get("/api/v1/intelligence/customer/CUST-INTEL-01?amount=75.0", headers=auth_headers)
    assert resp_intel.status_code == 200
    intel_data = resp_intel.json()
    assert intel_data["customer_id"] == "CUST-INTEL-01"
    assert "historical_avg_amount" in intel_data
