@echo off
setlocal enabledelayedexpansion

echo =====================================================================
echo  BSR Rate Hub - Sri Lanka BOQ Data System
echo  Production Windows Launcher
echo =====================================================================
echo.

cd /d "%~dp0\.."

:: Check if Docker daemon is running
docker info >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Docker Desktop is not running!
    echo Please launch Docker Desktop from your Start menu and wait until it is ready.
    echo.
    pause
    exit /b 1
)

echo [1/4] Ensuring persistent storage directories exist...
if not exist "data\uploads" mkdir "data\uploads"
if not exist "data\backups" mkdir "data\backups"

echo [2/4] Building and launching Docker containers (PostgreSQL, FastAPI, Nginx)...
docker compose up -d --build
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Failed to start Docker Compose services!
    pause
    exit /b 1
)

echo [3/4] Ensuring database schema and rate quality are synchronized...
timeout /t 2 /nobreak >nul
docker compose exec -T backend alembic upgrade head >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    docker compose exec -T backend alembic stamp head >nul 2>&1
)
docker compose exec -T backend python -m app.scripts.clean_noise_and_recalc >nul 2>&1

echo [4/4] System is healthy and operational!
echo.
echo =====================================================================
echo  APPLICATION ACCESSIBLE AT:
echo    Local PC:    http://localhost:8080
echo.
echo  OFFICE LAN ACCESS (From other PCs in office):
echo    Find your IP with 'ipconfig' (e.g. http://192.168.1.X:8080)
echo =====================================================================
echo.

:: Automatically open default browser
start http://localhost:8080

echo Press any key to close this launcher window (containers keep running in background).
pause >nul
