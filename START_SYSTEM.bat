@echo off
chcp 65001 > nul 2>&1
title ex-GPT AI System Startup

echo ==========================================
echo    ex-GPT AI System - Quick Start
echo ==========================================

REM Check if .env exists
if not exist .env.example (
    echo [WARNING] .env.example not found
) else (
    if not exist .env (
        echo [INFO] Creating .env from .env.example...
        copy .env.example .env > nul 2>&1
        if exist .env (
            echo [OK] .env file created
        ) else (
            echo [ERROR] Failed to create .env file
        )
    )
)

REM Create necessary directories
if not exist logs mkdir logs
if not exist uploads mkdir uploads
if not exist temp mkdir temp
if not exist cache mkdir cache

echo.
echo [INFO] Checking system requirements...

REM Check Python
python --version > nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Please install Python 3.10+
    echo Press any key to exit...
    pause > nul
    exit /b 1
)
echo [OK] Python detected

REM Check for running processes on common ports
echo [INFO] Checking for running services...
netstat -an | find ":8201 " > nul 2>&1
if not errorlevel 1 (
    echo [INFO] Port 8201 is already in use - stopping existing service...
    for /f "tokens=5" %%a in ('netstat -ano ^| find ":8201 "') do (
        taskkill /F /PID %%a > nul 2>&1
    )
)

echo.
echo Select startup option:
echo 1) Quick Test Mode (Backend only)
echo 2) Full System (Backend + Frontend)
echo 3) Docker Mode (All services)
echo 4) Service Test Only
echo 5) Exit
echo.
set /p choice=Enter your choice [1-5]:

if "%choice%"=="1" goto quick_test
if "%choice%"=="2" goto full_system
if "%choice%"=="3" goto docker_mode
if "%choice%"=="4" goto service_test
if "%choice%"=="5" goto end
echo Invalid choice. Starting Quick Test Mode...
goto quick_test

:quick_test
echo.
echo ==========================================
echo      Quick Test Mode - Backend Only
echo ==========================================
echo [INFO] Starting backend API server...

REM Change to backend directory and start server
if exist backend\simple_test.py (
    cd /d backend
    echo [INFO] Backend directory found, starting server...
    start "ex-GPT Backend" cmd /k "python simple_test.py"
    cd /d ..
    echo [OK] Backend server started
) else (
    echo [ERROR] Backend files not found
    echo Looking for: backend\simple_test.py
    goto end
)

echo [INFO] Running service tests...
python test_services.py

echo.
echo [SUCCESS] Quick test completed!
echo Backend API: http://localhost:8201
echo API Docs: http://localhost:8201/docs
goto wait_end

:full_system
echo.
echo ==========================================
echo        Full System Mode
echo ==========================================

REM Check Node.js
node --version > nul 2>&1
if errorlevel 1 (
    echo [WARNING] Node.js not found. Starting backend only...
    goto quick_test
)
echo [OK] Node.js detected

echo [INFO] Starting backend API server...
if exist backend\simple_test.py (
    cd /d backend
    start "ex-GPT Backend" cmd /k "python simple_test.py"
    cd /d ..
    echo [OK] Backend started
) else (
    echo [ERROR] Backend files not found
    goto end
)

echo [INFO] Preparing frontend...
if exist frontend\package.json (
    cd /d frontend
    echo [INFO] Installing dependencies (this may take a moment)...
    npm install > install.log 2>&1
    if errorlevel 1 (
        echo [WARNING] npm install had issues, checking log...
        type install.log
    )

    echo [INFO] Starting frontend development server...
    start "ex-GPT Frontend" cmd /k "npm run dev"
    cd /d ..
    echo [OK] Frontend started
) else (
    echo [ERROR] Frontend package.json not found
)

echo [INFO] Waiting for services to start...
timeout /t 5 > nul 2>&1

echo.
echo [SUCCESS] Full system started!
echo Frontend: http://localhost:5173
echo Backend: http://localhost:8201
echo API Docs: http://localhost:8201/docs
goto wait_end

:docker_mode
echo.
echo ==========================================
echo           Docker Mode
echo ==========================================
docker --version > nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker not found. Please install Docker Desktop
    echo Falling back to local mode...
    goto full_system
)
echo [OK] Docker detected

echo [INFO] Starting Docker services...
docker-compose down > nul 2>&1
docker-compose up -d

echo [INFO] Waiting for services to initialize...
timeout /t 15 > nul 2>&1

echo [INFO] Checking service status...
docker-compose ps

echo.
echo [SUCCESS] Docker services started!
echo API Server: http://localhost:8080
echo Admin UI: http://localhost:5000
echo Qdrant: http://localhost:6333
echo MinIO Console: http://localhost:9001
goto wait_end

:service_test
echo.
echo ==========================================
echo        Service Test Mode
echo ==========================================
echo [INFO] Running comprehensive service tests...
python test_services.py

echo.
echo [INFO] Running project verification...
python verify_setup.py

echo.
echo [SUCCESS] Service tests completed!
goto wait_end

:wait_end
echo.
echo ==========================================
echo       Services Started Successfully
echo ==========================================
echo.
echo Useful commands:
echo   - Stop services: Close the opened windows
echo   - View logs: Check logs/ directory
echo   - Edit config: config/development.yaml
echo   - Docker stop: docker-compose down
echo.
echo Press any key to close this launcher...
pause > nul
goto end

:end
echo.
echo Goodbye!
timeout /t 2 > nul 2>&1