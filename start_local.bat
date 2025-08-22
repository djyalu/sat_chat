@echo off
echo =====================================
echo    SatChat Local Test Environment
echo =====================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://www.python.org
    pause
    exit /b 1
)

REM Check if backend is running
netstat -an | findstr :8000 | findstr LISTENING >nul
if %errorlevel% equ 0 (
    echo [OK] Backend server is already running on port 8000
) else (
    echo [INFO] Starting backend server...
    start /b python test_app.py
    timeout /t 2 /nobreak >nul
)

echo.
echo =====================================
echo    System Ready!
echo =====================================
echo.
echo Test Options:
echo.
echo 1. Open in browser:
echo    - index.html (Full React-like UI)
echo    - test.html (API Tester)
echo.
echo 2. API Endpoints:
echo    - http://localhost:8000
echo    - http://localhost:8000/docs
echo.
echo Press any key to open index.html in your browser...
pause >nul

start index.html

echo.
echo Server is running. Press Ctrl+C to stop.
pause >nul