@echo off
setlocal enabledelayedexpansion

echo =====================================================================
echo  BSR Rate Hub - Import Data ^& Document Updates
echo =====================================================================
echo.

cd /d "%~dp0"

if "%~1"=="" (
    python "%~dp0scripts\import_data_update.py"
) else (
    python "%~dp0scripts\import_data_update.py" "%~1"
)

echo.
pause
