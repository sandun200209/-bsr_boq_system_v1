@echo off
echo =====================================================================
echo  Restarting BSR Rate Hub Containers...
echo =====================================================================

cd /d "%~dp0\.."
docker compose restart

echo.
echo All services restarted successfully!
echo Web App: http://localhost:8080
echo.
pause
