<#
Run both backend API and Streamlit frontend from project root (PowerShell).

Usage:
  Right-click -> Run with PowerShell, or from an elevated PowerShell:
    .\run_all.ps1

Notes:
 - Ensure Python virtualenv is activated or installed packages are available.
 - Create `backend/.env` with DB and API keys before running.
#>

Set-StrictMode -Version Latest

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Definition
Push-Location $projectRoot

# Activate virtualenv if present
if (Test-Path .venv\Scripts\Activate.ps1) {
    Write-Host "Activating virtualenv .venv"
    . .\.venv\Scripts\Activate.ps1
}
# Run ETL (main.py) first to fetch/transform/populate
Write-Host "Running ETL pipeline (backend\main.py)"
& python backend\main.py --year 2025
if ($LASTEXITCODE -ne 0) {
  Write-Error "ETL pipeline failed (exit code $LASTEXITCODE). Aborting launcher."
  Pop-Location
  exit $LASTEXITCODE
}

# Start backend API
Write-Host "Starting backend API (data_api.py) on http://127.0.0.1:5001"
Start-Process -NoNewWindow -FilePath python -ArgumentList 'backend\data_api.py --host 127.0.0.1 --port 5001' -WindowStyle Hidden

Start-Sleep -Seconds 2

# Start Streamlit frontend
Write-Host "Starting Streamlit frontend on http://localhost:8501"
Start-Process -NoNewWindow -FilePath streamlit -ArgumentList 'run frontend\app.py --server.port 8501' -WindowStyle Hidden

Write-Host "Launched ETL, backend and frontend. Open http://localhost:8501 in your browser."
Pop-Location
