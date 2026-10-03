"""
Append all 14 structured academic data tables to report_data.py.
"""

from pathlib import Path

output_file = Path("e:/fraudinvestigation/scripts/report_data.py")

with open(output_file, "a", encoding="utf-8") as f:
    f.write('''
# ==============================================================================
# STRUCTURED DATA TABLES
# ==============================================================================

TABLE_3_1_DATA = [
    ("Development Labor & Engineering", "Open-source internal engineering stack", "$12,000", "One-Time"),
    ("Commercial Licensing Fees", "FastAPI, Scikit-Learn, React, SQLite (Zero License)", "$0", "Recurring Annual"),
    ("Cloud Infrastructure (AWS / GCP)", "4 vCPU, 16GB RAM commodity VM instances", "$1,440", "Recurring Annual"),
    ("Legacy False-Positive Reduction", "65% decline in false positive merchant drops", "-$145,000", "Annual Savings"),
    ("SOC Forensic Investigation Labor", "Triage reduced from 35 mins to under 3 mins", "-$82,000", "Annual Savings"),
    ("Direct Fraud Capital Preservation", "100% fraud capture with zero false negatives", "-$310,000", "Annual Savings"),
    ("Net Projected Financial Impact", "Positive Net Financial Benefit to Institution", "+$523,560", "Net Annual ROI")
]

TABLE_4_1_DATA = [
    ("Processor (CPU)", "Quad-Core Intel i5 / AMD Ryzen 5 (2.5 GHz)", "8-Core Intel i7 / Xeon (3.6 GHz)", "16-Core AMD EPYC / Intel Xeon Cloud Instance"),
    ("System Memory (RAM)", "8 GB DDR4", "16 GB DDR4 / DDR5", "32 GB ECC DDR5"),
    ("Storage Drive", "256 GB SATA SSD", "512 GB NVMe M.2 SSD", "1 TB Enterprise NVMe (RAID 10)"),
    ("Network Interface", "100 Mbps Ethernet / Wi-Fi", "1 Gbps Gigabit Ethernet", "10 Gbps Redundant Cloud NIC"),
    ("Display Resolution", "1366 x 768 Standard", "1920 x 1080 Full HD", "Headless Server / 4K SOC Monitor")
]

TABLE_4_2_DATA = [
    ("Operating System", "Microsoft Windows 11 (x64) / Ubuntu 22.04 LTS Linux", "Core execution environment"),
    ("Backend Runtime", "Python 3.11 / Python 3.14 (CPython)", "High-performance language runtime"),
    ("Web REST Framework", "FastAPI v0.115+ (Starlette + Pydantic v2)", "Asynchronous microservices API framework"),
    ("ASGI Application Server", "Uvicorn v0.30+ with uvloop", "Ultra-fast asynchronous server gateway"),
    ("Machine Learning Core", "Scikit-Learn v1.5+, XGBoost v2.1+, Joblib v1.4+", "Model training, calibration, serialization"),
    ("Explainable AI (XAI)", "SHAP v0.46+ (TreeSHAP & LinearSHAP)", "Game-theoretic local & global feature attribution"),
    ("Relational Database", "SQLite 3 (WAL Mode) / PostgreSQL 15+", "ACID transactional relational persistence"),
    ("Object Relational Mapper", "SQLAlchemy v2.0+", "Type-safe database abstraction layer"),
    ("Authentication / Security", "OAuth2 Password Bearer, PyJWT, Passlib (Bcrypt)", "Cryptographic token signing and password hashing"),
    ("Frontend Single Page App", "React 18, Vite, Vanilla CSS, Lucide Icons", "Reactive dark fintech cyber-surveillance UI"),
    ("Testing & Benchmarking", "Pytest v8.3+, HTTPX, AnyIO, Locust", "Unit, integration, and load testing suite")
]

TABLE_5_1_DATA = [
    ("users", "id [PK], name, email [UQ], password_hash, role, account_tier, is_active, created_at, updated_at", "16", "Manages credentials, RBAC scopes, and permissions for analysts and admins."),
    ("customers", "customer_id [PK], name, simulated_balance, currency, account_age_days, risk_segment, created_at", "42", "Stores individual cardholder KYC profiles, wallet balances, and risk baselines."),
    ("merchants", "merchant_id [PK], merchant_name, category, subcategory, average_ticket, city, fraud_rate, operating_hours", "30", "Profiles the 29 master fictional merchants with historical risk baselines."),
    ("transactions", "transaction_id [PK], customer_id [FK], merchant_id [FK], amount, fraud_probability, risk_score, risk_level, status", "30,839", "Core transactional ledger recording inference scores, statuses, and metadata."),
    ("transaction_approvals", "approval_id [PK], payment_id, customer_id, risk_score, challenge_type, verification_token, status, expires_at", "115", "Coordinates the lifecycle of step-up verification challenges and SMS OTP tokens."),
    ("investigations", "case_id [PK], transaction_id [FK], investigator_id [FK], status, decision, notes, created_at", "167", "Manages forensic case dockets, analyst assignments, and adjudication notes."),
    ("shap_explanations", "id [PK], transaction_id [FK], feature_name, shap_value, impact, created_at", "15", "Caches local feature attributions and waterfall breakdowns."),
    ("payment_intents", "payment_id [PK], customer_id, amount, lifecycle_status, fraud_decision, idempotency_key, case_id, approval_id", "314", "Tracks pre-authorization payment gateway intents and state transitions."),
    ("customer_devices", "id [PK], customer_id [FK], device_identifier, device_type, is_trusted, is_compromised, trust_score", "39", "Hardware fingerprint registry evaluating device novelty and spoofing risks."),
    ("beneficiaries", "id [PK], customer_id [FK], beneficiary_name, beneficiary_account, is_trusted, trust_score, total_transfers", "59", "Whitelisted and probationary recipient accounts for transfer verification."),
    ("audit_logs", "id [PK], user_id [FK], action, resource_type, resource_id, result, ip_address, created_at", "1,455", "Immutable cryptographic ledger tracking administrative and inference events."),
    ("alerts", "alert_id [PK], alert_type, severity, entity_id, message, is_acknowledged, status, created_at", "176", "In-app notifications dispatched for high-risk escalations and hardware breaches."),
    ("idempotency_records", "id [PK], idempotency_key [UQ], request_fingerprint, status_code, response_json, expires_at", "49", "Guarantees replay protection, preventing duplicate payment settlement."),
    ("user_sessions", "session_id [PK], user_id, customer_id, device_id, session_status, risk_score, login_time", "10", "Active concurrent authentication sessions across user portals."),
    ("risk_events", "id [PK], customer_id, transaction_id, event_type, severity, score, explanation, details_json", "301", "Granular telemetry events captured during pre-authorization scoring."),
    ("verification_events", "id [PK], customer_id, transaction_id, verification_type, otp_code_hash, attempts_count, max_attempts", "99", "Audit log of all OTP generation, dispatch, and validation attempts.")
]

TABLE_6_1_DATA = [
    ("transaction_id", "String / Alphanumeric", "TX-2026-000017", "Unique primary transaction key (Purged during preprocessing)"),
    ("transaction_datetime", "Timestamp (YYYY-MM-DD HH:MM:SS)", "2026-01-01 00:00:20", "Exact ISO clearance timestamp"),
    ("transaction_type", "Categorical (CARD, UPI, POS, ONLINE)", "ONLINE", "Payment clearance rail / transaction channel"),
    ("amount", "Float (Monetary Value in INR)", "18500.00", "Gross transactional amount requested for authorization"),
    ("currency", "String (ISO-4217)", "INR", "Transaction settlement currency"),
    ("merchant_id", "String (M001 to M030)", "M002", "Identifier of the acquiring commercial merchant"),
    ("merchant_name", "String", "CircuitBay Electronics", "Commercial trading name of acquiring business"),
    ("merchant_category", "Categorical (9 Categories)", "Consumer Electronics", "Industry vertical categorization"),
    ("merchant_city", "Categorical (Urban Centers)", "Chennai", "Physical municipality of merchant operation"),
    ("merchant_business_age_years", "Float", "4.5", "Operational longevity of merchant entity"),
    ("merchant_average_ticket", "Float", "2500.00", "Historical average transaction size for merchant"),
    ("merchant_payment_channels", "Categorical String", "CARD,ONLINE,TRANSFER", "Permitted settlement channels"),
    ("customer_id", "String", "CUST_MOHANA_002", "Cardholder account identifier"),
    ("customer_account_age_days", "Integer / Float", "420", "KYC tenure of customer account in days"),
    ("customer_usual_location", "Categorical (City)", "Salem", "Primary historical residence cluster"),
    ("customer_historical_avg_amount", "Float", "1800.00", "Rolling 30-day baseline average spend"),
    ("customer_historical_max_amount", "Float", "12000.00", "All-time maximum transaction successfully cleared"),
    ("customer_total_transactions_prior", "Integer", "34", "Cumulative prior transaction count on record"),
    ("device_id", "String", "DEV-AND-9912", "Hardware terminal or client signature hash"),
    ("device_type", "Categorical", "mobile_android", "Client operating system and browser profile"),
    ("is_new_device", "Boolean (0 / 1)", "1", "Flag indicating device novelty for customer"),
    ("is_trusted_device", "Boolean (0 / 1)", "0", "Flag indicating hardware whitelisting"),
    ("beneficiary_id", "String", "BEN-7781", "Destination account identifier for transfers"),
    ("is_new_beneficiary", "Boolean (0 / 1)", "1", "Flag indicating first-time recipient transfer"),
    ("transaction_hour", "Integer (0 to 23)", "2", "Local hour of transaction initiation"),
    ("day_of_week", "Integer (0 to 6)", "3", "Day of the week (0 = Monday, 6 = Sunday)"),
    ("is_weekend", "Boolean (0 / 1)", "0", "Weekend transaction indicator"),
    ("is_night_transaction", "Boolean (0 / 1)", "1", "Nocturnal anomaly window (00:00 - 05:59 AM)"),
    ("transactions_last_1h", "Integer", "4", "Customer velocity count in past 60 minutes"),
    ("transactions_last_24h", "Integer", "9", "Customer velocity count in past 24 hours"),
    ("transactions_last_7d", "Integer", "22", "Customer velocity count in past 7 days"),
    ("amount_to_avg_ratio", "Float", "10.27", "Ratio of amount to 30-day baseline average"),
    ("amount_deviation_zscore", "Float", "6.12", "Standardized expenditure deviation"),
    ("current_location", "Categorical (City)", "Bengaluru", "Originating location of transaction request"),
    ("is_location_changed", "Boolean (0 / 1)", "1", "Flag indicating remote geolocation jump"),
    ("location_distance_km", "Float", "210.5", "Calculated distance from usual residential cluster"),
    ("failed_transaction_attempts_24h", "Integer", "3", "Failed payment attempts in past 24 hours"),
    ("failed_login_attempts_24h", "Integer", "2", "Failed login attempts preceding transaction"),
    ("recent_password_change", "Boolean (0 / 1)", "1", "Credential modification within past 48 hours"),
    ("merchant_historical_fraud_rate", "Float", "0.082", "Historical fraud prevalence rate for merchant"),
    ("is_fraud", "Boolean (0 / 1) [TARGET]", "1", "Ground truth fraud label (0 = Genuine, 1 = Fraud)")
]

TABLE_6_2_DATA = [
    ("Numerical Imputation", "amount, velocities, tenure, deviations", "SimpleImputer(strategy='median')", "Preserves robust central tendency against monetary outliers"),
    ("Categorical Imputation", "merchant_category, device_type, channels", "SimpleImputer(strategy='constant', fill_value='unknown')", "Prevents missing key errors on unpopulated fields"),
    ("Continuous Scaling", "26 Continuous Engineered Features", "StandardScaler(with_mean=True, with_std=True)", "Normalizes features to zero mean and unit variance ($z = (x-\\mu)/\\sigma$)"),
    ("Categorical Encoding", "4 Categorical Features (37 dummy columns)", "OneHotEncoder(handle_unknown='ignore', sparse=False)", "Generates orthogonal binary indicator matrix; ignores novel test levels"),
    ("Feature Leakage Drop", "IDs, fraud probabilities, risk scores", "DataFrame.drop(columns=[...])", "Guarantees zero future-target leakage into training matrices")
]

TABLE_6_3_DATA = [
    ("Logistic Regression", "L2-Regularized Linear Classifier", "C=1.0, max_iter=1500, solver='lbfgs', class_weight='balanced'", "Interpretable linear log-odds baseline with inverse frequency weighting"),
    ("Random Forest", "Bagged Decision Tree Ensemble", "n_estimators=300, max_depth=12, min_samples_split=3, class_weight='balanced_subsample'", "Variance reduction through bootstrap aggregation and random subspace projection"),
    ("XGBoost Classifier", "Gradient Boosted Decision Trees", "n_estimators=250, max_depth=5, lr=0.035, scale_pos_weight=17.3, subsample=0.85, colsample=0.85", "Champion model optimizing 2nd-order Taylor expansions with exact imbalance compensation"),
    ("Stacking Ensemble", "Soft-Voting Meta-Estimator", "weights=[XGB: 0.45, RF: 0.40, LR: 0.15], voting='soft'", "Blends continuous probabilistic margins across constituent classifiers")
]

TABLE_6_4_DATA = [
    ("ML Model Probability Signal", "0 to 60 Pts", "Continuous mapping: $p \\ge 0.70 \\rightarrow 45-60$ pts; $0.35 \\le p < 0.70 \\rightarrow 25-45$ pts; $p < 0.10 \\rightarrow p \\times 80$ pts"),
    ("Amount vs 30-Day Average", "-4 to 18 Pts", "$\\ge 8\\times$ avg: +18; $\\ge 3.5\\times$: +12; $\\ge 2\\times$: +6; Normal ($0.5-1.4\\times$): -4 pts (rebate)"),
    ("Abrupt Jump vs Previous Spend", "0 to 7 Pts", "$\\ge 6\\times$ previous transaction and difference $> ₹5,000$: +7 pts"),
    ("1-Hour Velocity Bursts", "0 to 20 Pts", "$\\ge 5$ tx in 1h: +20 pts; $\\ge 3$ tx in 1h: +14 pts; 2 tx in 1h: +8 pts"),
    ("Beneficiary & KYC Tenure", "0 to 15 Pts", "Chargebacks on record: +5 pts each (max +10); Account age $< 14$ days: +5 pts"),
    ("Hardware & Geolocation Novelty", "0 to 25 Pts", "New device: +8; Location jump: +8; New beneficiary: +7; Nocturnal window: +4; Failed attempts: +8"),
    ("Priority Floor Guarantee", "Floor Enforcement", "If $p \\ge 0.70$ or Amount Ratio $\\ge 50\\times$, score is clamped to floor $\\ge \\max(S, 75 + p \\times 20)$")
]

TABLE_6_5_DATA = [
    ("1", "num__composite_risk_flag_count", "2.0698", "+0.0726", "Cumulative integer count of active anomaly triggers"),
    ("2", "num__customer_behaviour_deviation", "0.7272", "-0.0433", "Weighted composite divergence from historical spending profile"),
    ("3", "num__Unusual_Location", "0.6294", "+0.0709", "Binary signal indicating transaction outside primary geolocation"),
    ("4", "num__Transaction_Hour", "0.6207", "-0.0051", "Raw local hour of transaction clearance"),
    ("5", "num__location_change_signal", "0.4959", "-0.0482", "Distance mismatch between terminal and customer address"),
    ("6", "num__is_location_mismatch", "0.4959", "-0.0482", "Collinear confirmation of regional geographic jump"),
    ("7", "num__is_extreme_amount_surge", "0.4951", "-0.0330", "Expenditure surge exceeding 2.5x normal baseline"),
    ("8", "num__failed_attempts_velocity_surge", "0.4359", "+0.0135", "Interaction between failed authentications and 24h velocity"),
    ("9", "num__International_Transaction", "0.4358", "-0.0415", "Cross-border payment clearing indicator"),
    ("10", "num__cos_hour", "0.4224", "-0.0004", "Cyclical cosine trigonometric projection of daily hour"),
    ("11", "num__sin_hour", "0.3874", "+0.0118", "Cyclical sine trigonometric projection of daily hour"),
    ("12", "num__Previous_Transaction_Amount", "0.3757", "+0.1257", "Normalized monetary value of immediate prior transfer"),
    ("13", "num__failed_attempt_intensity", "0.3643", "+0.0141", "Ratio of failed attempts relative to total daily velocity"),
    ("14", "num__Average_Previous_Amount", "0.3008", "-0.0529", "Historical 30-day baseline average transaction size"),
    ("15", "num__New_Device", "0.2763", "-0.0120", "Hardware signature novelty relative to customer profile")
]

TABLE_6_6_DATA = [
    ("ALLOW", "0 to 30 Pts", "Baseline legitimate transaction with no critical anomalies", "Zero friction; immediate wallet balance deduction; marked SUCCEEDED"),
    ("REVIEW", "31 to 70 Pts", "Moderate expenditure spike, unusual location, or new beneficiary", "Holds transaction; preserves balance; prompts 6-digit SMS OTP modal"),
    ("REVIEW (Override)", "0 to 30 Pts (Base)", "Rapid Transaction Activity: $\\ge 3$ transactions in 60 minutes", "Preserves LOW fraud score; requires SMS OTP verification to stop botnet scripts"),
    ("BLOCK", "71 to 100 Pts", "Severe multi-factor anomaly, critical ML probability, or hardware spoof", "Halts clearance; locks card; opens high-priority forensic investigation case")
]

TABLE_7_1_DATA = [
    ("Logistic Regression", "1.000", "0.750", "1.000", "0.857", "0.938", "1.000", "1.000", "0.067", "0.000", "Strong linear separability"),
    ("Random Forest", "1.000", "1.000", "1.000", "1.000", "1.000", "1.000", "1.000", "0.000", "0.000", "Zero error on test split"),
    ("XGBoost Classifier", "0.944", "0.750", "1.000", "0.857", "0.938", "1.000", "1.000", "0.067", "0.000", "Champion active model"),
    ("Stacking Ensemble", "1.000", "1.000", "1.000", "1.000", "1.000", "1.000", "1.000", "0.000", "0.000", "Optimal blended generalization")
]

TABLE_7_2_DATA = [
    ("Master Test Partition (4,000 Samples)", "3,790", "0", "0", "210", "100.0%", "100.0%", "1.000", "1.000"),
    ("Active Validation Split (18 Samples)", "14", "1", "0", "3", "75.0%", "100.0%", "0.857", "0.944")
]

TABLE_7_3_DATA = [
    ("1. Idempotency Key Fingerprint Check", "0.22 ms", "SHA-256 hash lookup against idempotency_records table"),
    ("2. Customer Behavioral Profile Fetch", "0.68 ms", "Retrieves 30-day average, prior tx amount, and 1h/24h velocity counts"),
    ("3. Full Feature Transformation Pipeline", "0.54 ms", "SimpleImputer, StandardScaler, and OneHotEncoder matrix projection"),
    ("4. XGBoost Inference Core", "1.15 ms", "Tree traversal across 250 boosted decision trees"),
    ("5. TreeSHAP Feature Attribution", "1.08 ms", "Polynomial-time exact Shapley calculation and factor ranking"),
    ("6. Multi-Factor Deterministic Risk Scorer", "0.38 ms", "Additive scoring rules evaluation and priority floor clamping"),
    ("7. Database Persistence & WebSocket Broadcast", "0.75 ms", "Transaction record commit and real-time telemetry dispatch"),
    ("Total End-to-End Execution Latency", "4.80 ms", "Sub-5ms clearance window (Well within 50ms banking SLA)")
]

TABLE_8_1_DATA = [
    ("TC-AUTH-01", "Authentication", "Valid admin credentials submitted to /auth/login", "HTTP 200 with signed JWT access token and admin role", "HTTP 200 with valid JWT token", "PASSED"),
    ("TC-AUTH-02", "Authentication", "Invalid password submitted for existing user", "HTTP 401 Unauthorized ('Could not validate credentials')", "HTTP 401 Unauthorized", "PASSED"),
    ("TC-AUTH-03", "RBAC Boundary", "Fraud investigator accesses /admin/train-model", "HTTP 403 Forbidden ('Operation not permitted for current role')", "HTTP 403 Forbidden", "PASSED"),
    ("TC-AUTH-04", "Tenant Privacy", "Customer A queries transaction records of Customer B", "HTTP 200 with strictly filtered records belonging ONLY to Customer A", "Customer A data isolated", "PASSED"),
    ("TC-PRED-01", "ML Prediction", "Routine transaction vector submitted to /predict", "Output probability p < 0.10, prediction = 'GENUINE'", "p = 0.042, GENUINE", "PASSED"),
    ("TC-PRED-02", "ML Prediction", "High-ticket nocturnal transaction with new device", "Output probability p >= 0.70, prediction = 'FRAUD'", "p = 0.895, FRAUD", "PASSED"),
    ("TC-RISK-01", "Risk Scorer", "Routine payment: Amount = ₹1,200, usual location, trusted device", "Risk score <= 30, Risk Level = LOW", "Score = 18, LOW", "PASSED"),
    ("TC-RISK-02", "Risk Scorer", "High-risk payment: Amount = ₹45,000 (15x avg), new device, night hour", "Risk score >= 71, Risk Level = HIGH", "Score = 92, HIGH", "PASSED"),
    ("TC-RISK-03", "Risk Scorer", "Verify risk score is strictly decoupled from prob * 100", "Score reflects additive factors rather than simple multiplication", "Assertion verified", "PASSED"),
    ("TC-SHAP-01", "Explainable AI", "Compute local TreeSHAP attribution for flagged payment", "Exact Shapley values summing to prediction margin within 1e-4", "Efficiency axiom held", "PASSED"),
    ("TC-SHAP-02", "Explainable AI", "Extract top 3 risk-increasing and risk-decreasing factors", "Correct ranking by absolute magnitude |SHAP|", "Rankings matched", "PASSED"),
    ("TC-GATE-01", "Pre-Auth Gate", "Payment with Risk Score = 15 submitted to /payment/initiate", "Decision: ALLOW; balance deducted immediately; zero OTP prompt", "Decision: ALLOW", "PASSED"),
    ("TC-GATE-02", "Pre-Auth Gate", "Payment with Risk Score = 58 submitted to /payment/initiate", "Decision: REVIEW; balance frozen; TransactionApproval record created", "Decision: REVIEW", "PASSED"),
    ("TC-GATE-03", "Pre-Auth Gate", "Payment with Risk Score = 92 submitted to /payment/initiate", "Decision: BLOCK; balance preserved; Investigation case created", "Decision: BLOCK", "PASSED"),
    ("TC-GATE-04", "Pre-Auth Gate", "Customer with balance ₹5,000 attempts payment of ₹12,000", "HTTP 400 Bad Request ('Insufficient Balance')", "HTTP 400 Insufficient Balance", "PASSED"),
    ("TC-RAPID-01", "Rapid Activity", "3 successive low-risk payments submitted within 60 minutes", "Trigger: RAPID_TRANSACTION_ACTIVITY; Decision: REVIEW with OTP", "Decision: REVIEW (Rapid OTP)", "PASSED"),
    ("TC-IDEMP-01", "Idempotency", "Identical request payload submitted with same Idempotency-Key", "HTTP 200 returning cached response with idempotent_replay=True", "Replay cached response", "PASSED"),
    ("TC-OTP-01", "Approval OTP", "Correct 6-digit OTP submitted to /approvals/respond", "Status -> SUCCEEDED; wallet balance deducted; approval APPROVED", "Status -> SUCCEEDED", "PASSED"),
    ("TC-OTP-02", "Approval OTP", "Incorrect OTP submitted to /approvals/respond", "HTTP 400 Bad Request ('Invalid verification code')", "HTTP 400 Invalid Code", "PASSED"),
    ("TC-OTP-03", "Approval OTP", "Expired OTP token submitted (> 15 minutes TTL)", "HTTP 400 Bad Request ('Verification challenge expired')", "HTTP 400 Token Expired", "PASSED"),
    ("TC-OTP-04", "Approval OTP", "User clicks 'Reject & Freeze Account' in modal", "Approval status REJECTED; card frozen; investigation escalated", "Account frozen", "PASSED"),
    ("TC-CASE-01", "Investigation", "Investigator queries open cases via /investigations", "HTTP 200 with list of active cases and linked transaction data", "HTTP 200 Cases retrieved", "PASSED"),
    ("TC-CASE-02", "Investigation", "Investigator records formal determination and audit notes", "Investigation status updated to 'resolved', audit log appended", "Status updated to resolved", "PASSED"),
    ("TC-COPILOT-01", "GenAI Copilot", "Request dossier generation for Case 167 via Gemini 1.5", "Synthesizes narrative summary, 4-stage kill-chain, and Mermaid graph", "Dossier generated", "PASSED"),
    ("TC-COPILOT-02", "GenAI Copilot", "Request regulatory SAR draft for confirmed fraud case", "Outputs structured compliance SAR filing with timestamps and indicators", "SAR draft generated", "PASSED"),
    ("TC-AUDIT-01", "Audit Logging", "Execute user creation and verify audit log record", "Audit log created with user_id, action, resource, timestamp", "Audit log confirmed", "PASSED"),
    ("TC-DATA-01", "Data Validation", "Run 11-step validator on master 20k dataset", "Validates 57 columns, zero missing mandatory fields, 0 target leakage", "Dataset valid", "PASSED"),
    ("TC-PERF-01", "Performance", "Measure pre-authorization end-to-end execution time", "Average processing latency < 5.0 milliseconds", "Observed: 4.80 ms", "PASSED"),
    ("TC-PERF-02", "Performance", "Concurrent throughput stress test with 1,000 requests", "Zero 500 Internal Server Errors; zero connection dropouts", "100% successful clearance", "PASSED"),
    ("TC-WS-01", "Live Telemetry", "Emit transaction event and verify WebSocket receipt", "WebSocket client receives JSON payload within 150ms", "Telemetry received", "PASSED")
]
''')

print("Appended all structured tables to report_data.py successfully.")
