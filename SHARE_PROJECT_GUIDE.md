# 🚀 How to Share FraudLens AI with Your Friend (Without Deployment)

This guide explains exactly how to share your entire **FraudLens AI** project with your friend so he can access **100% of all features, AI models, modules, and datasets identically** to what you are using.

---

## 📌 Compatibility Confirmation: Python 3.14.7 vs 3.14.5

> **YES, 100% COMPATIBLE!**  
> Your project was developed on Python 3.14.5. Your friend has **Python 3.14.7**, which is in the exact same minor release series. All dependencies (`fastapi`, `xgboost`, `scikit-learn`, `shap`, `joblib`, `pandas`, `pydantic`) are 100% binary and API compatible with zero modifications required.

---

## 🎯 Will He Be Able to Access All Modules and Features?

**YES, every single module and capability will be available:**
1. **Pre-Auth Payment Gateway**: Real-time evaluation (< 4ms) with the all-names Recipient/Beneficiary dropdown across all **29 Registered Canonical Merchants**.
2. **Customer Dashboards & 3 Isolated Personas**:
   - **Monisha**: 3% Fraud Rate (Habitual shopper, ₹1,250 routine payments)
   - **Mohana**: 12% Fraud Rate (Velocity spikes, triggers Mobile OTP Step-Up)
   - **Sowmiya**: 26% Fraud Rate (Botnet account takeover, high-value gold bullion, AI freeze)
3. **Real-Time Mobile SMS OTP Step-Up**: Interactive 6-digit verification with genuine PIN matching.
4. **Explainable AI (XAI) & TreeSHAP Game Theory**: All 4 candidate ML models (**XGBoost Champion**, **Random Forest**, **Logistic Regression**, **Ensemble Stacking**) with multi-model comparison matrix, counterfactual what-if analysis, and directional Shapley value bars.
5. **AI Voice Help & What is Fraud Explainer**: Spoken voice briefings (Siri / Google Voice), microphone speech recognition commands, and Gemini/Grok switcher.
6. **Admin Command Center**: Fraud Investigations, Model Lab tournament, Live Radar Monitor, Merchant Intelligence, Dataset Health, and Operations Manual.

---

## 🛠️ The 4 Ways to Share (Without Any Cloud Deployment)

---

### Method 1: ZIP Archive / Google Drive / Pendrive Transfer (Recommended)

This gives your friend the full source code, pre-trained AI models, and database to run completely on his own machine.

#### Step 1: Prepare the Folder to Send
To keep the file size compact (compressing from ~1 GB down to ~35 MB), **exclude** temporary folders when zipping:
- **INCLUDE in the ZIP:**
  - `backend/`
  - `frontend/` (exclude `node_modules`)
  - `ml/` (contains serialized models like `xgboost_model.joblib`, `shap_explainer.joblib`)
  - `data/`
  - `scripts/`
  - `fraud_detection.db` *(Critical: contains all seeded transactions and personas)*
  - `requirements.txt`
  - `setup_project.bat`
  - `run_live_system.bat`
  - `USER_MANUAL.md`
- **EXCLUDE before zipping:**
  - `frontend/node_modules/` *(He will install this in 1 click)*
  - `.venv/` *(Python virtual environment is machine-specific)*
  - `.pytest_cache/`

#### Step 2: What Your Friend Needs to Do
1. Extract the ZIP folder anywhere on his PC (e.g. `C:\fraudlens` or `D:\fraudinvestigation`).
2. Double-click **`setup_project.bat`**:
   - It automatically checks Python 3.14.7.
   - Installs all Python dependencies from `requirements.txt`.
   - Runs `npm install` for the React frontend.
   - Verifies the pre-trained ML models and SQLite database.
3. Double-click **`run_live_system.bat`**:
   - Automatically opens the FastAPI backend on `http://127.0.0.1:8000`
   - Automatically opens the React Vite UI on `http://localhost:5173`
4. Open the browser to: **`http://localhost:5173/`**
5. Log in with either:
   - **Admin / Investigator**: `admin@fraudlens.com` / `adminpassword123`
   - **Monisha (3%)**: `monisha.s@customer.fraudlens.ai` / `customer123`
   - **Mohana (12%)**: `mohana.k@customer.fraudlens.ai` / `customer123`
   - **Sowmiya (26%)**: `sowmiya.m@customer.fraudlens.ai` / `customer123`

---

### Method 2: Private GitHub / GitLab Repository

If both of you use Git:

1. Push your repository to a private GitHub repo:
   ```bash
   git add .
   git commit -m "FraudLens AI - Complete Production Suite v2.6"
   git push origin main
   ```
2. In GitHub, go to **Settings &rarr; Collaborators** and invite your friend's GitHub account.
3. Your friend simply clones the repo on his machine:
   ```bash
   git clone <YOUR_GITHUB_REPO_URL>
   cd fraudinvestigation
   ```
4. He runs `setup_project.bat` and then `run_live_system.bat`.

---

### Method 3: Same Wi-Fi / Local Area Network (Zero Installation for Friend!)

If you and your friend are on the **same Wi-Fi network** (e.g., college lab, home, or mobile hotspot):
**Your friend does NOT need to install Python, Node.js, or anything!**

1. On your laptop, open `run_live_system.bat` or run:
   - Backend:
     ```powershell
     python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
     ```
   - Frontend:
     ```powershell
     npm --prefix frontend run dev -- --host 0.0.0.0
     ```
2. Find your laptop's local IP address:
   - Open Command Prompt and type `ipconfig` (look for `IPv4 Address`, e.g., `192.168.1.45`).
3. Tell your friend to open this in his browser (on his laptop or smartphone):
   ```
   http://192.168.1.45:5173
   ```
4. **He can immediately use all screens, simulate payments, hear voice briefings, and test AI models live from his device!**

---

### Method 4: Instant Free Secure Tunnel (Cloudflare Tunnel - Over the Internet!)

If your friend is in another location or city and you want him to test your running app **right now without any cloud hosting or deployment**:

1. Make sure your local servers are running (`run_live_system.bat`).
2. Open a new terminal on your PC and run:
   ```powershell
   npx cloudflared tunnel --url http://localhost:5173
   ```
3. Cloudflare will output a free, secure public link, for example:
   ```
   https://random-assigned-name.trycloudflare.com
   ```
4. Send that URL via WhatsApp or email to your friend.
5. He clicks the link on his laptop or phone and accesses the complete, live FraudLens AI application immediately!

---

## 📋 Checklist for Verification on Friend's Machine

| Step | Action | Expected Result |
| :--- | :--- | :--- |
| **1. Setup** | Run `setup_project.bat` | Installs `requirements.txt` & `package.json` with zero errors. |
| **2. Launch** | Run `run_live_system.bat` | Two terminal windows launch (FastAPI port 8000 & Vite port 5173). |
| **3. Login** | Visit `http://localhost:5173` | Login scene with cyber particles and sound effects appears. |
| **4. Payment Gateway** | Click "Recipient Dropdown" | Shows all 29 merchants and verified customer payees. |
| **5. Explainable AI** | View TreeSHAP | Renders XGBoost, Random Forest, Logistic Regression, Ensemble Stacking. |
| **6. AI Voice Help** | Click "🎙️ AI Voice Help" | Spoken audio briefing plays aloud with neon soundwave visualizer. |
| **7. Mobile OTP** | Run high-ticket txn | Triggers 6-digit OTP step-up notification on mobile simulator. |
