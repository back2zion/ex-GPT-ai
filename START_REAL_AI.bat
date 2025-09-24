@echo off
chcp 65001 > nul 2>&1
title ex-GPT Real AI System

echo ==========================================
echo   ex-GPT Real AI System Startup
echo ==========================================

echo.
echo [INFO] This will start the REAL AI system with:
echo - LLM (Qwen3-32B) for text processing
echo - VLM (BLIP-2, CLIP) for image analysis
echo - GPU acceleration (if available)
echo.
echo [WARNING] This requires:
echo - Docker Desktop running
echo - At least 8GB GPU memory
echo - High-end system (may be slow on CPU)
echo.

set /p choice=Do you want to continue? [Y/N]:

if /i "%choice%" neq "Y" (
    echo Cancelled by user
    goto end
)

echo.
echo [INFO] Checking Docker...
docker --version > nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker not found!
    echo Please install Docker Desktop first
    echo.
    echo Alternative: Use mock server for development
    echo   python backend\simple_test.py
    goto end
)
echo [OK] Docker detected

echo.
echo [INFO] Starting real AI services...
echo This may take several minutes to download models...

REM Stop any existing containers
docker-compose down > nul 2>&1

REM Start the full AI stack
docker-compose up -d

if errorlevel 1 (
    echo [ERROR] Failed to start AI services
    echo.
    echo Troubleshooting:
    echo 1. Check Docker Desktop is running
    echo 2. Check system has enough resources
    echo 3. Try: docker-compose logs
    echo.
    echo Fallback to mock server...
    cd backend
    start "Mock Backend" cmd /k "python simple_test.py"
    cd ..
    goto end
)

echo.
echo [INFO] Waiting for AI models to load...
echo This may take 5-10 minutes for first startup...
timeout /t 30 > nul 2>&1

echo.
echo [INFO] Checking service status...
docker-compose ps

echo.
echo ==========================================
echo    Real AI System Started!
echo ==========================================
echo.
echo Services available:
echo - LLM API: http://localhost:8000
echo - VLM API: http://localhost:8080
echo - Admin UI: http://localhost:5000
echo - Qdrant DB: http://localhost:6333
echo.
echo [INFO] Frontend will now connect to REAL AI
echo.
echo To stop AI services: docker-compose down
echo.

:end
echo Press any key to exit...
pause > nul