@echo off
REM APL Migration Platform - Full Stack Startup (Windows)
REM ============================================================

setlocal enabledelayedexpansion

color 0A
cls

echo.
echo ======================================================================
echo  APL Migration Platform - Full Stack Startup
echo ======================================================================
echo.

REM Check if .env exists
if not exist .env (
    echo [SETUP] Creating .env from .env.example...
    copy .env.example .env > nul
    echo [OK] .env file created
    echo.
)

REM Install backend dependencies
echo [STEP 1] Installing Backend Dependencies
echo ======================================================================
pip install -r backend\requirements.txt
if errorlevel 1 (
    echo [ERROR] Failed to install backend dependencies
    pause
    exit /b 1
)
echo [OK] Backend dependencies installed
echo.

REM Install frontend dependencies
echo [STEP 2] Installing Frontend Dependencies
echo ======================================================================
call npm install
if errorlevel 1 (
    echo [ERROR] Failed to install frontend dependencies
    pause
    exit /b 1
)
echo [OK] Frontend dependencies installed
echo.

REM Start backend
echo [STEP 3] Starting Backend Server on port 8000
echo ======================================================================
start "APL Backend" cmd /k "cd backend && python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload"
echo [OK] Backend started in new window
timeout /t 3 /nobreak

REM Start frontend
echo [STEP 4] Starting Frontend Server on port 3000
echo ======================================================================
start "APL Frontend" cmd /k "npm run dev"
echo [OK] Frontend started in new window
timeout /t 2 /nobreak

echo.
echo ======================================================================
echo [SUCCESS] SYSTEM ONLINE
echo ======================================================================
echo.
echo URLs:
echo   Frontend:   http://localhost:3000
echo   Backend:    http://localhost:8000
echo   API Docs:   http://localhost:8000/docs
echo.
echo Configuration:
for /f "tokens=2 delims==" %%a in ('findstr "^AI_MODE=" .env') do echo   Mode:        %%a
for /f "tokens=2 delims==" %%a in ('findstr "^AI_PROVIDER=" .env') do echo   Provider:    %%a
echo.
echo Backend and Frontend windows are open.
echo Close windows or press Ctrl+C to stop services.
echo.

REM Keep this window open
pause
