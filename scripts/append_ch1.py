"""
Script to generate the complete, comprehensive report_data.py.
"""

from pathlib import Path

output_file = Path("e:/fraudinvestigation/scripts/report_data.py")

with open(output_file, "a", encoding="utf-8") as f:
    f.write('''
# ==============================================================================
# CHAPTER 1: INTRODUCTION
# ==============================================================================

CH1_OVERVIEW = """
1.1 OVERVIEW OF THE PROJECT

The contemporary financial architecture has experienced an unprecedented paradigm shift, propelled by the ubiquity of high-speed telecommunications, pervasive mobile computing, and the national deployment of immediate clearing settlement payment networks. Systems such as the Unified Payments Interface (UPI) in India, Immediate Payment Service (IMPS), real-time automated clearinghouses (ACH), and digital multi-currency card networks have permanently condensed transaction clearance latencies from multi-day batch settlement cycles to sub-second cryptographic handshakes. While this hyper-connected velocity has fundamentally democratized financial access, catalyzed micro-commerce, and drastically elevated consumer liquidity, it has concurrently expanded the digital threat landscape to an extraordinary degree.

Financial fraud syndicates have evolved far beyond opportunistic, isolated debit card theft into industrialized, highly coordinated cybercriminal syndicates. Modern payment fraud leverages distributed account takeover (ATO) botnets, automated credential stuffing attacks, SIM-swapping operations, social engineering reverse-vishing exploits, and automated velocity burst manipulation. Fraudsters exploit the structural blind spots of legacy banking infrastructure: specifically, the narrow 50-millisecond authorization window within which an issuing bank must evaluate transaction legitimacy before committing funds to an acquiring merchant terminal.

Historically, financial institutions defended these digital perimeters using static, deterministic rule-based expert engines. These legacy systems operate on heuristic Boolean threshold filters—such as flagging any transaction exceeding a fixed monetary threshold (e.g., amount > ₹50,000) or rejecting transactions originating outside a cardholder\'s resident nation. However, deterministic rule engines exhibit severe structural failure modes in high-volume environments:
1. Acute Rule Rigidity and Latency: Static rules cannot adapt dynamically to evolving fraudulent tactics. Fraud syndicates routinely conduct reconnaissance to probe authorization thresholds and systematically route micro-transactions just beneath established rule triggers.
2. Catastrophic False-Positive Rates: Rule-based systems lack individualized behavioral context. Legitimate cardholder behaviors—such as emergency medical expenses, holiday travel, or irregular late-night commerce—trigger erroneous transaction declines. Studies indicate that up to 80% of transactions flagged by legacy rule engines represent legitimate consumer spending, precipitating severe customer attrition, brand damage, and lost merchant revenue.
3. Exponential Rule Accumulation: As new fraud typologies emerge, financial institutions continually append heuristic rules, resulting in unwieldy policy rulebooks containing thousands of overlapping, conflicting rules that degrade gateway latency without improving fraud detection precision.

To overcome the fragility of heuristic rules, the financial technology sector turned toward supervised and unsupervised machine learning (ML) models, including gradient-boosted decision trees, random forests, and deep neural networks. While these statistical models achieve superior discriminative performance on high-dimensional tabular data, their widespread adoption in commercial banking has introduced a profound regulatory and operational impasse: the "black-box" dilemma. Highly complex non-linear ensemble models output a singular continuous probability metric (e.g., fraud_probability = 0.942) without articulating the underlying feature interactions or causal attributions that drove the prediction.

This lack of transparency produces severe operational and legal ramifications:
• Regulatory Non-Compliance: Global legal frameworks, including the European Union General Data Protection Regulation (GDPR Article 22 Right to Explanation) and the Reserve Bank of India (RBI) Cyber Security Framework for Digital Payment Transactions, legally mandate that automated financial decisions affecting consumer rights, credit limits, or fund freezes must be interpretable and auditable.
• Investigator Burnout and Triage Delays: In enterprise Security Operations Centers (SOC) and Fraud Investigation Units (FIU), human forensic analysts are tasked with reviewing hundreds of flagged transactions daily. Confronted with an opaque probability score devoid of context, analysts are forced into manual, laborious cross-referencing across disparate ledger systems, taking 30 to 45 minutes to adjudicate a single case.
• Conflation of Risk and Probability: Conventional fraud architectures routinely make the flawed assumption that statistical fraud probability is identical to operational transactional risk. In reality, a micro-transaction of ₹150 attempted from an unrecognized device may carry high statistical anomaly probability due to novelty, yet represents negligible balance exposure; conversely, a ₹2,00,000 transaction from an established device carries catastrophic financial loss exposure despite displaying a moderate statistical probability.

To resolve these fundamental industry dilemmas, this project develops FraudLens AI, an enterprise-grade, explainable artificial intelligence (XAI) financial fraud and risk detection system. FraudLens AI bridges the gap between state-of-the-art predictive performance, deterministic multi-factor risk assessment, mathematical explainability, and autonomous operational investigation. Architected upon an end-to-end modern software stack, FraudLens AI unifies extreme gradient boosting (XGBoost) and soft-voting ensemble learning with TreeSHAP (SHapley Additive exPlanations) game theory, sub-5ms pre-authorization gatekeeping, smartphone SMS OTP step-up verification, and an autonomous GenAI forensic investigation copilot powered by Google Gemini 1.5 Pro and xAI Grok-2.
"""

CH1_OBJECTIVES = """
1.2 OBJECTIVE OF THE PROJECT

The primary objective of FraudLens AI is to design, develop, rigorously validate, and deploy an explainable, real-time, multi-factor financial fraud detection, risk intelligence, and autonomous case investigation platform. The system is engineered to provide actionable transparency, zero-data-leakage multi-tenant privacy, and sub-second operational decisioning for digital payment networks.

The specific, measurable academic and technical objectives of this project are formulated as follows:

1. High-Performance Tabular Machine Learning Pipeline:
   To formulate, train, tune, and evaluate high-performance supervised classification models—specifically regularized Logistic Regression with inverse class weighting, a tuned Random Forest ensemble, and an Extreme Gradient Boosted decision tree (XGBoost) model—on a multi-merchant dataset of 20,000 synthetic transaction records spanning 57 behavioral, temporal, and spatial attributes across 30 commercial merchants, achieving a test Recall of 100.0% and a ROC-AUC exceeding 0.990 on imbalanced fraud distributions.

2. Strict Architectural Decoupling of Fraud Probability and Risk Score:
   To engineer a transparent, deterministic Multi-Factor Risk Scoring Engine that strictly separates model-derived Fraud Probability (a continuous metric between 0.0 and 1.0) from an independent operational Risk Score (an integer metric scaled between 0 and 100). The scoring engine must incorporate five orthogonal dimensions: continuous ML probability curves, spending deviation ratios against 30-day customer historical baselines, transaction velocity bursts across 1-hour and 24-hour windows, beneficiary integrity profiles, and hardware/environmental novelty signals.

3. Game-Theoretic Explainable AI (XAI) via TreeSHAP:
   To embed exact, mathematically consistent feature attribution into the pre-authorization pipeline using TreeSHAP and LinearSHAP. The system must compute exact Shapley values for all transformed input features in real time, decomposing every prediction into local risk-increasing and risk-decreasing factors visualized through interactive waterfall plots, and generating evidence-grounded natural language forensic explanations for investigators.

4. Autonomous Pre-Authorization Gatekeeper & Decisioning:
   To establish a sub-5ms pre-authorization gatekeeper that executes deterministic decisioning across three discrete operational tiers:
   • ALLOW (Score 0–30): Frictionless, zero-latency transaction pass-through and simulated wallet balance deduction.
   • REVIEW (Score 31–70 or rapid velocity trigger): Automated transaction holding, simulated balance freezing, and initiation of a cryptographic step-up verification challenge.
   • BLOCK (Score 71–100 or hard security violations): Immediate transaction termination, balance preservation, and automatic escalation to the forensic investigation queue.

5. Realistic Smartphone SMS OTP Security Verification:
   To implement an interactive, simulated smartphone push-notification and SMS One-Time Password (OTP) verification modal for review-tier transactions. The verification subsystem must enforce cryptographic token hashing, a 15-minute time-to-live (TTL) countdown, and strict multi-attempt rate limiting, ensuring that zero funds are exfiltrated from the cardholder wallet until explicit verification is achieved.

6. Autonomous GenAI Forensic Copilot & Investigation Dossier Synthesis:
   To develop a specialized Generative AI Forensic Copilot supporting multi-model reasoning through Google Gemini 1.5 Pro, xAI Grok-2, and Anthropic Claude 3.5 Sonnet. The copilot must autonomously synthesize comprehensive case investigation dossiers, delineate 4-stage kill-chain attack topologies, generate copyable Mermaid architectural graphs, draft regulatory Suspicious Activity Reports (SAR) compliant with financial intelligence standards, and provide spoken natural voice briefings via browser speech synthesis.

7. Multi-Tenant Role-Based Access Control (RBAC) & Immutable Audit Logging:
   To enforce zero-data-leakage data contracts across customer, investigator, and administrator personas using FastAPI OAuth2 Password Bearer authentication, JWT token signing, and granular permission scopes. To record every administrative, authentication, and scoring event in an immutable cryptographic audit ledger, guaranteeing comprehensive forensic traceability.
"""

CH1_LITERATURE = """
1.3 LITERATURE REVIEW

Financial fraud detection has historically served as a critical benchmark domain for computational statistics, pattern recognition, and machine learning. Over the past three decades, research has transitioned from rudimentary statistical outlier detection to complex deep neural networks and, most recently, to explainable artificial intelligence (XAI). This section critically reviews the seminal paradigms in payment fraud analytics, identifies key methodological advancements, and delineates the specific research gaps that FraudLens AI addresses.

1.3.1 Statistical Profiling and Unsupervised Anomaly Detection
Early foundational research by Bolton and Hand (2002) established the utility of statistical profiling and unsupervised anomaly detection in credit card transaction monitoring. Their methodology, termed Breakpoint Analysis and Peer Group Analysis, focused on detecting structural shifts in a consumer\'s spending trajectory over time and identifying abnormal divergence from cohort clusters. While unsupervised statistical techniques eliminate the requirement for labeled fraud training data, they exhibit severe vulnerabilities in modern real-time environments: they generate extraordinarily high false-alarm rates because normal human consumer behavior is inherently non-stationary, featuring spontaneous expenditure spikes during festive seasons or life events that statistical distance metrics erroneously categorize as malicious.

1.3.2 Supervised Learning and Class Imbalance Mitigation
The advent of digital payment clearing houses shifted research toward supervised machine learning. Phua et al. (2010) presented an extensive survey of data mining techniques in financial fraud detection, benchmarking decision trees, naive Bayes, and backpropagation neural networks. Their findings underscored that class imbalance—where fraudulent transactions constitute less than 1% of total transaction volume—serves as the single greatest impediment to classifier convergence. Conventional empirical loss functions naturally gravitate toward the majority class, producing high nominal accuracy (e.g., 99%) while failing to detect genuine fraud incidents.

Dal Pozzolo et al. (2014, 2015) conducted extensive empirical investigations into real-world credit card data streams, formalizing the concept of verification latency and non-stationary concept drift. Verification latency refers to the reality that true fraud labels are not immediately available; chargebacks and customer fraud dispute reports require days or weeks to propagate back into the training corpus. Their work demonstrated that ensemble architectures combining bagging and adaptive boosting outperform individual classifiers by stabilizing decision boundaries against concept drift.

1.3.3 Ensemble Methods and Gradient Tree Boosting
In tabular financial data domains, tree-based ensemble methods consistently outperform unconstrained deep neural networks. Chen and Guestrin (2016) introduced XGBoost, an optimized distributed gradient boosting framework utilizing second-order Taylor approximations of the objective function, shrinkage, and column subsampling. XGBoost has achieved widespread prominence in financial risk modeling due to its handling of sparse categorical data, non-linear interaction modeling, and embedded support for class imbalance calibration via the scale_pos_weight parameter. Concurrently, Breiman\'s Random Forest (2001) remains a cornerstone benchmark, leveraging bootstrap aggregation (bagging) and random feature subspace selection to minimize variance without escalating model bias.

1.3.4 The Explainability Imperative and Game-Theoretic SHAP
Despite the predictive prowess of ensemble gradient boosting, their multi-layered branching structures render them opaque black boxes. In financial systems, black-box predictions produce acute operational liabilities. Caruana et al. (2015) demonstrated that high-performing machine learning models trained on complex tabular datasets frequently learn spurious correlations and toxic dataset artifacts that lead to disastrous real-world failures when deployed without interpretability safeguards.

To resolve the interpretability challenge, Lundberg and Lee (2017) formulated SHAP (SHapley Additive exPlanations), a unified game-theoretic framework for interpreting model predictions based on cooperative game theory originally formulated by Lloyd Shapley (1953). SHAP defines the explanation of an individual prediction as the unique additive feature attribution method satisfying three fundamental mathematical axioms: Local Accuracy (efficiency), Missingness, and Consistency. Lundberg et al. (2020) subsequently introduced TreeSHAP, an algorithm optimizing exact Shapley value computation for tree ensembles by traversing tree structures in low-order polynomial time $O(TLD^2)$ rather than exponential feature subsets $O(TL2^M)$, where $T$ is the number of trees, $L$ is the number of leaves, and $D$ is the maximum tree depth. This algorithmic breakthrough rendered real-time local attribution computationally feasible for high-throughput payment gateways.

1.3.5 Literature Comparison and Research Gap Analysis
Table 1.1 provides a structured comparative synthesis of prominent research contributions in financial fraud detection, delineating their primary methodologies, application contexts, key findings, intrinsic limitations, and direct relevance to FraudLens AI.
"""
''')

print("Appended Chapter 1 data successfully.")
