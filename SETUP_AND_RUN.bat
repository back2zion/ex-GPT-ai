@echo off
echo ========================================
echo ex-GPT COMPLETE SETUP
echo ========================================
echo.
echo This will:
echo 1. Rename folders (backend/frontend/admin)
echo 2. Delete unnecessary files
echo 3. Start the system
echo.
echo Press Ctrl+C to cancel, or
pause

cd /d C:\Users\user\Documents\interim_report

REM ===== STEP 1: RENAME FOLDERS =====
echo.
echo [STEP 1] Renaming folders...
echo.

if exist "ex-gpt-multimodal-backend" (
    if exist "backend" rmdir /S /Q "backend" 2>NUL
    ren "ex-gpt-multimodal-backend" "backend" 2>NUL
    echo   OK: backend
) else if exist "backend" (
    echo   OK: backend (already exists)
)

if exist "ex-gpt-user" (
    if exist "frontend" rmdir /S /Q "frontend" 2>NUL
    ren "ex-gpt-user" "frontend" 2>NUL
    echo   OK: frontend
) else if exist "frontend" (
    echo   OK: frontend (already exists)
)

if exist "ex-gpt-admin" (
    if exist "admin" rmdir /S /Q "admin" 2>NUL
    ren "ex-gpt-admin" "admin" 2>NUL
    echo   OK: admin
) else if exist "admin" (
    echo   OK: admin (already exists)
)

REM ===== STEP 2: DELETE UNNECESSARY =====
echo.
echo [STEP 2] Cleaning up...
echo.

REM Delete folders
for %%f in (ex-gpt-mcp-backend ex-gpt-backend backends components scenario images UsersuserDocumentsinterim-report-github) do (
    if exist "%%f" rmdir /S /Q "%%f" 2>NUL
)

REM Delete files
del /F /Q "*.zip" 2>NUL
del /F /Q "cleanup*.bat" 2>NUL
del /F /Q "CLEANUP*.bat" 2>NUL
del /F /Q "RUN*.bat" 2>NUL
del /F /Q "RENAME*.bat" 2>NUL
del /F /Q "FINAL*.bat" 2>NUL
del /F /Q "START_*.bat" 2>NUL
del /F /Q "start.bat" 2>NUL
del /F /Q "*.ps1" 2>NUL
del /F /Q "*BACKEND*.md" 2>NUL
del /F /Q "*CLEANUP*.md" 2>NUL
del /F /Q "README_*.md" 2>NUL
del /F /Q "*.yml" 2>NUL
del /F /Q "*.txt" 2>NUL

echo   OK: Cleaned up

REM ===== STEP 3: SHOW RESULT =====
echo.
echo ========================================
echo SETUP COMPLETE!
echo ========================================
echo.
echo Folder structure:
for /D %%d in (*) do echo   - %%d
echo.
echo Files:
echo   - START.bat (system starter)
echo   - README.md (documentation)
echo   - SETUP_AND_RUN.bat (this file)
echo.

REM ===== STEP 4: START SYSTEM =====
echo ========================================
echo Starting system...
echo ========================================
echo.
timeout /t 3 >NUL

call START.bat
