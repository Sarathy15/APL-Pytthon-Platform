@echo off
REM Benchmark Test Runner for APL-to-Python Migration Platform (Windows)
REM This batch file runs the comprehensive benchmark suite

setlocal enabledelayedexpansion

echo.
echo ============================================================================
echo APL-to-Python Migration Platform - Benchmark Suite
echo ============================================================================
echo.

REM Get the directory where this script is located
set SCRIPT_DIR=%~dp0
set PROJECT_ROOT=%SCRIPT_DIR%..\..\..

echo Project Root: %PROJECT_ROOT%
echo Benchmark Directory: %SCRIPT_DIR%
echo.

REM Check if Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ and try again
    pause
    exit /b 1
)

REM Verify benchmark directory exists
if not exist "%SCRIPT_DIR%01_sum.apl" (
    echo ERROR: Benchmark APL files not found
    echo Expected: %SCRIPT_DIR%01_sum.apl
    pause
    exit /b 1
)

REM Run the benchmark runner
echo Running benchmark suite...
echo.

python "%SCRIPT_DIR%benchmark_runner.py"

if %errorlevel% neq 0 (
    echo.
    echo ERROR: Benchmark runner failed with exit code %errorlevel%
    pause
    exit /b %errorlevel%
)

echo.
echo ============================================================================
echo Benchmark completed successfully!
echo Results saved to: outputs\benchmark_results\
echo ============================================================================
echo.

pause
