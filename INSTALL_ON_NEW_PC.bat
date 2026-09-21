@echo off
setlocal enabledelayedexpansion

title BSR Rate Hub - Setup & Installer for Windows

echo =====================================================================
echo  BSR Rate Hub - Sri Lanka BOQ Data System
echo  Setup ^& Installation Wizard for Any Windows PC or Laptop
echo =====================================================================
echo.
echo  This wizard will automatically configure and launch the BSR Rate Hub
echo  on this PC or laptop.
echo.

cd /d "%~dp0"

:: -------------------------------------------------------------------
:: Step 1: Check Docker Desktop Installation & Status
:: -------------------------------------------------------------------
echo [Step 1/6] Checking Docker Desktop status...

docker info >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [SUCCESS] Docker Desktop engine is running and ready.
    goto DOCKER_OK
)

:: Docker is not running. Is it installed?
set "DOCKER_EXE="
if exist "C:\Program Files\Docker\Docker\Docker Desktop.exe" (
    set "DOCKER_EXE=C:\Program Files\Docker\Docker\Docker Desktop.exe"
) else if exist "%LOCALAPPDATA%\Programs\Docker\Docker\Docker Desktop.exe" (
    set "DOCKER_EXE=%LOCALAPPDATA%\Programs\Docker\Docker\Docker Desktop.exe"
)

if "%DOCKER_EXE%"=="" goto DOCKER_NOT_INSTALLED

echo [INFO] Docker Desktop is installed but not started.
echo Launching Docker Desktop in the background...
start "" "%DOCKER_EXE%"

echo Waiting for Docker Desktop engine to initialize (up to 90 seconds)...
set WAITED=0

:WAIT_DOCKER_LOOP
ping 127.0.0.1 -n 4 >nul
docker info >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [SUCCESS] Docker Desktop is now running!
    goto DOCKER_OK
)
set /a WAITED+=3
echo   Initializing engine... (!WAITED!s)
if !WAITED! GEQ 90 (
    echo.
    echo [ERROR] Docker Desktop engine took longer than 90 seconds to respond.
    echo Please look at your Windows system tray (near the clock) for Docker Desktop.
    echo Wait until the whale icon shows 'Engine running', then run this setup again.
    echo.
    pause
    exit /b 1
)
goto WAIT_DOCKER_LOOP

:DOCKER_NOT_INSTALLED
:: Docker Desktop is not installed
echo =====================================================================
echo [ATTENTION] Docker Desktop is not installed on this PC or laptop!
echo =====================================================================
echo Docker is required to run the secure PostgreSQL database, FastAPI engine,
echo and Nginx web server on Windows.
echo.
echo Please choose an option:
echo   [1] Automatically download Docker Desktop Installer (~550 MB)
echo   [2] Open the official Docker Desktop website in browser
echo   [3] Exit installer
echo.
set /p DOCKER_CHOICE="Enter your choice (1, 2, or 3): "

if "%DOCKER_CHOICE%"=="1" (
    echo.
    echo Downloading Docker Desktop Installer to your Temp folder...
    echo (This may take 2-5 minutes depending on your internet connection)
    powershell -NoProfile -Command ^
        "$url = 'https://desktop.docker.com/win/main/amd64/Docker%20Desktop%20Installer.exe';" ^
        "$out = Join-Path $env:TEMP 'DockerDesktopInstaller.exe';" ^
        "Write-Host 'Downloading from:' $url -ForegroundColor Cyan;" ^
        "Invoke-WebRequest -Uri $url -OutFile $out;" ^
        "Write-Host '[SUCCESS] Download complete! Launching installer...' -ForegroundColor Green;" ^
        "Start-Process $out -Wait;"
    
    echo.
    echo =====================================================================
    echo Docker Desktop installation has completed!
    echo NOTE: If prompted by Windows, you may need to restart your PC,
    echo or ensure WSL2 is enabled (open CMD and run: wsl --install).
    echo.
    echo Once Docker Desktop is running (green whale icon), run this script again!
    echo =====================================================================
    pause
    exit /b 0
)

