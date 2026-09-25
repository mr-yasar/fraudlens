# FraudLens AI - PowerShell Dual Server Launcher
Write-Host "===================================================" -ForegroundColor Cyan
Write-Host "    Starting FraudLens AI Backend and Frontend     " -ForegroundColor Cyan
Write-Host "===================================================" -ForegroundColor Cyan

# 1. Start Backend in separate window
Write-Host "`n[1/2] Launching FastAPI Backend on http://127.0.0.1:8000 ..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "`$env:PYTHONPATH='.'; python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload"

# 2. Start Frontend in separate window
Write-Host "[2/2] Launching React Vite Frontend on http://localhost:5173 ..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "npm --prefix frontend run dev"

Write-Host "`nBoth servers started in separate windows!" -ForegroundColor Yellow
Write-Host "Open your browser to: http://localhost:5173`n" -ForegroundColor Cyan
