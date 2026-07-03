@echo off
SETLOCAL ENABLEDELAYEDEXPANSION
title Open WebUI - Dev Launcher

echo.
echo  ========================================
echo   Open WebUI - Development Launcher
echo  ========================================
echo.

SET "ROOT_DIR=%~dp0"
cd /d "%ROOT_DIR%" || (
    echo [ERROR] Cannot cd to %ROOT_DIR%
    pause
    exit /b 1
)

if "%BACKEND_PORT%"=="" set BACKEND_PORT=8080
if "%FRONTEND_PORT%"=="" set FRONTEND_PORT=5173

echo  Backend  : http://localhost:%BACKEND_PORT%
echo  Frontend : http://localhost:%FRONTEND_PORT%
echo.

where python >nul 2>&1 || (
    echo [ERROR] Python not found.
    pause
    exit /b 1
)

:: Use Python 3.11 venv if available, otherwise fall back to system python
set "VENV_PYTHON=%ROOT_DIR%backend\.venv\Scripts\python.exe"
if exist "%VENV_PYTHON%" (
    echo [INFO] Using Python 3.11 venv: %VENV_PYTHON%
    set "PYTHON_CMD=%VENV_PYTHON%"
    set "PIP_CMD=%ROOT_DIR%backend\.venv\Scripts\pip.exe"
) else (
    echo [INFO] No .venv found, using system python
    set "PYTHON_CMD=python"
    set "PIP_CMD=pip"
)

where node >nul 2>&1 || (
    echo [ERROR] Node.js not found.
    pause
    exit /b 1
)

if not exist "node_modules" (
    echo [INFO] Installing frontend dependencies...
    call npm install
    if !ERRORLEVEL! NEQ 0 (
        echo [ERROR] npm install failed.
        pause
        exit /b 1
    )
    echo.
)

%PIP_CMD% show uvicorn >nul 2>&1 || (
    echo [INFO] Installing backend dependencies...
    %PIP_CMD% install -r backend\requirements.txt
    if !ERRORLEVEL! NEQ 0 (
        echo [ERROR] pip install failed.
        pause
        exit /b 1
    )
    echo.
)

if /i "%WEB_LOADER_ENGINE%"=="playwright" (
    if "%PLAYWRIGHT_WS_URL%"=="" (
        echo [INFO] Installing Playwright browsers...
        playwright install chromium
        playwright install-deps chromium
    )
    %PYTHON_CMD% -c "import nltk; nltk.download('punkt_tab')"
)

set "KEY_FILE=backend\.webui_secret_key"
if not "%WEBUI_SECRET_KEY_FILE%"=="" set "KEY_FILE=%WEBUI_SECRET_KEY_FILE%"

if not defined WEBUI_SECRET_KEY (
    if not exist "%KEY_FILE%" (
        echo [INFO] Generating WEBUI_SECRET_KEY...
        %PYTHON_CMD% -c "import secrets; open(r'%KEY_FILE%','w').write(secrets.token_hex(32))"
    )
    set /p WEBUI_SECRET_KEY=<%KEY_FILE%
)

set CORS_ALLOW_ORIGIN=http://localhost:%FRONTEND_PORT%;http://localhost:%BACKEND_PORT%
set HOST=0.0.0.0
set PORT=%BACKEND_PORT%
if "%FORWARDED_ALLOW_IPS%"=="" set "FORWARDED_ALLOW_IPS='*'"
if "%UVICORN_WORKERS%"=="" set UVICORN_WORKERS=1

:: Default admin account for dev (only created if no users exist)
if "%WEBUI_ADMIN_EMAIL%"=="" set WEBUI_ADMIN_EMAIL=admin@dev.local
if "%WEBUI_ADMIN_PASSWORD%"=="" set WEBUI_ADMIN_PASSWORD=admin

echo [1/2] Starting backend on port %BACKEND_PORT% ...
echo [2/2] Starting frontend on port %FRONTEND_PORT% ...
echo.
echo  Press Ctrl+C to stop. Close the windows to exit.
echo  ========================================
echo.

:: Determine uvicorn command: use venv's uvicorn if available, else system
set "VENV_DIR=%ROOT_DIR%backend\.venv"
if exist "%VENV_DIR%\Scripts\uvicorn.exe" (
    set "UVICORN_CMD=%VENV_DIR%\Scripts\python.exe -m uvicorn"
) else (
    set "UVICORN_CMD=uvicorn"
)

start "Open WebUI Backend" cmd /c "cd /d %ROOT_DIR%backend && set CORS_ALLOW_ORIGIN=%CORS_ALLOW_ORIGIN% && set HOST=%HOST% && set PORT=%PORT% && set WEBUI_SECRET_KEY=%WEBUI_SECRET_KEY% && set FORWARDED_ALLOW_IPS=%FORWARDED_ALLOW_IPS% && set WEBUI_ADMIN_EMAIL=%WEBUI_ADMIN_EMAIL% && set WEBUI_ADMIN_PASSWORD=%WEBUI_ADMIN_PASSWORD% && %UVICORN_CMD% open_webui.main:app --host 0.0.0.0 --port %BACKEND_PORT% --forwarded-allow-ips %FORWARDED_ALLOW_IPS% --workers %UVICORN_WORKERS% --reload --ws auto"

timeout /t 3 /nobreak >nul

start "Open WebUI Frontend" cmd /c "cd /d %ROOT_DIR% && npm run dev:fast -- --port %FRONTEND_PORT%"

echo.
echo  Both servers launched.
echo  Frontend: http://localhost:%FRONTEND_PORT%
echo  Backend:  http://localhost:%BACKEND_PORT%
echo  PM Page:  http://localhost:%FRONTEND_PORT%/pm
echo.

timeout /t 2 /nobreak >nul
start http://localhost:%FRONTEND_PORT%

pause
