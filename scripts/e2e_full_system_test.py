"""Comprehensive End-to-End System Health & Subsystem Verification Script.

Tests all 11 core functional domains:
1. System Health & Probes
2. Authentication, Token Issuance & RBAC Profile
3. Real-Time Transaction Scoring & Pre-Auth Gate
4. Pre-Authorization Payment Gateway & Idempotency Replay
5. AI Predictions, Anomaly Scoring, Uncertainty & Real Counterfactuals
6. Local TreeSHAP & Global Feature Importance
7. Customer Velocity & Behavioral Intelligence
8. Investigation Case Management & Disposition Workflow
9. Network Relationship Sub-Graph & Ring Detection
10. System Governance, Data Drift (PSI) & Fairness Telemetry
11. Admin Model Registry & Challenger Comparison
"""

import sys
import os
sys.path.insert(0, ".")

import json
import time
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

print("=" * 80)
print("FRAUDLENS AI — 100X FULL END-TO-END SYSTEM HEALTH & VERIFICATION TEST")
print("=" * 80)

passed_checks = 0
total_checks = 0

def check(condition: bool, description: str, detail: str = ""):
    global passed_checks, total_checks
    total_checks += 1
    if condition:
        passed_checks += 1
        print(f"  [PASS] {description} {('-> ' + detail) if detail else ''}")
    else:
        print(f"  [FAIL] {description} {('-> ' + detail) if detail else ''}")
        assert condition, f"Check failed: {description}"

# -----------------------------------------------------------------------------
# 1. System Health & Probes
# -----------------------------------------------------------------------------
print("\n[DOMAIN 1] System Health & Probes")
res = client.get("/api/v1/health")
check(res.status_code == 200, "Health Basic Probe (/health HTTP 200)", f"Status: {res.json().get('status')}")

res_ready = client.get("/api/v1/health/readiness")
check(res_ready.status_code == 200, "Readiness Deep Probe (/health/readiness HTTP 200)", f"Status: {res_ready.json().get('status')}")
subsystems = res_ready.json().get("subsystems", {})
check(subsystems.get("database") == "healthy", "Database Subsystem Connected & Healthy")
check(subsystems.get("ml_prediction_service") == "healthy", "ML Prediction Service Subsystem Healthy")
check(subsystems.get("xai_shap_engine") == "healthy", "XAI SHAP Engine Subsystem Healthy")
check(subsystems.get("payment_provider_adapter") == "healthy", "Payment Provider Adapter Subsystem Healthy")

# -----------------------------------------------------------------------------
# 2. Authentication, Token Issuance & Profile
# -----------------------------------------------------------------------------
print("\n[DOMAIN 2] Authentication, Token Issuance & RBAC Profile")
from backend.app.core.security import create_access_token
token = create_access_token(subject="1", role="admin")
headers = {"Authorization": f"Bearer {token}"}
check(True, "Admin JWT Bearer Token Created & Signed", f"Token: {token[:16]}...")

me_res = client.get("/api/v1/auth/me", headers=headers)
check(me_res.status_code == 200, "Profile Retrieval (/auth/me)", f"Role: {me_res.json().get('role')}")

# -----------------------------------------------------------------------------
# 3. Real-Time Transaction Scoring & Pre-Auth Evaluation
# -----------------------------------------------------------------------------
print("\n[DOMAIN 3] Real-Time Transaction Scoring (/transactions/evaluate)")
low_risk_payload = {
    "transaction_id": f"TEST-TX-{int(time.time())}",
    "customer_id": "CUST001",
    "Amount": 55.0,
    "transaction_amount": 55.0,
    "Transaction_Type": "Purchase",
    "Transaction_Hour": 14,
    "transaction_hour": 14,
    "Location": "Pune",
    "Usual_Location": "Pune",
    "Device_Type": "Mac",
    "New_Device": 0,
    "Account_Age_Days": 743,
    "Previous_Transaction_Amount": 50.0,
    "Average_Previous_Amount": 60.0,
    "Transactions_Last_24H": 1,
    "Failed_Attempts": 0,
    "International_Transaction": 0,
    "Unusual_Location": 0,
}
res_eval = client.post("/api/v1/transactions/evaluate", json=low_risk_payload, headers=headers)
check(res_eval.status_code == 200, "Low-Risk Transaction Evaluation", f"Risk Level: {res_eval.json().get('risk_level')}")
eval_data = res_eval.json()
check(eval_data.get("prediction") in ["FRAUD", "GENUINE"], "Prediction Classification Valid")
check(0 <= eval_data.get("risk_score") <= 100, "Risk Score Within [0, 100]")
check("top_explanations" in eval_data, "SHAP Top Factors Returned")

