@echo off
echo ========================================
echo ex-GPT 테스트 백엔드 재시작
echo ========================================
echo.

REM 기존 프로세스 종료
echo [1/2] 기존 백엔드 종료 중...
taskkill /F /FI "WINDOWTITLE eq Test Backend*" >NUL 2>&1
timeout /t 2 >NUL

REM 새로 시작
echo [2/2] 테스트 백엔드 재시작 중...
cd backend
start "Test Backend" cmd /k "python simple_test.py"
cd ..

echo.
echo ========================================
echo 테스트 백엔드가 재시작되었습니다!
echo ========================================
echo.
echo URL: http://localhost:8201
echo API Docs: http://localhost:8201/docs
echo.
echo 브라우저에서 새로고침(F5)하세요.
echo ========================================
echo.
timeout /t 2 >NUL

pause