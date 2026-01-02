@echo off
REM Start Risk Runners development server on Windows

echo 🚀 Starting Risk Runners development server...

REM Update cache-busting parameters for JavaScript files
echo 🔄 Updating cache-busting parameters...
python --version >nul 2>&1
if %errorlevel% == 0 (
    python update-cache-busting.py
) else (
    echo ⚠️  Python not found - skipping cache-busting update
)

echo.

REM Check if Python is available
python --version >nul 2>&1
if %errorlevel% == 0 (
    python serve.py
) else (
    echo ❌ Python is not installed or not in PATH
    echo Please install Python 3 to run the development server
    pause
    exit /b 1
)