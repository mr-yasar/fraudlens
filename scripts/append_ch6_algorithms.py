"""
Append Chapter 6: Proposed Algorithm Implementation to report_data.py.
"""

from pathlib import Path

output_file = Path("e:/fraudinvestigation/scripts/report_data.py")

with open(output_file, "a", encoding="utf-8") as f:
    f.write('''
# ==============================================================================
# CHAPTER 6: PROPOSED ALGORITHM IMPLEMENTATION
# ==============================================================================

CH6_TEXT = """
6.1 PROJECT DESCRIPTION

FraudLens AI is an end-to-end, explainable artificial intelligence (XAI) financial fraud detection, risk intelligence, and autonomous case investigation platform engineered specifically for high-throughput digital payment networks. The system bridges the critical operational divide between high-accuracy non-linear machine learning, deterministic multi-factor risk assessment, mathematical explainability, and rapid forensic investigation triage.

6.1.1 Dataset Specification & Integrity Audit
The foundational empirical evaluation of FraudLens AI is conducted on the master transaction corpus: `fraudlens_master_synthetic_transactions_29_merchants.csv`. The dataset comprises exactly 20,000 transaction instances structured across 57 distinct behavioral, spatial, temporal, and merchant attributes. It models the transactional ecosystem of 30 heterogeneous commercial merchants situated across key urban centers in Tamil Nadu and Karnataka (including Chennai, Coimbatore, Madurai, Salem, and Bengaluru).

Key structural properties of the dataset include:
• Total Transaction Records: 20,000 rows.
• Ground-Truth Target Variable: `is_fraud` (binary indicator where 0 denotes legitimate commercial settlement and 1 denotes confirmed fraudulent exfiltration).
• Class Imbalance Ratio: The dataset reflects an authentic real-world fraud prevalence rate of 5.46% (1,092 fraudulent instances against 18,908 legitimate transactions), representing an acute class imbalance ratio of approximately 1:17.3.
• Merchant Entity Representation: 30 distinct commercial establishments spanning diverse categories: Grocery & Supermarkets (e.g., NovaMart Fresh), Consumer Electronics (e.g., CircuitBay Electronics), Mobile Stores (e.g., Pulse Mobile Hub), Jewellery & Bullion (e.g., Aurelia Gold House), Fashion & Apparel (e.g., UrbanThread Studio), Pharmacies (e.g., MedicoCare Pharmacy), Restaurants & Cafes, Fuel Stations, and Hospitality.
• Fictional Fraud Typologies: Fraud scenarios represented include Account Takeover (ATO) botnet injection, Card-Not-Present (CNP) basket velocity surges, nocturnal brute-force credential stuffing, cross-border remittance anomalies, and high-ticket bullion exfiltration.

Table 6.1 delineates the complete attribute specification across all 57 raw and engineered dimensions.

6.1.2 Preprocessing, Imputation & Feature Scaling
To ensure deterministic execution and prevent data leakage, FraudLens AI encapsulates all transformation logic within a Scikit-Learn compatible `FullFraudPreprocessor` pipeline. The preprocessing methodology comprises four sequential stages (summarized in Table 6.2):
1. Target Leakage & Identifier Removal:
   The pipeline systematically purges unique identifier keys (`transaction_id`, `customer_id`, `device_id`, `beneficiary_id`) to prevent classifier memorization. Furthermore, all downstream target proxies (such as `Fraud_Probability`, `Risk_Score`, `Risk_Level`, and `customer_risk_score`) are explicitly dropped.
2. Missing-Value Imputation:
   Numerical feature missingness is resolved using median imputation (`SimpleImputer(strategy="median")`), preserving robustness against extreme monetary outliers. Categorical missingness is handled using constant imputation (`SimpleImputer(strategy="constant", fill_value="unknown")`).
3. Continuous Feature Scaling:
   Numerical variables are standardized using `StandardScaler`, centering features to zero mean and unit variance ($z = (x - \mu) / \sigma$). This guarantees optimal convergence for gradient descent and regularized linear baselines.
4. Categorical Feature Encoding:
   Categorical attributes (`merchant_category`, `transaction_type`, `merchant_payment_channels`, `device_type`) are encoded via `OneHotEncoder(handle_unknown="ignore", sparse_output=False)`, expanding categorical cardinality into 37 binary orthogonal indicator columns while preventing runtime errors upon encountering novel categories.

6.1.3 Behavioral Feature Engineering & Interaction Signals
Raw payment parameters alone cannot expose sophisticated fraud patterns. The `FraudFeatureEngineer` derives 26 advanced behavioral and temporal features (Figure 6.1):
1. Spending Baseline Deviation Ratios:
   • $\text{amount\_to\_average\_ratio} = \text{Amount} / (\text{Customer\_Historical\_Avg\_Amount} + \epsilon)$
   • $\text{amount\_deviation\_zscore} = (\text{Amount} - \mu_{\text{customer}}) / (\sigma_{\text{customer}} + \epsilon)$
   • $\text{is\_extreme\_amount\_surge} = \mathbb{I}(\text{amount\_to\_average\_ratio} > 2.5)$
2. Velocity Burst & Acceleration Interactions:
   • $\text{amount\_velocity\_24h\_surge} = \text{Amount} \times (\text{Transactions\_Last\_24H} + 1)$
   • $\text{failed\_attempt\_intensity} = \text{Failed\_Attempts} / (\text{Transactions\_Last\_24H} + 1)$
3. Cyclical Trigonometric Temporal Projections:
   Standard integer hour representations introduce an artificial mathematical discontinuity between 23:59 and 00:00. To preserve cyclical continuity, hours are mapped onto the unit circle:
   • $\sin\_hour = \sin(2\pi \times \text{Hour} / 24.0)$
   • $\cos\_hour = \cos(2\pi \times \text{Hour} / 24.0)$
   • Nocturnal vulnerability indicator: $\text{is\_night\_transaction} = \mathbb{I}(\text{Hour} \in [0, 5])$
4. High-Risk Multi-Factor Composite Signals:
   • $\text{account\_takeover\_risk} = \text{New\_Device} \times \text{Unusual\_Location}$
   • $\text{international\_risk\_signal} = \text{Is\_International} \times (\text{Unusual\_Location} + \text{New\_Device} + 0.5)$
   • $\text{composite\_risk\_flag\_count} = \sum (\text{New\_Device} + \text{Unusual\_Location} + \text{Is\_International} + \text{Night} + \text{Extreme\_Surge} + \text{Failed\_Attempt})$

6.1.4 Stratified Data Splitting & Leakage Auditing
The dataset is partitioned using a stratified 70% / 15% / 15% Train / Validation / Test split. Stratification enforces identical 5.46% fraud prevalence across all partitions. Crucially, the `FullFraudPreprocessor` is fitted **exclusively on the training split** ($X_{\text{train}}$) and subsequently applied to transform $X_{\text{val}}$ and $X_{\text{test}}$, completely eliminating data leakage from test distributions into model training parameters.

6.1.5 Class Imbalance Mitigation Strategy
To overcome the severe 1:17.3 class imbalance:
• In Logistic Regression, inverse frequency weighting is enforced via `class_weight="balanced"`.
• In Random Forest, sub-tree bootstrap re-weighting is applied via `class_weight="balanced_subsample"`.
• In XGBoost, exact negative-to-positive ratio weighting is calibrated via `scale_pos_weight = N_{\text{negative}} / N_{\text{positive}} \approx 17.3$. This penalizes false negatives 17.3 times more heavily than false positives, forcing the boosting algorithm to optimize decision boundaries specifically for rare fraud vectors.

6.1.6 Supervised Machine Learning Architectures
FraudLens AI evaluates three distinct classification algorithms and one meta-ensemble (Table 6.3):
1. Regularized Logistic Regression: Serves as an interpretable linear baseline optimizing the L2-regularized log-loss objective via the L-BFGS solver.
2. Tuned Random Forest Classifier: An ensemble of 300 de-correlated decision trees (max depth 12) utilizing Gini impurity split criteria and bootstrap aggregation to capture non-linear feature interactions without overfitting.
3. Extreme Gradient Boosted Trees (XGBoost): The champion classification architecture, utilizing 250 gradient boosted trees (max depth 5, learning rate $\eta = 0.035$, subsample 0.85, colsample_bytree 0.85). XGBoost optimizes second-order Taylor expansions of the loss function with L1 ($\alpha = 0.1$) and L2 ($\lambda = 1.0$) regularization.
4. Soft-Voting Stacking Ensemble: Combines calibrated probabilistic predictions across constituent estimators using weighted averaging:
   $P_{\text{ensemble}} = 0.45 \times P_{\text{XGBoost}} + 0.40 \times P_{\text{RandomForest}} + 0.15 \times P_{\text{LogisticRegression}}$.

6.1.7 Decoupled Deterministic Multi-Factor Risk Scoring Methodology
A cornerstone innovation of FraudLens AI is the strict mathematical decoupling between model-estimated Fraud Probability ($p \in [0.0, 1.0]$) and an independent Deterministic Operational Risk Score ($S \in [0, 100]$). As illustrated in Figure 6.2 and Table 6.4, the total risk score is an additive composite aggregating five distinct operational dimensions:
$$S = \text{clamp}_{[0, 100]}\left( S_{\text{ML}} + S_{\text{Amount}} + S_{\text{Velocity}} + S_{\text{History}} + S_{\text{Env}} \right)$$

1. Dimension 1: ML Model Baseline Signal ($S_{\text{ML}} \in [0, 60]$ pts):
   • If $p \ge 0.70$: $S_{\text{ML}} = \min(60, 45.0 + (p - 0.70) \times 50.0)$
   • If $0.35 \le p < 0.70$: $S_{\text{ML}} = 25.0 + (p - 0.35) \times (20.0 / 0.35)$
   • If $0.10 \le p < 0.35$: $S_{\text{ML}} = 8.0 + (p - 0.10) \times (17.0 / 0.25)$
   • If $p < 0.10$: $S_{\text{ML}} = p \times 80.0$
2. Dimension 2: Spending Baseline Deviation Signal ($S_{\text{Amount}} \in [-6, 25]$ pts):
   • Severe customer average spike ($\ge 8\times$ baseline): $+18$ pts; ($3.5\times - 8\times$): $+12$ pts; ($2\times - 3.5\times$): $+6$ pts.
   • Normal expenditure consistent with customer history ($0.5\times - 1.4\times$): $-4$ pts (credit rebate).
   • Abrupt jump from immediate previous transaction ($\ge 6\times$ and difference $> ₹5,000$): $+7$ pts.
3. Dimension 3: Transaction Velocity & Burst Acceleration ($S_{\text{Velocity}} \in [0, 20]$ pts):
   • Critical 1-hour burst ($\ge 5$ transactions in 1 hour): $+20$ pts.
   • Elevated 1-hour burst ($3 - 4$ transactions in 1 hour): $+14$ pts.
   • Moderate velocity ($2$ transactions in 1 hour): $+8$ pts.
4. Dimension 4: Beneficiary & History Integrity ($S_{\text{History}} \in [0, 15]$ pts):
   • Historical chargebacks recorded: $+5$ pts per incident (max $+10$ pts).
   • Young account probationary window ($< 14$ days since registration): $+5$ pts.
5. Dimension 5: Environmental & Hardware Novelty ($S_{\text{Env}} \in [0, 25]$ pts):
   • Unrecognized hardware device fingerprint (`is_new_device`): $+8$ pts.
   • Remote geolocation jump / distance $> 50$ km (`is_location_changed`): $+8$ pts.
   • First-time unverified beneficiary transfer (`is_new_beneficiary`): $+7$ pts.
   • Nocturnal anomaly window ($00:00 - 05:59$ AM): $+4$ pts.
   • Preceding failed authentication attempts ($\ge 2$ in 24h): $+8$ pts; ($1$ failed): $+3$ pts.
   • Cross-border international transaction: $+4$ pts.

Priority Override Guarantee: If ML probability indicates critical fraud ($p \ge 0.70$) or amount ratio exceeds $50\times$ baseline, the scoring engine enforces an automatic floor: $S \ge \max(S, \text{round}(75.0 + p \times 20.0))$, ensuring that high-confidence threats are guaranteed to land in the HIGH RISK tier.

Risk Band Classification:
• LOW RISK ($0 \le S \le 30$): Clean baseline; zero friction; frictionless authorization.
• MEDIUM RISK ($31 \le S \le 70$): Elevated anomaly; holds transaction; issues SMS OTP challenge.
• HIGH RISK ($71 \le S \le 100$): Critical danger; halts transaction; opens forensic case docket.

6.1.8 Explainable AI (XAI) via TreeSHAP
To eliminate model opacity, FraudLens AI incorporates TreeSHAP, an exact game-theoretic feature attribution engine grounded in cooperative game theory (Figure 6.3). For any individual prediction $f(x)$, TreeSHAP decomposes the model output into additive attributions:
$$f(x) = \phi_0 + \sum_{i=1}^{M} \phi_i(x)$$
where $\phi_0 = \mathbb{E}[f(z)]$ is the base expected value across the training background dataset, and $\phi_i(x)$ is the Shapley attribution value for feature $i$.

Mathematical Properties Satisfied:
1. Efficiency (Local Accuracy): The sum of feature attributions plus the base value exactly equals the model prediction output.
2. Missingness: Features with zero impact on the tree traversal receive exactly zero attribution ($\phi_i = 0$).
3. Consistency: If a model modification increases the marginal contribution of a feature, its attribution value cannot decrease.

Table 6.5 reports the global top-15 feature importance rankings across the master dataset, confirming that composite risk flag counts, behavioral spending deviations, location mismatches, and nocturnal transaction timing serve as the primary global determinants of fraudulent activity.

6.2 MODULES OVERVIEW

The functional architecture of FraudLens AI is partitioned into 10 cohesive, loosely coupled modules spanning the full software lifecycle from data ingestion to regulatory case closure:
1. Module 1: Data Ingestion & Validation Pipeline
2. Module 2: Machine Learning Prediction Engine
3. Module 3: Multi-Factor Deterministic Risk Scoring Engine
4. Module 4: Explainable AI & SHAP Attribution Subsystem
5. Module 5: Pre-Authorization Decision & Autonomous Orchestration Engine
6. Module 6: Step-Up Security & Realistic Smartphone SMS OTP Verification
7. Module 7: Autonomous Case Management & Investigation Hub
8. Module 8: Interactive Command Center & Streaming Radar Dashboard
9. Module 9: AI Forensic Copilot & Multi-LLM Reasoning Engine
10. Module 10: Security, Multi-Tenant RBAC & Immutable Audit Logging

6.3 MODULE DESCRIPTION

6.3.1 Module 1: Data Ingestion & Preprocessing Module
• Purpose: Ingests raw transaction payloads, executes 11-step schema validation, and cleanses data.
• Processing: Resolves missing values via median/constant imputers, removes identifier leakage, derives behavioral ratios, and encodes categoricals via OneHotEncoder into 63 model-ready inputs.
• Input / Output: Raw transaction dictionary $\rightarrow$ Standardized dense numerical matrix ($1 \times 63$).

6.3.2 Module 2: Machine Learning Prediction Engine
• Purpose: Executes low-latency inference using serialized champion models (.joblib).
• Processing: Passes preprocessed feature vectors through tuned XGBoost / Stacking Ensemble, applying threshold optimization ($T = 0.0637$ for active deployment).
• Input / Output: Transformed feature matrix $\rightarrow$ Continuous Fraud Probability ($p \in [0.0, 1.0]$).

6.3.3 Module 3: Multi-Factor Deterministic Risk Scoring Engine
• Purpose: Computes an objective operational risk score strictly separated from ML probability.
• Processing: Aggregates 5 weighted dimensions (ML baseline, amount spike, velocity, history, novelty) and enforces priority high-risk floor clamping.
• Input / Output: Fraud probability and raw transaction metadata $\rightarrow$ Integer Risk Score ($0-100$) and Risk Level (LOW, MEDIUM, HIGH).

6.3.4 Module 4: Explainable AI (TreeSHAP & LinearSHAP Attribution)
• Purpose: Decomposes model predictions into interpretable local feature contributions.
• Processing: Executes TreeSHAP polynomial tree traversal, sorting attributions into top risk-increasing and risk-decreasing factors.
• Input / Output: Transformed vector $\rightarrow$ Local waterfall attributions and plain-language evidence narrative.

6.3.5 Module 5: Pre-Authorization Decision & Autonomous Orchestrator
• Purpose: Acts as the authoritative gatekeeper for digital payment clearance.
• Processing: Enforces idempotency checks, verifies wallet balance, evaluates rule heuristics, and dispatches decisions: ALLOW (0-30), REVIEW (31-70), or BLOCK (71-100).
• Input / Output: Payment initiation request $\rightarrow$ Decision result (ALLOW, REVIEW, BLOCK) with operational directives.

6.3.6 Module 6: Step-Up Security & Mobile Phone OTP Verification Module
• Purpose: Provides adaptive challenge-response authentication for held review transactions.
• Processing: Generates 6-digit cryptographic OTP, renders realistic smartphone slide-down SMS banner, enforces 15-minute countdown, and matches tokens.
• Input / Output: Approval request ID and user-submitted token $\rightarrow$ Authorization confirmation or account freeze.

6.3.7 Module 7: Autonomous Investigation & Case Management Module
• Purpose: Manages forensic investigative workflows for flagged transactions.
• Processing: Automatically creates investigation case records with audit notes, tracks analyst assignments, records formal determinations, and updates case lifecycles.
• Input / Output: Flagged transaction ID $\rightarrow$ Managed case docket with full forensic timeline.

6.3.8 Module 8: Interactive Command Center, Intelligence Radar & Analytics Dashboard
• Purpose: Visualizes real-time transaction telemetry and merchant fleet surveillance.
• Processing: Subscribes to full-duplex WebSocket feeds, rendering live radar streams, risk telemetry grids, and 29-merchant profiling summaries.
• Input / Output: Streaming transaction events $\rightarrow$ Interactive reactive charts and telemetry feeds.

6.3.9 Module 9: AI Forensic Copilot & Multi-LLM Reasoning Engine
• Purpose: Automates forensic dossier synthesis and regulatory compliance reporting.
• Processing: Coordinates multi-LLM reasoning via Google Gemini 1.5 Pro and xAI Grok-2, generating 4-stage kill-chain attack topologies, copyable Mermaid graphs, SAR drafts, and spoken natural voice briefings.
• Input / Output: Case ID $\rightarrow$ Synthesized forensic dossier, attack graph, and spoken audio narration.

6.3.10 Module 10: Role-Based Access Control, Idempotency & Immutable Audit Logging
• Purpose: Enforces zero-data-leakage multi-tenant privacy and systemic auditability.
• Processing: Validates OAuth2 JWT bearer tokens with role scopes (CUSTOMER, INVESTIGATOR, ADMIN), enforces customer-isolated database queries, intercepts duplicate network payloads, and records SHA-256 hashed audit logs.
• Input / Output: HTTP request headers $\rightarrow$ Authenticated session context and tamper-evident audit record.
"""
''')

print("Appended Chapter 6: Proposed Algorithm Implementation successfully.")