if "%DOCKER_CHOICE%"=="2" (
    start https://www.docker.com/products/docker-desktop/
    echo.
    echo Webpage opened. Please download and install Docker Desktop for Windows.
    echo After installation, launch Docker Desktop and run this setup script again.
    pause
    exit /b 0
)

echo Setup cancelled.
pause
exit /b 0

:DOCKER_OK

:: -------------------------------------------------------------------
:: Step 2: Storage & Environment Setup
:: -------------------------------------------------------------------
echo.
echo [Step 2/6] Preparing data storage and configuration...
if not exist "data\uploads" mkdir "data\uploads"
if not exist "data\backups" mkdir "data\backups"

if not exist ".env" (
    if exist ".env.example" (
        copy ".env.example" ".env" >nul
        echo       Created .env from .env.example
    )
)

:: Check if offline bundle exists
set USE_OFFLINE=0
if exist "offline_bundle\docker_images.tar" (
    echo.
    echo Found offline container bundle in 'offline_bundle\'!
    set /p OFFLINE_CHOICE="Do you want to use fast offline install (zero internet needed)? (Y/N) [Default: Y]: "
    if /i not "!OFFLINE_CHOICE!"=="N" (
        set USE_OFFLINE=1
    )
)

:: -------------------------------------------------------------------
:: Step 3: Deploy & Start Containers
:: -------------------------------------------------------------------
echo.
echo [Step 3/6] Starting application services...

if "!USE_OFFLINE!"=="1" (
    echo Loading pre-built images from offline bundle...
    docker load -i "offline_bundle\docker_images.tar"
    if exist "offline_bundle\uploads" (
        xcopy /E /I /Q /Y "offline_bundle\uploads" "data\uploads" >nul 2>&1
    )
    docker compose up -d
) else (
    echo Building and launching Docker containers (PostgreSQL, FastAPI, Nginx)...
    docker compose up -d --build
)

if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Failed to start Docker services!
    pause
    exit /b 1
)

:: -------------------------------------------------------------------
:: Step 4: Synchronize Database Schema & Seed Data
:: -------------------------------------------------------------------
echo.
echo [Step 4/6] Synchronizing database tables and rate catalogues...
timeout /t 3 /nobreak >nul

if "!USE_OFFLINE!"=="1" (
    if exist "offline_bundle\seed_database.sql" (
        echo Restoring seed rates from offline package...
        docker compose exec -T postgres psql -U bsr_user -d bsr_boq < "offline_bundle\seed_database.sql" >nul 2>&1
    )
)

docker compose exec -T backend alembic upgrade head >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    docker compose exec -T backend alembic stamp head >nul 2>&1
)
docker compose exec -T backend python -m app.scripts.clean_noise_and_recalc >nul 2>&1

:: -------------------------------------------------------------------
:: Step 5: Create Windows Desktop Shortcut
:: -------------------------------------------------------------------
echo.
echo [Step 5/6] Creating Windows Desktop Shortcut...
powershell -NoProfile -ExecutionPolicy Bypass -File "scripts\create_shortcut.ps1" -ProjectDir "%CD%" >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [SUCCESS] Shortcut 'BSR Rate Hub' placed on your Windows Desktop!
)

:: -------------------------------------------------------------------
:: Step 6: Configure Office LAN / Wi-Fi Firewall Access
:: -------------------------------------------------------------------
echo.
echo [Step 6/6] Office Network / LAN Access...
set /p FIREWALL_CHOICE="Allow other laptops and PCs on your office Wi-Fi to access this system? (Y/N) [Default: Y]: "
if /i not "%FIREWALL_CHOICE%"=="N" (
    call "%~dp0allow_firewall_lan.bat"
)

echo.
echo =====================================================================
echo  INSTALLATION SUCCESSFUL! BSR RATE HUB IS RUNNING!
echo =====================================================================
echo.
echo  Access from this PC / laptop:
echo    http://localhost:8080
echo.
powershell -NoProfile -ExecutionPolicy Bypass -File "scripts\get_lan_ip.ps1"
echo.
echo  To start the app anytime in the future, just double-click
echo  the 'BSR Rate Hub' shortcut on your Desktop!
echo =====================================================================
echo.
echo Opening browser...
start http://localhost:8080

echo.
echo Setup completed. Press any key to close this installer window.
pause >nul
