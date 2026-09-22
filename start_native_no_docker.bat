@echo off
setlocal enabledelayedexpansion

title BSR Rate Hub - Native Windows (No Docker)

echo =====================================================================
echo   BSR Rate Hub - Sri Lanka BOQ Data System
echo   Native Windows Launcher (NO DOCKER REQUIRED)
echo =====================================================================
echo.

cd /d "%~dp0"

:: Step 1: Check for Python 3
echo [Step 1/4] Checking Python installation...
where python >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo =====================================================================
    echo [ERROR] Python 3 was not found on this computer!
    echo =====================================================================
    echo To run without Docker, you just need Python (takes 2 minutes to install):
    echo.
    echo 1. Download Python 3.11 or 3.12 from:
    echo    https://www.python.org/downloads/
    echo 2. When running the installer, make sure to check the box:
    echo    "Add python.exe to PATH"
    echo 3. Click "Install Now".
    echo 4. After installation, double-click this script again!
    echo =====================================================================
    echo.
    pause
    exit /b 1
)

for /f "tokens=*" %%v in ('python --version 2^>^&1') do set "PY_VER=%%v"
echo [SUCCESS] Found %PY_VER%

:: Step 2: Check / Create Python Virtual Environment
echo.
echo [Step 2/4] Setting up Python virtual environment...
if not exist "venv\Scripts\python.exe" (
    echo Creating lightweight virtual environment in .\venv ...
    python -m venv venv
    if %ERRORLEVEL% NEQ 0 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
    echo [SUCCESS] Virtual environment created.
) else (
    echo [INFO] Existing virtual environment found.
)

:: Step 3: Install / verify Python requirements
echo.
echo [Step 3/4] Checking dependencies (FastAPI, ReportLab, openpyxl)...
call venv\Scripts\activate.bat

python -c "import fastapi, openpyxl, reportlab, uvicorn" >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Installing required packages (one-time setup, takes ~1 minute)...
    python -m pip install --upgrade pip
    pip install -r backend\requirements.txt
    if %ERRORLEVEL% NEQ 0 (
        echo [ERROR] Failed to install Python dependencies.
        pause
        exit /b 1
    )
) else (
    echo [SUCCESS] All Python libraries are ready.
)

:: Step 4: Ensure data directories and database exist
echo.
echo [Step 4/4] Verifying database and folders...
if not exist "data\uploads" mkdir "data\uploads"
if not exist "data\backups" mkdir "data\backups"

if exist "data\bsr_boq.db" (
    echo [SUCCESS] SQLite database verified (data\bsr_boq.db).
) else (
    echo [INFO] Database will be initialized automatically on first launch.
)

echo.
echo =====================================================================
echo   BSR Rate Hub is launching natively on Windows!
echo   URL: http://localhost:8080
echo =====================================================================
echo.
echo Press CTRL+C in this window anytime to stop the server.
echo.

:: Open browser after 2 seconds
start "" powershell -NoProfile -Command "Start-Sleep -Seconds 2; Start-Process 'http://localhost:8080'"

:: Launch FastAPI serving both API and built React frontend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8080 --app-dir backend
