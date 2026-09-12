@echo off
setlocal enabledelayedexpansion

echo =====================================================================
echo  BSR Rate Hub - Windows Defender Firewall LAN Configuration
echo =====================================================================
echo.

:: Check for administrative privileges
net session >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [INFO] Requesting Administrator privileges to add Windows Firewall rule...
    powershell -Command "Start-Process cmd -ArgumentList '/c \"\"%~dp0allow_firewall_lan.bat\"\"' -Verb runAs"
    exit /b 0
)

echo [1/2] Adding inbound firewall rules for BSR Rate Hub (Ports 8080 and 8085)...
netsh advfirewall firewall delete rule name="BSR Rate Hub (Port 8080)" >nul 2>&1
netsh advfirewall firewall add rule name="BSR Rate Hub (Port 8080)" dir=in action=allow protocol=TCP localport=8080 profile=any >nul 2>&1
netsh advfirewall firewall delete rule name="BSR Rate Hub (Port 8085)" >nul 2>&1
netsh advfirewall firewall add rule name="BSR Rate Hub (Port 8085)" dir=in action=allow protocol=TCP localport=8085 profile=any >nul 2>&1

if %ERRORLEVEL% EQU 0 (
    echo [SUCCESS] Windows Firewall rules configured successfully!
) else (
    echo [WARNING] Could not automatically configure firewall rule.
)

echo.
echo [2/2] Detecting your Office Network / Wi-Fi IP Address...
echo.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\get_lan_ip.ps1"

echo.
echo Press any key to close this window.
pause >nul
