@echo off
setlocal enabledelayedexpansion

cd /d "%~dp0\.."

:: Generate timestamp formatted as YYYYMMDD_HHMMSS using PowerShell (works on all Windows 10/11)
for /f %%I in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd_HHmmss"') do set TIMESTAMP=%%I

if "%TIMESTAMP%"=="" set TIMESTAMP=%date:~-4%%date:~4,2%%date:~7,2%_%time:~0,2%%time:~3,2%%time:~6,2%
set TIMESTAMP=%TIMESTAMP: =0%

set BACKUP_DIR=data\backups\backup_%TIMESTAMP%
mkdir "%BACKUP_DIR%"
mkdir "%BACKUP_DIR%\uploads"

echo =====================================================================
echo  Backing up BSR Rate Hub Database and Uploaded Documents...
echo  Target: %BACKUP_DIR%
echo =====================================================================

:: 1. Dump PostgreSQL database
echo [1/2] Exporting PostgreSQL database dump (bsr_boq)...
docker compose exec -T postgres pg_dump -U bsr_user -d bsr_boq > "%BACKUP_DIR%\database.sql"
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Failed to dump PostgreSQL database!
    pause
    exit /b 1
)

:: 2. Copy uploaded source files
echo [2/2] Archiving uploaded source documents...
if exist "data\uploads" (
    xcopy /E /I /Q /Y "data\uploads" "%BACKUP_DIR%\uploads" >nul
)

echo.
echo =====================================================================
echo  BACKUP COMPLETED SUCCESSFULLY!
echo  Location: %BACKUP_DIR%
echo  Contents:
echo    - %BACKUP_DIR%\database.sql
echo    - %BACKUP_DIR%\uploads\
echo =====================================================================
echo.
pause
