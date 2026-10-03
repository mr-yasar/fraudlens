"""
Append Chapter 5: System Design to report_data.py.
"""

from pathlib import Path

output_file = Path("e:/fraudinvestigation/scripts/report_data.py")

with open(output_file, "a", encoding="utf-8") as f:
    f.write('''
# ==============================================================================
# CHAPTER 5: SYSTEM DESIGN
# ==============================================================================

CH5_TEXT = """
5.1 SYSTEM ARCHITECTURE

The architectural topology of FraudLens AI is organized as an enterprise-grade, multi-tier decoupled system engineered for ultra-low latency pre-authorization decisioning, mathematical explainability, robust multi-tenant data isolation, and comprehensive forensic intelligence. As illustrated in Figure 5.1, the system is structured into five distinct, cooperating tiers:

1. Client Presentation Tier:
   The client layer is implemented as an interactive, highly responsive Single Page Application (SPA) built on React 18, Vite, and modern styling tokens. It serves three distinct operational personas:
   • Cardholder & Customer Space: Provides instant pre-authorization payment simulation, personal wallet balance tracking, self-ledger inspection, and the realistic smartphone SMS OTP verification modal.
   • Fraud Investigator Command Center: Features real-time streaming transaction radars, live risk telemetry, multi-merchant risk surveillance grids, horizontal TreeSHAP waterfall attribution visualizers, and the AI Forensic Copilot interface.
   • Security Administrator Console: Enables machine learning model registry management, candidate model tournament benchmarking, dataset schema health auditing, and immutable audit log inspection.
   The presentation tier communicates with the backend via secure HTTPS REST APIs for transactional operations and persistent full-duplex WebSocket connections for sub-second telemetry broadcasting.

2. API Gateway & Security Tier:
   The entry portal is governed by a high-performance FastAPI asynchronous gateway powered by Uvicorn ASGI workers. Key components include:
   • Authentication & RBAC Engine: Implements OAuth2 Password Bearer authentication with cryptographically signed JSON Web Tokens (JWT). The system strictly enforces role-based access control (CUSTOMER, FRAUD_INVESTIGATOR, ADMIN), guaranteeing that customers can never access merchant fleet intelligence or cross-customer records.
   • Idempotency & Replay Protection: Employs SHA-256 request payload fingerprinting and unique idempotency keys to intercept duplicate network transmissions, preventing double-debiting during mobile network retry spikes.
   • Compression & Rate Limiting: GZip middleware compresses responses exceeding 1KB, optimizing bandwidth across mobile connections.

3. Pre-Authorization & Risk Orchestration Tier:
   Serving as the authoritative gatekeeper, the RiskDecisionOrchestrator coordinates end-to-end payment processing:
   • Customer Balance Verification: Validates simulated account balances prior to authorization, halting requests with insufficient funds.
   • Behavioral Profiling Service: Reconstructs 30-day customer expenditure averages, immediate prior transaction amounts, 1-hour and 24-hour transaction velocities, and novel hardware/beneficiary signatures.
   • Centralized Rule Engine: Evaluates deterministic boundary heuristics (such as hard velocity blocks and known fraud ring links).
   • Deterministic Multi-Factor Risk Scorer: Combines model probability and behavioral signals into an integer score [0, 100].
   • Decision Gatekeeper: Dispatches transactions to ALLOW (0–30), REVIEW (31–70 or rapid velocity trigger), or BLOCK (71–100).

4. Machine Learning & Explainable AI (XAI) Subsystem:
   • Preprocessing & Feature Registry: The FullFraudPreprocessor applies median imputation, StandardScaler normalization, and OneHotEncoder transformations across 63 derived features, with strict target leakage prevention.
   • Candidate Model Registry: Caches serialized model artifacts (.joblib) for regularized Logistic Regression, Random Forest, XGBoost, and the Soft-Voting Stacking Ensemble.
   • TreeSHAP Explainer: Computes exact Shapley feature attributions within 1.1ms, identifying the top risk-increasing and risk-decreasing factors.
   • Counterfactual Engine & Anomaly Scorer: Provides "what-if" counterfactual perturbations and Isolation Forest unsupervised anomaly scores.

5. Data Persistence & GenAI Service Fabric:
   • Relational Persistence: An optimized SQLite database (with WAL mode enabled) managing 20 relational entities through SQLAlchemy ORM.
   • Cryptographic Audit Ledger: Records immutable chronological entries for every authentication, scoring, and administrative action.
   • GenAI Forensic Copilot: Powered by Google Gemini 1.5 Pro and xAI Grok-2, generating narrative case dossiers, visual attack flow diagrams, and regulatory SAR drafts.

5.2 CLASS DIAGRAM

The static structural composition of FraudLens AI is represented in the UML Class Diagram shown in Figure 5.2. The core domain entities and their structural relationships are defined as follows:

• User: Encapsulates authentication credentials (password_hash), assigned security role (admin, investigator, analyst, customer), account status, and tier. Maintains a 1-to-many relationship with AuditLog and Investigation entities.
• Customer: Represents individual cardholder accounts, encapsulating account_age_days, simulated_balance, currency, risk_segment, and KYC registration metadata. Maintains a 1-to-many relationship with Transaction, CustomerDevice, and Beneficiary entities.
• Merchant: Stores commercial partner profiles across the 29 Master Merchants, including category, subcategory, average_ticket size, operating hours, geolocation coordinates, and historical_fraud_rate baselines.
• Transaction: The central transactional entity recording transaction_id, monetary amount, currency, timestamp, device_id, geolocation region, model-derived fraud_probability, deterministic risk_score, risk_level, status, and ground-truth is_fraud labels. Maintains foreign key links to Customer and Merchant.
• TransactionApproval: Manages the lifecycle of step-up verification challenges, storing payment_id, customer_id, challenge_type (SMS_OTP), verification_token (cryptographic OTP hash), risk_score, approval status (PENDING, APPROVED, REJECTED), and expiration timestamps.
• Investigation: Represents forensic case dockets opened for high-risk or flagged review transactions, tracking case_id, transaction_id, assigned investigator_id, case status (open, under_review, closed), formal decision, and investigative notes.
• ShapExplanation: Stores exact local feature attributions, recording transaction_id, model_version, base_value, feature_names_json, feature_values_json, and shap_values_json.

5.3 USE CASE DIAGRAM

Figure 5.3 delineates the functional interactions between external human actors and the FraudLens AI system:

• Cardholder / Customer Actor:
  - Submits pre-authorization payment intents through the interactive payment portal.
  - Receives simulated mobile SMS notifications containing cryptographic 6-digit OTP codes.
  - Submits OTP tokens through the step-up verification modal to authorize held transactions.
  - Accesses personal account ledgers and transaction history under strict tenant isolation.
• Fraud Investigator Actor:
  - Monitors real-time transaction telemetry and streaming fraud radars.
  - Inspects flagged transactions, reviewing local TreeSHAP waterfall charts and feature attributions.
  - Interacts with the AI Forensic Copilot (Gemini / Grok) to generate case dossiers and attack kill-chains.
  - Adjudicates pending investigation cases, recording formal decisions (confirm fraud, dismiss, escalate).
  - Drafts and exports regulatory Suspicious Activity Reports (SAR) for compliance filing.
• Security Administrator Actor:
  - Manages user accounts, assigns security roles, and controls RBAC permissions.
  - Audits dataset schema integrity, verifying absence of synthetic target leakage.
  - Conducts Model Lab tournament evaluations, comparing model metrics and promoting champion models.
  - Reviews immutable system audit logs to verify administrative and operational compliance.

5.4 FLOW DIAGRAM

The sequential procedural logic executed during payment authorization is illustrated in the System Flow Diagram in Figure 5.4:
1. Transaction Initiation: The client submits a payment request containing amount, merchant, device, and channel parameters.
2. Idempotency & Balance Verification: The system verifies request fingerprints to prevent duplicate processing and validates that available wallet balance >= transaction amount.
3. Feature Engineering & Preprocessing: Derives spending ratios, historical deviations, velocity counters, and cyclical temporal projections, fitting the 63-feature matrix.
4. Model Inference & SHAP Attribution: The active XGBoost champion model computes continuous fraud probability ($p$), while TreeSHAP computes exact local attributions.
5. Deterministic Risk Scoring: Evaluates the 5 additive scoring dimensions, yielding an integer score [0, 100].
6. Three-Tier Gatekeeper Decision:
   • IF Risk Score > 70 OR Hard Block Rule Triggered: Decision = BLOCK. Balance is frozen; transaction is halted; investigation case is opened.
   • ELSE IF Risk Score >= 31 OR Rapid Transaction Activity Triggered: Decision = REVIEW. Transaction is held; 6-digit SMS OTP is generated; phone modal is presented.
   • ELSE: Decision = ALLOW. Frictionless authorization; wallet balance is deducted; transaction is marked SUCCEEDED.
7. Cardholder OTP Response (for REVIEW):
   • IF Valid Token Submitted Within 15 Mins: Status updates to AUTHORIZED; balance is deducted; ledger is committed.
   • ELSE (Mismatch or Rejection): Account is locked; balance is preserved; forensic case is escalated.

5.5 SEQUENCE DIAGRAM

Figure 5.5 presents the UML Sequence Diagram tracing the synchronous and asynchronous messaging exchanges across system components during a pre-authorization step-up challenge:
• The Cardholder client submits a payment intent to FastAPI Gateway (1).
• The Gateway delegates the request to RiskDecisionOrchestrator (2).
• The Orchestrator queries Database/Ledger for customer balance, KYC tenure, and recent transaction velocity (3-4).
• The Orchestrator passes normalized inputs to ML & SHAP Core, which returns fraud probability ($p = 0.58$) and TreeSHAP attributions within 1.1ms (5-6).
• The Orchestrator evaluates deterministic rules and computes a multi-factor risk score of 58/100 (MEDIUM RISK) (7).
• The Orchestrator writes a PENDING_APPROVAL record and opens an Investigation case in Database (8).
• The Orchestrator returns a REVIEW decision payload to the Gateway, which returns HTTP 200 with verification_required = True (9-10).
• The client displays the realistic phone modal, and the cardholder submits the 6-digit OTP (11).
• The Gateway passes the token to Orchestrator, which validates the cryptographic hash, deducts the simulated wallet balance, and updates status to AUTHORIZED (12-13).

5.6 DATABASE DESIGN

The relational persistence tier of FraudLens AI is implemented on an optimized relational database schema comprising 20 specialized tables designed to support high-throughput transactional logging, state transitions, explainability caching, and forensic investigation tracking.

5.6.1 Table Design
Table 5.1 details the schema specifications, column definitions, data types, primary/foreign key constraints, and operational descriptions for the primary entities in FraudLens AI.

5.6.2 Entity-Relationship (ER) Diagram
Figure 5.6 illustrates the comprehensive Entity-Relationship Diagram for FraudLens AI, delineating primary-to-foreign key relationships, indexing strategies, and relational cardinalities between USERS, CUSTOMERS, MERCHANTS, TRANSACTIONS, INVESTIGATIONS, TRANSACTION_APPROVALS, SHAP_EXPLANATIONS, AUDIT_LOGS, and ALERTS.

5.6.3 Data Flow Diagrams
The functional data transformation pathways within FraudLens AI are represented through multi-level Data Flow Diagrams:
• DFD Level 0 (Context Diagram - Figure 5.7): Depicts the high-level boundary interactions between external entities (Cardholder, Merchant Terminal, Fraud Investigator, Security Administrator, Mobile SMS Gateway) and the central 0.0 FraudLens AI System Core.
• DFD Level 1 (Process Decomposition - Figure 5.8): Decomposes system operations into six constituent processes: Process 1.0 (Idempotency & Balance Verification), Process 2.0 (Behavioral Profiling & Feature Pipeline), Process 3.0 (ML Inference & TreeSHAP Attribution), Process 4.0 (Multi-Factor Risk Assessment), Process 5.0 (Pre-Authorization Gatekeeper & Approval Lifecycle), and Process 6.0 (Case Creation & GenAI Forensic Copilot), detailing interactions with data stores D1 through D6.
"""
''')

print("Appended Chapter 5: System Design successfully.")
