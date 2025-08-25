@echo off
echo.
echo ========================================
echo    FaceScannerPro - People Tracking
echo ========================================
echo.

cd /d "%~dp0"

echo Checking virtual environment...
if not exist ".venv" (
    echo Creating virtual environment...
    python -m venv .venv
    echo Virtual environment created.
)

echo Activating virtual environment...
call .venv\Scripts\activate.bat

echo.
echo Checking dependencies...
python -c "import cv2, flask, numpy" 2>nul
if errorlevel 1 (
    echo Installing required packages...
    pip install Flask opencv-python numpy
)

echo.
echo Testing setup...
python test_minimal.py
if errorlevel 1 (
    echo.
    echo ❌ Setup test failed. Please check the errors above.
    pause
    exit /b 1
)

echo.
echo ✅ All checks passed!
echo.
echo Starting FaceScannerPro...
echo Access the dashboard at: http://localhost:8080
echo Press Ctrl+C to stop the application
echo.

python minimal_app.py

echo.
echo Application stopped.
pause
