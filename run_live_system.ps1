# FraudLens AI - PowerShell Dual Server Launcher
Write-Host "===================================================" -ForegroundColor Cyan
Write-Host "    Starting FraudLens AI Backend and Frontend     " -ForegroundColor Cyan
Write-Host "===================================================" -ForegroundColor Cyan

# Ensure System32 and PowerShell are in PATH
$sys32 = "$env:SystemRoot\System32"
$psDir = "$env:SystemRoot\System32\WindowsPowerShell\v1.0"
if ($env:PATH -notlike "*$sys32*") { $env:PATH = "$sys32;$psDir;$env:PATH" }

$psExe = (Get-Process -Id $PID).Path
if (-not (Test-Path $psExe)) { 
    $psExe = "$psDir\powershell.exe"
    if (-not (Test-Path $psExe)) { $psExe = "powershell" }
}

$pyExe = "$env:LOCALAPPDATA\Python\pythoncore-3.14-64\python.exe"
if (-not (Test-Path $pyExe)) {
    if (Test-Path ".venv\Scripts\python.exe") { 
        $pyExe = Resolve-Path ".venv\Scripts\python.exe" 
    } else { 
        $pyExe = "python" 
    }
}

# 1. Start Backend in separate window
Write-Host "`n[1/2] Launching FastAPI Backend on http://127.0.0.1:8000 ..." -ForegroundColor Green
Start-Process $psExe -WorkingDirectory $PSScriptRoot -ArgumentList "-NoExit", "-Command", "`$env:PYTHONPATH='.'; & '$pyExe' -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload"

Write-Host "Waiting for backend ML models to warm up..." -ForegroundColor Gray
$ready = $false
for ($i = 0; $i -lt 15; $i++) {
    try {
        $res = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/health" -TimeoutSec 2 -ErrorAction Stop
        if ($res.status -eq "healthy") {
            $ready = $true
            break
        }
    } catch {
        Start-Sleep -Seconds 1
    }
}

if ($ready) {
    Write-Host "Backend is healthy and models are ready!" -ForegroundColor Green
} else {
    Write-Host "Backend is still initializing, proceeding with frontend launch..." -ForegroundColor Yellow
}

# 2. Start Frontend in separate window
Write-Host "[2/2] Launching React Vite Frontend on http://localhost:5173 ..." -ForegroundColor Green
Start-Process $psExe -WorkingDirectory $PSScriptRoot -ArgumentList "-NoExit", "-Command", "npm --prefix frontend run dev"

Write-Host "`nBoth servers started in separate windows!" -ForegroundColor Yellow
Write-Host "Open your browser to: http://localhost:5173`n" -ForegroundColor Cyan

