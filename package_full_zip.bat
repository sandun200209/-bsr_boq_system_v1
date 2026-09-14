@echo off
setlocal enabledelayedexpansion

echo =====================================================================
echo  BSR Rate Hub - Build Full Complete Installation Pack ZIP
echo =====================================================================
echo.

cd /d "%~dp0"

:: First verify offline bundle exists
if not exist "offline_bundle\docker_images.tar" (
    echo [INFO] Offline bundle not detected. Building offline package first...
    call "%~dp0export_offline_package.bat"
)

python "%~dp0scripts\package_full_zip.py"

echo.
pause
