@echo off
echo ========================================
echo ex-GPT AI System Start (Improved)
echo ========================================
echo.

REM 1. Ollama check
echo [1/4] Checking Ollama server...
curl -s http://localhost:11434/api/version >NUL 2>&1
if errorlevel 1 (
    echo Starting Ollama server...
    start /min cmd /c "ollama serve"
    timeout /t 5 >NUL
) else (
    echo Ollama is running.
)

REM 2. Main Backend (port 8200 - from .env)
echo.
echo [2/4] Starting main backend (port 8200)...
cd backend
if exist .venv (
    echo Using virtual environment...
    start "Main Backend" cmd /k ".venv\Scripts\activate && python main.py"
) else (
    echo Using uv...
    start "Main Backend" cmd /k "uv run python main.py"
)
cd ..
timeout /t 3 >NUL

REM 3. Test Backend (port 8201)
echo.
echo [3/4] Starting test backend (port 8201)...
cd backend
if exist .venv (
    start "Test Backend" cmd /k ".venv\Scripts\activate && python simple_test.py"
) else (
    start "Test Backend" cmd /k "uv run python simple_test.py"
)
cd ..
timeout /t 3 >NUL

REM 4. Frontend (port 5174)
echo.
echo [4/4] Starting frontend (port 5174)...
cd frontend
start "Frontend" cmd /k "npm run dev"
cd ..

echo.
echo ========================================
echo System Started!
echo ========================================
echo.
echo URLs:
echo   Frontend:     http://localhost:5174
echo   Main Backend: http://localhost:8200 (VLM search)
echo   Test Backend: http://localhost:8201 (file search)
echo   Main Docs:    http://localhost:8200/docs
echo   Test Docs:    http://localhost:8201/docs
echo.
echo Note: 
echo - Main backend needs 10-15 minutes to initialize VLM model
echo - Use test backend (8201) for immediate testing
echo - Check backend status at /health endpoint
echo.
echo To stop: Close all terminal windows
echo ========================================
echo.
timeout /t 3 >NUL
start http://localhost:5174

pause