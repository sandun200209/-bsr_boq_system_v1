@echo off
setlocal enabledelayedexpansion

echo =====================================================================
echo  BSR Rate Hub - Connect from Another PC / Laptop (Office LAN)
echo =====================================================================
echo.
echo Use this script to connect to BSR Rate Hub running on another PC in your office.
echo.

set /p HOST_IP="Enter the IP address of the Host PC (e.g. 192.168.1.15): "

if "%HOST_IP%"=="" (
    echo [ERROR] No IP address provided!
    pause
    exit /b 1
)

set URL=http://%HOST_IP%:8080

echo.
echo Opening BSR Rate Hub at: %URL%
start %URL%

:: Create a desktop URL shortcut on this laptop
powershell -NoProfile -Command ^
    "$Desktop = [Environment]::GetFolderPath('Desktop');" ^
    "$ShortcutFile = Join-Path $Desktop 'BSR Rate Hub (Office LAN).url';" ^
    "'[InternetShortcut]' | Out-File -FilePath $ShortcutFile -Encoding ascii;" ^
    "'URL=%URL%' | Out-File -FilePath $ShortcutFile -Append -Encoding ascii;" ^
    "Write-Host '[SUCCESS] Created desktop shortcut: BSR Rate Hub (Office LAN)' -ForegroundColor Green;"

echo.
echo Connected successfully! You can now access BSR Rate Hub from your desktop.
echo.
pause
