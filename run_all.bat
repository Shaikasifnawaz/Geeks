@echo off
REM Run backend API and Streamlit frontend (Windows CMD)
REM Usage: run_all.bat

SETLOCAL
SET PROJECT_ROOT=%~dp0
cd /d "%PROJECT_ROOT%"

REM If you use a virtualenv, activate it before running this script (uncomment next line)
REM call .venv\Scripts\activate.bat

echo Starting backend API on http://127.0.0.1:5001

echo Running ETL pipeline (backend\main.py)
call python backend\main.py --year 2025
if ERRORLEVEL 1 (
	echo ETL failed. Aborting launcher.
	goto :EOF
)

echo Starting backend API on http://127.0.0.1:5001
start "NCAAFB Backend" cmd /k "python backend\data_api.py --host 127.0.0.1 --port 5001"

timeout /t 2 /nobreak >nul

echo Starting Streamlit frontend on http://localhost:8501
start "NCAAFB Frontend" cmd /k "streamlit run frontend\app.py --server.port 8501"

echo Launched backend and frontend. Open http://localhost:8501 in your browser.
ENDLOCAL
