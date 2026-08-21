@echo off
setlocal

rem =====================================================================
rem  EDIT THESE TWO LINES so they match where you cloned the project
rem  and where you created the virtual environment.
rem =====================================================================
set PROJECT_DIR=C:\Users\LEGION\Desktop\AI-BrandPilot-main\AI-BrandPilot\AI-BrandPilot
set VENV_DIR=%PROJECT_DIR%\.venv
rem =====================================================================

if not exist "%PROJECT_DIR%\logs" mkdir "%PROJECT_DIR%\logs"

cd /d "%PROJECT_DIR%"
call "%VENV_DIR%\Scripts\activate.bat"
python scheduler.py >> "%PROJECT_DIR%\logs\scheduler.log" 2>&1

endlocal
