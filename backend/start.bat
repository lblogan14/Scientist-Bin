@echo off
REM ============================================================
REM  Scientist-Bin Backend — Windows Startup Script
REM ============================================================
REM  Prerequisites: Python 3.11+, uv (https://docs.astral.sh/uv/)
REM  Usage:  start.bat              (default: port 8000)
REM          start.bat --port 9000  (custom port)
REM ============================================================

setlocal

cd /d "%~dp0"

REM -- Parse optional --port argument (default 8000) --
set PORT=8000
:parse_args
if "%~1"=="" goto :done_args
if /i "%~1"=="--port" (
    set PORT=%~2
    shift
    shift
    goto :parse_args
)
shift
goto :parse_args
:done_args

REM -- Check for .env --
if not exist ".env" (
    if exist ".env.example" (
        echo [WARNING] No .env file found. Copying .env.example to .env
        echo           Please edit .env and set your GOOGLE_API_KEY.
        copy .env.example .env >nul
    ) else (
        echo [ERROR] No .env or .env.example found. Create a .env with GOOGLE_API_KEY.
        exit /b 1
    )
)

REM -- Install / sync dependencies --
echo [1/2] Syncing dependencies...
uv sync --all-groups
if %errorlevel% neq 0 (
    echo [ERROR] uv sync failed. Is uv installed?
    exit /b 1
)

REM -- Start the server --
echo [2/2] Starting Scientist-Bin backend on port %PORT%...
echo        API docs: http://localhost:%PORT%/docs
echo        Health:   http://localhost:%PORT%/api/v1/health
echo.
uv run uvicorn scientist_bin_backend.main:app --host 0.0.0.0 --port %PORT% --reload

endlocal
