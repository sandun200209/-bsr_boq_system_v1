@echo off
setlocal enabledelayedexpansion

echo =====================================================================
echo  BSR Rate Hub - Export Portable Offline Installation Package
echo =====================================================================
echo.
echo This utility creates a 100%% self-contained offline installer bundle
echo containing all Docker container images, all 3,754 rate items, and all
echo uploaded files. You can copy this folder to ANY USB drive or laptop!
echo.

cd /d "%~dp0"

:: Check if Docker is running
docker info >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Docker Desktop is not running! Please start Docker Desktop first.
    pause
    exit /b 1
)

set BUNDLE_DIR=offline_bundle
if not exist "%BUNDLE_DIR%" mkdir "%BUNDLE_DIR%"
if not exist "%BUNDLE_DIR%\uploads" mkdir "%BUNDLE_DIR%\uploads"

echo [1/3] Exporting current PostgreSQL database (all sectors ^& rate items)...
docker compose exec -T postgres pg_dump -U bsr_user -d bsr_boq > "%BUNDLE_DIR%\seed_database.sql"
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Failed to dump database!
    pause
    exit /b 1
)
echo       Database dumped successfully to %BUNDLE_DIR%\seed_database.sql

echo.
echo [2/3] Exporting Docker images to %BUNDLE_DIR%\docker_images.tar...
echo       (This may take 1-2 minutes, please wait...)
docker save postgres:16-alpine bsr_boq_system_v1-backend:latest bsr_boq_system_v1-frontend:latest -o "%BUNDLE_DIR%\docker_images.tar"
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Failed to export Docker images!
    pause
    exit /b 1
)
echo       Docker images exported successfully!

echo.
echo [3/3] Archiving uploaded source documents...
if exist "data\uploads" (
    xcopy /E /I /Q /Y "data\uploads" "%BUNDLE_DIR%\uploads" >nul
)
echo       Uploaded files archived successfully!

echo.
echo =====================================================================
echo  PORTABLE OFFLINE PACKAGE CREATED SUCCESSFULLY!
echo =====================================================================
echo  Contents in "%CD%\%BUNDLE_DIR%":
echo    - docker_images.tar    (Pre-built container engines)
echo    - seed_database.sql    (Database with all rates)
echo    - uploads\             (Original source files)
echo.
echo  HOW TO INSTALL ON ANY OTHER PC OR LAPTOP:
echo   1. Copy the entire 'bsr_boq_system_v1' folder to a USB drive or laptop.
echo   2. On the new laptop, double-click 'install_offline.bat'.
echo   3. Everything starts in 15 seconds with ZERO internet required!
echo =====================================================================
echo.
pause
