@echo off
setlocal enabledelayedexpansion

cd /d "%~dp0\.."

if "%~1"=="" (
    echo =====================================================================
    echo  BSR Rate Hub - Database Restore Tool
    echo =====================================================================
    echo.
    echo  Usage: restore_database.bat ^<path_to_database.sql^>
    echo  Example: restore_database.bat data\backups\backup_20260909_120000\database.sql
    echo.
    pause
    exit /b 1
)

set BACKUP_FILE=%~1
if not exist "%BACKUP_FILE%" (
    echo [ERROR] Backup file '%BACKUP_FILE%' does not exist!
    pause
    exit /b 1
)

echo =====================================================================
echo  Restoring BSR Database from: %BACKUP_FILE%
echo  WARNING: This will replace current database tables!
echo =====================================================================
set /p CONFIRM="Are you sure you want to proceed? (Y/N): "
if /i not "%CONFIRM%"=="Y" (
    echo Restore cancelled.
    pause
    exit /b 0
)

echo Restoring PostgreSQL database...
docker compose exec -T postgres psql -U bsr_user -d bsr_boq < "%BACKUP_FILE%"
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Database restore failed!
    pause
    exit /b 1
)

echo.
echo =====================================================================
echo  DATABASE RESTORED SUCCESSFULLY!
echo =====================================================================
echo.
pause
