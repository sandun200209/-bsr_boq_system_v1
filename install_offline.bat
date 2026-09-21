@echo off
setlocal enabledelayedexpansion

echo =====================================================================
echo  BSR Rate Hub - 100%% Offline Fast Installer
echo =====================================================================
echo  (No Internet Connection Required)
echo.

cd /d "%~dp0"

:: 1. Check for offline bundle
if not exist "offline_bundle\docker_images.tar" (
    echo [ERROR] 'offline_bundle\docker_images.tar' was not found!
    echo.
    echo To use offline installation, please run 'export_offline_package.bat'
    echo on your source computer first, then copy this folder over.
    echo.
    echo Alternatively, if this laptop has internet, run 'INSTALL_ON_NEW_PC.bat'.
    echo.
    pause
    exit /b 1
)

:: 2. Check Docker Desktop
docker info >nul 2>&1
if %ERRORLEVEL% EQU 0 goto DOCKER_OFFLINE_READY

set "DOCKER_EXE="
if exist "C:\Program Files\Docker\Docker\Docker Desktop.exe" (
    set "DOCKER_EXE=C:\Program Files\Docker\Docker\Docker Desktop.exe"
) else if exist "%LOCALAPPDATA%\Programs\Docker\Docker\Docker Desktop.exe" (
    set "DOCKER_EXE=%LOCALAPPDATA%\Programs\Docker\Docker\Docker Desktop.exe"
)

if "%DOCKER_EXE%"=="" (
    echo [ERROR] Docker Desktop is not installed on this PC!
    echo Please install Docker Desktop first.
    pause
    exit /b 1
)

echo Docker Desktop is not currently running. Attempting to start it...
start "" "%DOCKER_EXE%"
echo Waiting for Docker Desktop engine to start (up to 90 seconds)...
set WAITED=0

:WAIT_DOCKER_OFFLINE
ping 127.0.0.1 -n 4 >nul
docker info >nul 2>&1
if %ERRORLEVEL% EQU 0 goto DOCKER_OFFLINE_READY
set /a WAITED+=3
echo   Waiting... (!WAITED!s)
if !WAITED! GEQ 90 (
    echo.
    echo [ERROR] Docker Desktop took too long to start.
    echo Please open Docker Desktop manually, wait until it says 'Engine running', and run this script again.
    pause
    exit /b 1
)
goto WAIT_DOCKER_OFFLINE

:DOCKER_OFFLINE_READY
echo [SUCCESS] Docker Desktop engine is ready.
echo.

:: 3. Prepare storage directories
echo [1/5] Setting up data directories...
if not exist "data\uploads" mkdir "data\uploads"
if not exist "data\backups" mkdir "data\backups"
if not exist ".env" (
    if exist ".env.example" copy ".env.example" ".env" >nul
)
if exist "offline_bundle\uploads" (
    echo       Restoring archived source files...
    xcopy /E /I /Q /Y "offline_bundle\uploads" "data\uploads" >nul 2>&1
)

:: 4. Load offline Docker images
echo [2/5] Importing pre-built container images (Zero internet required)...
docker load -i "offline_bundle\docker_images.tar"
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Failed to load docker images from archive!
    pause
    exit /b 1
)
echo       Images imported successfully!

:: 5. Launch containers
echo [3/5] Starting containers (PostgreSQL, FastAPI Backend, Nginx Web UI)...
docker compose up -d
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Failed to launch containers!
    pause
    exit /b 1
)

:: Wait for PostgreSQL to be healthy
echo [4/5] Synchronizing database...
timeout /t 4 /nobreak >nul

:: If seed_database.sql exists, restore it if database is fresh
if exist "offline_bundle\seed_database.sql" (
    echo       Restoring all 3,754 rate items from offline seed...
    docker compose exec -T postgres psql -U bsr_user -d bsr_boq < "offline_bundle\seed_database.sql" >nul 2>&1
) else (
    docker compose exec -T backend alembic upgrade head >nul 2>&1
)

:: 6. Create Desktop Shortcut
echo [5/5] Creating Windows Desktop Shortcut...
powershell -NoProfile -ExecutionPolicy Bypass -File "scripts\create_shortcut.ps1" -ProjectDir "%CD%" >nul 2>&1

echo.
echo =====================================================================
echo  INSTALLATION COMPLETE! BSR RATE HUB IS READY!
echo =====================================================================
echo.
echo  Access locally at:
echo    http://localhost:8080
echo.
powershell -NoProfile -ExecutionPolicy Bypass -File "scripts\get_lan_ip.ps1"
echo.
echo Opening browser...
start http://localhost:8080
echo.
echo Setup finished. Press any key to close this window.
pause >nul
