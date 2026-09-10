@echo off
setlocal enabledelayedexpansion

echo =====================================================================
echo  BSR Rate Hub - Reset Database
echo =====================================================================
echo.
echo WARNING: This will permanently erase ALL uploaded documents, rates,
echo and review queue items from the database!
echo.
set /p CONFIRM="Are you sure you want to completely clean the database? (Y/N): "
if /i not "!CONFIRM!"=="Y" (
    echo Reset cancelled.
    pause
    exit /b 0
)

echo.
echo [1/3] Creating automatic safety backup before reset...
call "%~dp0backup_database.bat"

echo.
echo [2/3] Truncating all database tables...
docker compose exec -T backend python -c "from app.database import engine; from sqlalchemy import text; conn = engine.connect(); conn.execute(text('TRUNCATE TABLE rate_item_master_mapping, rate_items, master_items, import_jobs, source_files RESTART IDENTITY CASCADE;')); conn.commit(); conn.close(); print('Database tables truncated.')"

echo.
echo [3/3] Clearing uploads directory...
powershell -NoProfile -Command "if (Test-Path 'data\uploads') { Get-ChildItem -Path 'data\uploads' | Remove-Item -Recurse -Force }"

echo.
echo =====================================================================
echo  DATABASE HAS BEEN COMPLETELY RESET AND CLEANED!
echo  You can now upload fresh BSR documents in the Import Center.
echo =====================================================================
echo.
pause
