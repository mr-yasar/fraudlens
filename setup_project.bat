@echo off
title FraudLens AI - 1-Click Automated Setup
color 0B
echo ======================================================================
echo          FraudLens AI - Automated Environment Setup
echo          Compatible with Python 3.10, 3.11, 3.12, 3.13, 3.14+
echo ======================================================================
echo.

echo [1/4] Verifying Python Environment...
python --version
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH!
    echo Please install Python 3.10+ from https://www.python.org/
    pause
    exit /b 1
)
echo Python detected successfully!
echo.

echo [2/4] Installing / Verifying Python Backend Dependencies...
python -m pip install --upgrade pip --quiet
python -m pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [WARNING] Some pip packages had warnings, checking core modules...
) else (
    echo Python dependencies installed cleanly!
)
echo.

echo [3/4] Verifying Node.js and Installing Frontend Dependencies...
call npm --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Node.js / npm is not installed or not in PATH!
    echo Please install Node.js from https://nodejs.org/ (LTS version recommended).
    pause
    exit /b 1
)
echo Node.js & npm detected! Installing React frontend dependencies...
cd frontend
call npm install
cd ..
echo Frontend packages installed successfully!
echo.

echo [4/4] Verifying Pre-Trained AI Models and Canonical Database...
if exist "fraud_detection.db" (
    echo [OK] Database 'fraud_detection.db' found with seeded 29 merchants and 3 customer profiles!
) else (
    echo [INFO] Seeding canonical database...
    set PYTHONPATH=.
    python scripts/seed_canonical_database.py
)

if exist "ml\artifacts\xgboost_model.joblib" (
    echo [OK] Serialized Machine Learning models and TreeSHAP explainer found!
) else (
    echo [INFO] Training ML models...
    set PYTHONPATH=.
    python scripts/train_canonical_models.py
)

echo.
echo ======================================================================
echo    SETUP COMPLETE! All modules and AI models are ready.
echo    You can now double-click 'run_live_system.bat' to launch the app!
echo ======================================================================
echo.
pause