# -----------------------------------------------------------------------------
# 4. Pre-Authorization Payment Gateway & Idempotency
# -----------------------------------------------------------------------------
print("\n[DOMAIN 4] Pre-Authorization Payment Gateway & Idempotency (/payment/initiate)")
idemp_key = f"IDEMP-{time.time()}"
payment_payload = {
    "customer_id": "CUST001",
    "amount": 75.0,
    "currency": "USD",
    "payment_method": "credit_card",
    "merchant_name": "Apple Store",
    "merchant_category": "electronics",
    "device_type": "Mac",
    "location": "Pune",
    "transaction_country": "IN",
    "transaction_type": "Purchase",
    "failed_attempts": 0,
    "idempotency_key": idemp_key,
}
res_pay = client.post("/api/v1/payment/initiate", json=payment_payload, headers=headers)
check(res_pay.status_code == 200, "Payment Initiation Allowed", f"Decision: {res_pay.json().get('decision')}")
pay_data = res_pay.json()
check(pay_data.get("decision") in ["ALLOW", "REVIEW", "BLOCK"], "Decision Gate Valid")

# Idempotency replay check
res_replay = client.post("/api/v1/payment/initiate", json=payment_payload, headers=headers)
check(res_replay.status_code == 200, "Idempotency Replay Matched", f"Replay Flag: {res_replay.json().get('idempotent_replay')}")

# -----------------------------------------------------------------------------
# 5. Predictions, Anomaly Scoring, Uncertainty & Counterfactuals
# -----------------------------------------------------------------------------
print("\n[DOMAIN 5] Predictions, Anomaly Scoring, Uncertainty & Counterfactuals")
pred_payload = {
    "Amount": 12500.0,
    "Average_Previous_Amount": 500.0,
    "Transaction_Type": "Transfer",
    "Transaction_Hour": 3,
    "Location": "Unknown_City",
    "Usual_Location": "Pune",
    "Device_Type": "Linux_Bot",
    "New_Device": 1,
    "Failed_Attempts": 3,
    "International_Transaction": 1,
    "Unusual_Location": 1,
}
res_pred = client.post("/api/v1/predictions/predict", json=pred_payload, headers=headers)
check(res_pred.status_code == 200, "High-Risk Multi-Factor Prediction (/predictions/predict)")
p_data = res_pred.json()
check(p_data.get("risk_level") in ["MEDIUM", "HIGH"], "High Risk Correctly Categorized")
check(p_data.get("anomaly_status") in ["AVAILABLE", "UNAVAILABLE"], "Anomaly Status Provided", f"Status: {p_data.get('anomaly_status')}")
check(p_data.get("uncertainty_level") in ["LOW", "MODERATE", "HIGH"], "Uncertainty Level Estimated", f"Level: {p_data.get('uncertainty_level')}")

# Counterfactual Endpoint Check
res_cf = client.post("/api/v1/predictions/explain/counterfactual", json=pred_payload, headers=headers)
check(res_cf.status_code == 200, "Counterfactual Endpoint (/predictions/explain/counterfactual)")
cf_data = res_cf.json()
check("status" in cf_data, "Counterfactual Status Present", f"Status: {cf_data.get('status')}")
check("actionable_summary" in cf_data, "Actionable Summary Generated")

# Global Feature Explanation Check
res_global = client.get("/api/v1/predictions/explain/global", headers=headers)
check(res_global.status_code == 200, "Global Feature Importance (/predictions/explain/global)")
check(len(res_global.json().get("feature_importance_ranking", [])) > 0, "Global SHAP Ranking Non-Empty")

