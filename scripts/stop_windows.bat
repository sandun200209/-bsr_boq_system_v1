@echo off
echo =====================================================================
echo  Stopping BSR Rate Hub Containers...
echo =====================================================================

cd /d "%~dp0\.."
docker compose down

echo.
echo All BSR Rate Hub services have been gracefully stopped.
echo Your PostgreSQL data and uploaded documents remain safely preserved.
echo.
pause
