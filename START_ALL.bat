@echo off
chcp 65001 > nul
REM ex-GPT 통합 시작 스크립트 - 모든 서비스 한번에 실행

echo ==========================================
echo    ex-GPT AI System - Quick Start
echo ==========================================

REM 환경 변수 체크
if not exist .env (
    echo [INFO] Creating .env from .env.example...
    copy .env.example .env > nul
    echo [OK] .env file created
)

REM 필요한 디렉토리 생성
if not exist logs mkdir logs
if not exist uploads mkdir uploads
if not exist temp mkdir temp
if not exist cache mkdir cache

echo.
echo [INFO] Checking system requirements...

REM Python 체크
python --version > nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Please install Python 3.10+
    pause
    exit /b 1
)
echo [OK] Python detected

REM 포트 체크 함수
echo [INFO] Checking available ports...
for %%p in (8200,8201,5173) do (
    netstat -an | find ":%%p " > nul
    if not errorlevel 1 (
        echo [WARNING] Port %%p is already in use
        echo [INFO] Attempting to stop existing services...
        for /f "tokens=5" %%a in ('netstat -ano ^| find ":%%p "') do (
            taskkill /F /PID %%a > nul 2>&1
        )
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

:quick_test
echo.
echo ==========================================
echo      Quick Test Mode - Backend Only
echo ==========================================
echo [INFO] Starting backend API server...
cd backend
start "ex-GPT Backend" cmd /k "python simple_test.py"
cd ..

echo [INFO] Running service tests...
python test_services.py

echo.
echo [SUCCESS] Quick test completed!
echo Backend API: http://localhost:8201
echo API Docs: http://localhost:8201/docs
goto end

:full_system
echo.
echo ==========================================
echo        Full System Mode
echo ==========================================

REM Node.js 체크
echo [INFO] Checking Node.js...
node --version > nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js not found. Please install Node.js 18+
    echo [INFO] Starting backend only...
    goto quick_test
)
echo [OK] Node.js detected

echo [INFO] Starting backend API server...
cd backend
start "ex-GPT Backend" cmd /k "python simple_test.py"
cd ..

echo [INFO] Installing frontend dependencies...
cd frontend
npm install > nul 2>&1
if errorlevel 1 (
    echo [WARNING] npm install failed, trying with existing packages
)

echo [INFO] Starting frontend development server...
start "ex-GPT Frontend" cmd /k "npm run dev"
cd ..

echo [INFO] Running system diagnostics...
timeout /t 3 > nul
powershell -ExecutionPolicy Bypass -File check_system.ps1

echo.
echo [SUCCESS] Full system started!
echo Frontend: http://localhost:5173
echo Backend: http://localhost:8201
echo API Docs: http://localhost:8201/docs
goto end

:docker_mode
echo.
echo ==========================================
echo           Docker Mode
echo ==========================================
echo [INFO] Checking Docker...
docker --version > nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker not found. Please install Docker Desktop
    echo [INFO] Falling back to local mode...
    goto full_system
)
echo [OK] Docker detected

echo [INFO] Starting Docker services...
docker-compose down > nul 2>&1
docker-compose up -d

echo [INFO] Waiting for services to start...
timeout /t 10 > nul

echo [INFO] Checking service status...
docker-compose ps

echo.
echo [SUCCESS] Docker services started!
echo API Server: http://localhost:8080
echo Admin UI: http://localhost:5000
echo Qdrant: http://localhost:6333
echo MinIO: http://localhost:9001
goto end

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
goto end

:end
echo.
echo ==========================================
echo       Startup Complete
echo ==========================================
echo.
echo Useful commands:
echo   - Stop all: Ctrl+C in each window
echo   - Logs: check logs/ directory
echo   - Config: edit config/development.yaml
echo   - Docker stop: docker-compose down
echo.
echo Press any key to close this window...
pause > nul