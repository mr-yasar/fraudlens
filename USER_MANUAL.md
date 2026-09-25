# 🛡️ FraudLens AI — Master User Manual & Operations Guide (₹ INR Edition)

Welcome to **FraudLens AI**, an Explainable AI Financial Fraud Detection, Risk Intelligence, Adaptive Defense & Autonomous Case Investigation Command Center.

---

## ⚡ Quick Start: 3 Steps to Launch & Log In

### Step 1: Access the Application
Open your web browser and navigate to: **[http://localhost:5173](http://localhost:5173)**.  
*(Ensure the backend Uvicorn API is running on `http://127.0.0.1:8000`)*.

### Step 2: Role Authentication & Strict Data Isolation
FraudLens AI enforces zero-data-leakage and strict role-based access control (RBAC):

| Portal | Scope & Privacy Guarantee | Access Privileges |
| :--- | :--- | :--- |
| 🛡️ **Administrator & Security Analyst** | **Merchant & Fleet Surveillance**: Oversees merchant risks and investigation queues without exposing private customer credentials. | Complete access to 29 merchant parameters, AI Forensic Copilot (Gemini & Grok), visual attack kill-chain diagrams, Model Lab tournament, and SAR filings. |
| 👤 **Customer & Cardholder Space** | **Strict Tenant Privacy**: Cardholders can **only** access their own transaction records, account balances, and security approvals. | Instant pre-auth payment gateway, real-time risk scores, personalized TreeSHAP explanation bars, and mobile phone SMS OTP authorization. |

> **Privacy Guarantee**: Under no circumstances can any customer view or query another customer's transactions, account numbers, or personal profile history. Database queries are strictly scoped to the authenticated customer token.

### Step 3: Enter the AI Command Center
Click **"ENTER COMMAND CENTER"** to launch the dark cyber-fintech security interface.

---

## 📱 Real Mobile Phone SMS & OTP Security Verification

When a transaction triggers an **Elevated / High Risk** determination or is flagged for step-up verification:

```
┌────────────────────────┐      ┌─────────────────────────┐      ┌─────────────────────────┐
│ Suspicious Transaction │ ───► │ Realistic Smartphone    │ ───► │ Strict 6-Digit OTP      │
│ Flagged (Score > 75)   │      │ SMS Push Banner         │      │ Match Verification      │
└────────────────────────┘      └─────────────────────────┘      └────────────┬────────────┘
                                                                              │
                                 ┌────────────────────────────────────────────┴────────────┐
                                 ▼                                                         ▼
                     [ ✅ Code Matches OTP ]                                    [ ❌ Reject / Timeout ]
                     Transaction Approved & Logged                              Account Locked & Frozen
```

### How to Complete Phone OTP Verification:
1. In the **Payment Gateway (Pre-Auth)**, submit a transaction with elevated amount or high velocity.
2. When the **Mobile Security Approval Modal** opens:
   - A simulated **Realistic Smartphone SMS Notification** slides down showing the real generated 6-digit OTP code (e.g. `482910`).
   - The OTP displays the target merchant, amount in **₹ INR**, and a 5-minute security validity countdown.
3. Enter the 6-digit code into the interactive input boxes.
4. Click **"Verify & Authorize Transaction"**:
   - If code matches: Transaction is confirmed, risk status updates to `AUTHORIZED`, and ledger reflects approval.
   - If suspicious: Click **"Reject & Freeze Account"** to immediately halt the card and open an investigation case.

---

## 🤖 Admin AI Forensic Copilot, Voice Briefing & Attack Diagrams

Accessible exclusively in **Admin Mode** under **Fraud Investigations**:

```
                       ┌────────────────────────────────────────┐
                       │       Admin Fraud Investigations       │
                       └───────────────────┬────────────────────┘
                                           │
         ┌─────────────────────────────────┴─────────────────────────────────┐
         ▼                                 ▼                                 ▼
┌─────────────────┐             ┌─────────────────────┐            ┌────────────────────┐
│ AI Reasoning    │             │ Visual Architecture │            │ Voice Assistant    │
│ Engine Switcher │             │ Diagrams & Defense  │            │ (Siri / Google)    │
├─────────────────┤             ├─────────────────────┤            ├────────────────────┤
│ • Google Gemini │             │ • 4-Stage Kill-Chain│            │ • Audio Briefing   │
│   1.5 Pro       │             │   Threat Flow       │            │   (Text-to-Speech) │
│ • xAI Grok-2    │             │ • Mermaid Graph     │            │ • Voice Command    │
│   Enterprise    │             │   Topology          │            │   Microphone Input │
│ • Claude 3.5    │             │ • Evidence Log &    │            │ • Soundwave Audio  │
│   Sonnet        │             │   Defense Barrier   │            │   Visualizer       │
└─────────────────┘             └─────────────────────┘            └────────────────────┘
```

### 1. Multi-Model AI Service Selection
* **Google Gemini 1.5 Pro**: Multimodal forensic reasoning, contextual customer profile matching, and comprehensive behavioral root-cause analysis.
* **xAI Grok-2 Enterprise**: Adversarial attack-pattern decomposition, botnet credential stuffing attribution, and high-precision fraud adjudication.
* **Claude 3.5 Sonnet**: Methodical audit-trail generation and evidence verification.

### 2. End-to-End Attack Architecture & Kill-Chain Diagram
Visualizes the 4 critical defense barriers preventing fund exfiltration:
1. **Threat Origin**: Compromised session, credential injection, or untrusted client device.
2. **Target Intent**: Velocity spike, abnormal merchant ticket size, or unauthorized transfer.
3. **AI Gatekeeper**: Sub-4ms isolation via XGBoost, Random Forest, and TreeSHAP game theory.
4. **Outcome / Asset Preservation**: Fund freeze, step-up challenge, or approval.
* Includes copyable **Mermaid Architecture Graph Syntax** for academic documentation and presentation slides.

### 3. Voice Assistant Integration (Siri & Google Voice)
* **Audible Spoken Case Briefings**: Click **"Listen to Briefing"** to hear a realistic spoken voice briefing generated in real-time via the browser's speech synthesis engine.
* **Natural Voice Selection**: Choose between Apple Siri-like voices, Google UK English, and Microsoft Natural voices.
* **Microphone Voice Commands**: Click **"Voice Command"** and speak into your mic:
  - *"Summarize case"* &rarr; Navigates to the executive forensic summary.
  - *"Attack diagram"* &rarr; Displays the visual kill-chain architecture.
  - *"Confirm fraud and freeze"* &rarr; Submits a formal case determination.

### 4. Regulatory SAR (Suspicious Activity Report) Drafting
* One-click generation of regulatory Suspicious Activity Reports (SAR) compliant with banking audit standards.
* Includes narrative findings, primary suspicious indicators, transaction timestamps, and copy-to-clipboard functionality.

---

## 🧭 Master Navigation & Module Overview

| Module | Purpose & Core Capabilities | Primary Role |
| :--- | :--- | :--- |
| **📊 Command Dashboard** | Real-time overview of fraud activity, high-risk flags, merchant risk alerts, and investigation queues. | Investigator & Customer |
| **💳 Payment Gateway** | Interactive payment processing with instant risk scoring, merchant selection, and phone OTP step-up. | Investigator & Customer |
| **🧠 Transaction Risk Analyzer** | In-depth parameter testing across the 29 Master Merchants with ML Probability, Independent Risk Score, and SHAP. | Investigator & Customer |
| **📻 Live Fraud Monitor** | Real-time streaming radar of incoming transactions with auto-updating risk telemetry and instant step-up flags. | Investigator Only |
| **🏬 Merchant Intelligence** | Directory and deep-dive profiling for all 29 master fictional merchants across Chennai, Coimbatore, Madurai, Salem, Bengaluru. | Investigator Only |
| **📜 All Transactions** | Searchable database of canonical transactions with filtering by merchant, fraud label, and risk score. | Investigator & Customer |
| **👥 Customer Intelligence** | Spending baseline analysis, tenure, velocity, and anomaly detection per customer. | Investigator Only |
| **✨ Explainable AI & SHAP** | Visual horizontal waterfall contribution bars explaining **why** the ML model flagged a transaction. | Investigator & Customer |
| **🛡️ Fraud Investigations** | AI Forensic Copilot (Gemini / Grok), Attack Diagrams, Siri Voice Briefings, and case lifecycle management. | Investigator Only |
| **⚙️ Model Lab & Registry** | Side-by-side tournament comparing Logistic Regression, Random Forest, and XGBoost using Precision, Recall, F1, and PR-AUC. | Investigator / Admin |
| **🗄️ Dataset Health & Audit** | Academic audit of 20,000 records, 29 merchants, and strict zero-target-leakage isolation. | Investigator / Admin |
| **📈 Reports & Analytics** | Executive summaries, merchant risk breakdowns, and exportable audit reports. | Investigator & Customer |
| **📜 Audit Logs** | Immutable chronological record of all administrative and inference events. | Investigator / Admin |

---

## 🏬 Master 29-Merchant Directory

FraudLens AI profiles 29 distinct synthetic commercial merchants across Tamil Nadu & Karnataka:
* **M001 — NovaMart Fresh Supermarket** (Grocery & Supermarket, T Nagar, Chennai)
* **M002 — CircuitBay Electronics** (Consumer Electronics, Velachery, Chennai)
* **M003 — Pulse Mobile Hub** (Mobile Store, Tambaram, Chennai)
* **M004 — Aurelia Gold House** (Jewellery, RS Puram, Coimbatore)
* **M005 — UrbanThread Studio** (Fashion, Anna Nagar, Chennai)
* **M006 — MedicoCare Pharmacy** (Pharmacy, KK Nagar, Madurai)
* **M007 — SpiceRoute Kitchen** (Restaurant, Adyar, Chennai)
* **M008 — BeanCircuit Cafe** (Cafe, Indiranagar, Bengaluru)
* **M009 — RapidFuel Station** (Fuel Station, Fairlands, Salem)
* **M010 — HarborView Residency** (Hospitality, OMR, Chennai)
* **M011 — SkyTrail Travels** (Travel Agency, Gandhipuram, Coimbatore)
* ... and M012 through M029 covering auto care, logistics, e-commerce, gaming, and cloud digital services.

---

## 🔬 How the Transaction Risk Analyzer Works

1. **Select Merchant**: Pick any of the 29 master merchants.
2. **Enter Transaction Amount**: Amount in Indian Rupees (**₹ INR**).
3. **Configure Context**: Device type, transaction hour, velocity in last 1h/24h, new device flag, new beneficiary flag, and location distance jump.
4. **Click "Analyze Transaction Risk"**:
   - **ML Fraud Probability**: 0.0% to 100.0% probability from the champion XGBoost/Random Forest model.
   - **Independent Risk Score**: 0 to 100 composite score factoring velocity, security flags, and merchant historical fraud rate.
   - **SHAP Feature Attributions**: Horizontal bars highlighting the strongest risk-increasing (+) and risk-reducing (-) contributors.
   - **Recommended Action**: `ALLOW / PROCEED`, `REVIEW / STEP-UP VERIFY`, or `BLOCK / INVESTIGATE`.

---

## 💡 Frequently Asked Questions (FAQ)

**Q: Are all currency amounts displayed in Indian Rupees?**  
> Yes. All amounts throughout the dashboard, transactions, analyzer, and merchant profiles are formatted in **₹ INR** using the Indian numbering system (e.g. ₹1,25,000.00).

**Q: Is there any data leakage in the ML models?**  
> Zero. Target fields (`is_fraud`, `fraud_type`, `fraud_stage`, `fraud_scenario`) and text summaries are strictly excluded from training. Models only receive features available prior to transaction authorization.

**Q: How does the AI Copilot help in presentations and vivas?**  
> You can switch between **Google Gemini 1.5** and **xAI Grok-2**, show the **Attack Architecture Diagram & Kill-Chain**, and click **"Listen to Briefing"** to let the voice assistant explain the fraud detection logic aloud to professors and evaluators!
