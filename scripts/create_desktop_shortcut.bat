@echo off
setlocal enabledelayedexpansion

echo =====================================================================
echo  Creating BSR Rate Hub Windows Desktop Shortcut...
echo =====================================================================

cd /d "%~dp0\.."

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0create_shortcut.ps1" -ProjectDir "%CD%"
if %ERRORLEVEL% NEQ 0 (
    echo [WARNING] PowerShell shortcut creation encountered an issue.
)

echo.
echo You can now launch BSR Rate Hub directly from your Windows Desktop!
echo.
pause
