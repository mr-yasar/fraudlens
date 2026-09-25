@echo off
title FraudLens AI - Dual Server Launcher
color 0A
echo ======================================================================
echo          FraudLens AI - Dual Server Production Launcher
echo ======================================================================
echo.

set PY_EXE=python
if exist ".venv\Scripts\python.exe" set PY_EXE=.venv\Scripts\python.exe

echo [1/2] Launching FastAPI Backend on http://127.0.0.1:8000 ...
start "FraudLens Backend API" cmd /k "set PYTHONPATH=. && %PY_EXE% -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload"

echo [2/2] Launching React Vite Frontend on http://localhost:5173 ...
start "FraudLens Frontend UI" cmd /k "npm --prefix frontend run dev"

echo.
echo ======================================================================
echo Both servers have been launched in separate terminal windows!
echo -> Web Application UI:   http://localhost:5173
echo -> Interactive API Docs: http://127.0.0.1:8000/docs
echo ======================================================================
echo.
pause
