@echo off
echo ========================================
echo ex-GPT System Start
echo ========================================
echo.

REM 1. Ollama check
echo [1/3] Checking Ollama server...
curl -s http://localhost:11434/api/version >NUL 2>&1
if errorlevel 1 (
    echo Starting Ollama server...
    start /min cmd /c "ollama serve"
    timeout /t 3 >NUL
    
    ollama list | findstr "qwen3:8b" >NUL 2>&1
    if errorlevel 1 (
        echo Installing qwen3:8b model...
        ollama pull qwen3:8b
    )
) else (
    echo Ollama is running.
)

REM 2. Backend (support both folder names)
echo.
echo [2/3] Starting backend (port 8001)...
if exist "backend" (
    cd backend
    echo Using: backend folder
) else if exist "ex-gpt-multimodal-backend" (
    cd ex-gpt-multimodal-backend
    echo Using: ex-gpt-multimodal-backend folder
) else (
    echo ERROR: Backend folder not found!
    pause
    exit /b 1
)

if exist run_cpu_fixed.bat (
    start "Backend" cmd /k run_cpu_fixed.bat
) else if exist run.bat (
    start "Backend" cmd /k run.bat
) else (
    start "Backend" cmd /k python main.py
)
cd ..
timeout /t 5 >NUL

REM 3. Frontend (support both folder names)
echo.
echo [3/3] Starting frontend (port 5173)...
if exist "frontend" (
    cd frontend
    echo Using: frontend folder
) else if exist "ex-gpt-user" (
    cd ex-gpt-user
    echo Using: ex-gpt-user folder
) else (
    echo ERROR: Frontend folder not found!
    pause
    exit /b 1
)

start "Frontend" cmd /k npm run dev
cd ..

echo.
echo ========================================
echo System Started!
echo ========================================
echo.
echo URLs:
echo   Frontend: http://localhost:5173
echo   Backend:  http://localhost:8001
echo   API Docs: http://localhost:8001/docs
echo.
echo Current folders:
dir /B /AD | findstr "backend frontend ex-gpt"
echo.
echo To stop: Close all windows or Ctrl+C
echo ========================================
echo.
timeout /t 5 >NUL
start http://localhost:5173

pause
