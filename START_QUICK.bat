@echo off
echo ========================================
echo ex-GPT AI System Quick Start
echo ========================================
echo.

REM 빠른 시작을 위한 간단 버전
REM 테스트 백엔드만 시작 (빠른 응답)

echo [1/2] Starting test backend (port 8201)...
cd backend
start "Test Backend" cmd /k "python simple_test.py"
cd ..
timeout /t 2 >NUL

echo [2/2] Starting frontend (port 5173)...
cd frontend
start "Frontend" cmd /k "npm run dev"
cd ..

echo.
echo ========================================
echo Quick Start Complete!
echo ========================================
echo.
echo URLs:
echo   Frontend:     http://localhost:5173
echo   Test Backend: http://localhost:8201
echo   API Docs:     http://localhost:8201/docs
echo.
echo This is a test backend with mock data.
echo For full VLM features, use START_IMPROVED.bat
echo ========================================
echo.
timeout /t 2 >NUL
start http://localhost:5173

pause