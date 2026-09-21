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
if %ERRORLEVEL% EQU 0 goto START_DOCKER_READY

:: Docker is not running. Find Docker Desktop executable
set "DOCKER_EXE="
if exist "C:\Program Files\Docker\Docker\Docker Desktop.exe" (
    set "DOCKER_EXE=C:\Program Files\Docker\Docker\Docker Desktop.exe"
) else if exist "%LOCALAPPDATA%\Programs\Docker\Docker\Docker Desktop.exe" (
    set "DOCKER_EXE=%LOCALAPPDATA%\Programs\Docker\Docker\Docker Desktop.exe"
)

if "%DOCKER_EXE%"=="" (
    echo [ERROR] Docker Desktop was not found at standard installation locations!
    echo Please open Docker Desktop manually from your Start Menu, wait until it says 'Engine running', and run this again.
    echo.
    pause
    exit /b 1
)

echo [INFO] Docker Desktop is not running. Starting Docker Desktop automatically...
start "" "%DOCKER_EXE%"
echo Waiting for Docker Desktop engine to become ready (up to 90 seconds)...

set WAITED=0

:WAIT_START_DOCKER
ping 127.0.0.1 -n 4 >nul
docker info >nul 2>&1
if %ERRORLEVEL% EQU 0 goto START_DOCKER_READY

set /a WAITED+=3
echo   Initializing engine... (!WAITED!s)
if !WAITED! GEQ 90 (
    echo.
    echo [ERROR] Docker Desktop took too long to respond.
    echo Please open Docker Desktop manually, ensure it says 'Engine running', and run this again.
    pause
    exit /b 1
)
goto WAIT_START_DOCKER

:START_DOCKER_READY

echo [1/4] Ensuring persistent storage directories exist...
if not exist "data\uploads" mkdir "data\uploads"
if not exist "data\backups" mkdir "data\backups"

echo [2/4] Starting Docker containers (PostgreSQL, FastAPI, Nginx)...
docker compose up -d
if %ERRORLEVEL% NEQ 0 (
    echo [INFO] Building containers if needed...
    docker compose up -d --build
)
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Failed to start Docker Compose services!
    pause
    exit /b 1
)

:: Verify backend is running and healthy
ping 127.0.0.1 -n 4 >nul
docker compose exec -T backend python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/health')" >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [INFO] Backend needs rebuild to sync dependencies. Rebuilding...
    docker compose up -d --build
)

echo [3/4] Ensuring database schema and rate quality are synchronized...
ping 127.0.0.1 -n 3 >nul
docker compose exec -T backend alembic upgrade head >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    docker compose exec -T backend alembic stamp head >nul 2>&1
)
docker compose exec -T backend python -m app.scripts.clean_noise_and_recalc >nul 2>&1

echo [4/4] System is healthy and operational!
echo.
echo =====================================================================
echo  APPLICATION READY AT:
echo    Local PC:    http://localhost:8080
echo =====================================================================
echo.
powershell -NoProfile -ExecutionPolicy Bypass -File "scripts\get_lan_ip.ps1"
echo.

:: Automatically open default browser
start http://localhost:8080

echo Press any key to close this launcher window (containers keep running in background).
pause >nul
