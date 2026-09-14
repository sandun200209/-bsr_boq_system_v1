@echo off
setlocal enabledelayedexpansion

echo =====================================================================
echo  BSR Rate Hub - Export Data ^& Document Updates
echo =====================================================================
echo.

cd /d "%~dp0"

python "%~dp0scripts\export_data_update.py"

echo.
pause