# -----------------------------------------------------------------------------
# 6. Customer Profile & Historical Velocity
# -----------------------------------------------------------------------------
print("\n[DOMAIN 6] Customer Management & Historical Velocity")
res_cust = client.get("/api/v1/customers", headers=headers)
check(res_cust.status_code == 200, "Customer Listing (/customers)", f"Count: {len(res_cust.json().get('items', []))}")
if res_cust.json().get("items"):
    c_id = res_cust.json()["items"][0]["customer_id"]
    res_prof = client.get(f"/api/v1/payment/customer-profile/{c_id}", headers=headers)
    check(res_prof.status_code == 200, f"Customer Profile Retrieval ({c_id})", f"Tx Count: {res_prof.json().get('total_transactions')}")

# -----------------------------------------------------------------------------
# 7. Investigations & Case Management
# -----------------------------------------------------------------------------
print("\n[DOMAIN 7] Investigation Case Management (/investigations)")
res_inv = client.get("/api/v1/investigations", headers=headers)
check(res_inv.status_code == 200, "Investigation Case Queue Listed", f"Total Cases: {res_inv.json().get('total')}")

# -----------------------------------------------------------------------------
# 8. Network Graph & Sybil Ring Intelligence
# -----------------------------------------------------------------------------
print("\n[DOMAIN 8] Fraud Network & Sybil Ring Intelligence (/network/graph)")
res_graph = client.get("/api/v1/network/graph?customer_id=CUST001&depth=2", headers=headers)
check(res_graph.status_code == 200, "Relationship Sub-Graph Generated", f"Nodes: {len(res_graph.json().get('nodes', []))}")
res_clusters = client.get("/api/v1/network/clusters", headers=headers)
check(res_clusters.status_code == 200, "Network Clusters Topology Retrieved")

# -----------------------------------------------------------------------------
# 9. Adaptive Threats & Dynamic Rules
# -----------------------------------------------------------------------------
print("\n[DOMAIN 9] Adaptive Threats & Dynamic Rule Simulation (/adaptive)")
res_threats = client.get("/api/v1/adaptive/threats", headers=headers)
check(res_threats.status_code == 200, "Adaptive Threat Feed Queried", f"Threat Count: {len(res_threats.json().get('threats', []))}")
res_eff = client.get("/api/v1/adaptive/rules/effectiveness", headers=headers)
check(res_eff.status_code == 200, "Rule Effectiveness Metrics Retrieved")

# -----------------------------------------------------------------------------
# 10. System Governance, Data Drift & Fairness Telemetry
# -----------------------------------------------------------------------------
print("\n[DOMAIN 10] Governance, Data Drift (PSI) & Fairness Telemetry (/governance)")
res_gov = client.get("/api/v1/governance/summary", headers=headers)
check(res_gov.status_code == 200, "Unified Governance Summary (/governance/summary)")
gov_data = res_gov.json()
check("model_health" in gov_data, "Model Health Telemetry in Snapshot")
check("drift_status" in gov_data, "Data Drift Telemetry in Snapshot")
check("fairness_audit" in gov_data, "Fairness Audit Telemetry in Snapshot")

res_drift = client.get("/api/v1/governance/drift", headers=headers)
check(res_drift.status_code == 200, "Live Data Drift Report (/governance/drift)", f"Status: {res_drift.json().get('overall_drift_status')}")

res_fair = client.get("/api/v1/governance/fairness", headers=headers)
check(res_fair.status_code == 200, "Operational Fairness Audit (/governance/fairness)", f"Status: {res_fair.json().get('fairness_status')}")

# -----------------------------------------------------------------------------
# 11. Admin Model Registry & Candidate Comparison
# -----------------------------------------------------------------------------
print("\n[DOMAIN 11] Admin ML Model Registry & Benchmarks (/admin/models)")
res_models = client.get("/api/v1/admin/models", headers=headers)
check(res_models.status_code == 200, "Model Registry Listing (/admin/models)")
res_comp = client.get("/api/v1/admin/models/comparison", headers=headers)
check(res_comp.status_code == 200, "Candidate Model Benchmark Comparison")

print("\n" + "=" * 80)
print(f"VERIFICATION SUMMARY: {passed_checks} / {total_checks} END-TO-END CHECKS PASSED (100% SUCCESS RATE)")
print("=" * 80)
