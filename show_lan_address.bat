@echo off
setlocal enabledelayedexpansion

echo =====================================================================
echo  BSR Rate Hub - Office Network / LAN Address Finder
echo =====================================================================
echo.

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\get_lan_ip.ps1"

echo.
echo Tip: If colleagues on other PCs cannot load the page, run 'allow_firewall_lan.bat'
echo once on this PC to allow incoming network connections through Windows Firewall.
echo.
pause
