@echo off
setlocal enabledelayedexpansion
set PROJECT_DIR=%~dp0
pushd !PROJECT_DIR!
title RadioManager - Local Deployment

echo ================================================
echo   RadioManager - Local Deployment (SQLite)
echo ================================================
echo.

:: Python
set PY_CMD=
python --version >/dev/null 2>&1
if %errorlevel% equ 0 (set PY_CMD=python & goto :PY_FOUND)
py --version >/dev/null 2>&1
if %errorlevel% equ 0 (set PY_CMD=py & goto :PY_FOUND)
echo [ERROR] Python not found. Install from https://www.python.org/
pause & exit /b 1

:PY_FOUND
for /f "delims=" %%v in ('%PY_CMD% --version') do set PY_VERSION=%%v
echo [OK] Python: %PY_CMD% - %PY_VERSION%

:: Node
node --version >/dev/null 2>&1
if %errorlevel% neq 0 (echo [ERROR] Node.js not found & pause & exit /b 1)
for /f "delims=" %%v in ('node --version') do set NODE_VERSION=%%v
echo [OK] Node.js: %NODE_VERSION%
echo.

:: Check dirs
if not exist "!PROJECT_DIR!backend" (echo [ERROR] Missing backend dir: !PROJECT_DIR!backend & pause & exit /b 1)
if not exist "!PROJECT_DIR!frontend" (echo [ERROR] Missing frontend dir: !PROJECT_DIR!frontend & pause & exit /b 1)
if not exist "!PROJECT_DIR!backend\logs" mkdir "!PROJECT_DIR!backend\logs"
if not exist "!PROJECT_DIR!backend\uploads" mkdir "!PROJECT_DIR!backend\uploads"

:: Step 1: Database
echo.
echo [1/4] Initializing database...
pushd "!PROJECT_DIR!backend"

set USE_VENV=1
if not exist venv (
    echo   Creating Python virtual environment...
    %PY_CMD% -m venv venv
    if !errorlevel! neq 0 (
        echo   [INFO] venv creation failed - will use system Python
        set USE_VENV=0
    )
)
if !USE_VENV! equ 1 (
    if exist venv\Scripts\activate.bat (
        echo   Activating virtual environment...
        call venv\Scripts\activate.bat
    )
)
echo   Installing Python dependencies (this may take a while)...
%PY_CMD% -m pip install -r requirements.txt
if !errorlevel! neq 0 (echo [ERROR] pip install failed & popd & pause & exit /b 1)
%PY_CMD% -m app.scripts.init_db
if !errorlevel! neq 0 (echo [ERROR] Database init failed & popd & pause & exit /b 1)
popd

:: Step 2: Backend
echo.
echo [2/4] Starting backend on port 8000...
if exist "!PROJECT_DIR!backend\venv\Scripts\python.exe" (
    set "PY_EXE=!PROJECT_DIR!backend\venv\Scripts\python.exe"
) else (
    echo   [INFO] venv not available, using system python
    set "PY_EXE=python"
)
(
echo @echo off
echo cd /d "!PROJECT_DIR!backend"
echo "!PY_EXE!" -m uvicorn app.main:app --host 0.0.0.0 --port 8000
echo pause
) > "%TEMP%\radiomanager_backend.bat"
start "RadioManager-Backend" cmd /k "%TEMP%\radiomanager_backend.bat"
echo   Waiting for backend (up to 15 seconds)...
set WAIT_MAX=15
set /a WAIT_COUNT=0

:BACKEND_WAIT
timeout /t 1 /nobreak >/dev/null
set /a WAIT_COUNT+=1
powershell -NoProfile -NonInteractive -Command "try { $r = Invoke-WebRequest -Uri 'http://localhost:8000/health' -UseBasicParsing -TimeoutSec 1; if ($r.StatusCode -eq 200) { exit 0 } else { exit 1 } } catch { exit 1 }" >/dev/null 2>&1
if !errorlevel! equ 0 (echo   [OK] Backend is running & goto :BACKEND_UP)
if %WAIT_COUNT% lss %WAIT_MAX% goto :BACKEND_WAIT
echo [WARN] Backend not responding - check RadioManager-Backend window.

:BACKEND_UP
echo.

:: Step 3: Frontend
echo [3/4] Building frontend...
echo   Project dir: !PROJECT_DIR!
if not exist "!PROJECT_DIR!frontend" (
    echo [ERROR] Frontend directory not found at: !PROJECT_DIR!frontend
    pause & exit /b 1
)
echo   OK - frontend directory exists

where npm >/dev/null 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] npm not found. Install Node.js from https://nodejs.org/
    pause & exit /b 1
)
echo   OK - npm found

cd /d "!PROJECT_DIR!frontend"
echo   Current directory: !CD!
echo   Installing frontend dependencies...
call npm install
if !errorlevel! neq 0 (
    echo [ERROR] npm install failed
    pause & exit /b 1
)
echo.
echo   Building frontend...
call npm run build
if !errorlevel! neq 0 (
    echo [ERROR] Frontend build failed
    pause & exit /b 1
)

:: Step 4: Start
echo.
echo [4/4] Starting frontend...
(
echo @echo off
echo cd /d "!PROJECT_DIR!frontend"
echo npm run dev
) > "%TEMP%\radiomanager_frontend.bat"
start "RadioManager-Frontend" cmd /k "%TEMP%\radiomanager_frontend.bat"
echo   Frontend starting on http://localhost:5173

:DONE
echo.
echo ================================================
echo   RadioManager is running
echo   Frontend: http://localhost:5173
echo   Backend:  http://localhost:8000
echo ================================================
pause
endlocal
