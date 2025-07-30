@echo off
echo.
echo ================================================================
echo  LUMEN PREDICTIVE MAINTENANCE DASHBOARD
echo ================================================================
echo  Starting the reactive dashboard with Lumen branding...
echo  Dashboard will open automatically in your default browser
echo ================================================================
echo.

REM Change to the script directory
cd /d "%~dp0"

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python and try again
    pause
    exit /b 1
)

REM Launch the dashboard
echo Starting dashboard server...
python launch_dashboard.py

echo.
echo Dashboard has been stopped.
pause
