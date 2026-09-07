@echo off
cd /d "%~dp0"

echo ==========================================
echo     IT SUPPORT AUTOMATION DASHBOARD
echo ==========================================
echo.

if not exist ".venv\Scripts\python.exe" (
    echo ERROR: .venv folder not found.
    pause
    exit /b 1
)

if not exist ".env" (
    echo ERROR: .env file not found.
    pause
    exit /b 1
)

echo Loading Gemini configuration...

for /f "usebackq tokens=1,* delims==" %%A in (".env") do (
    set "%%A=%%B"
)

echo Starting backend server...
echo.

start "IT Support Backend" /min cmd /c ""%~dp0.venv\Scripts\python.exe" -m uvicorn main:app --host 127.0.0.1 --port 8000"

echo Waiting for server...
timeout /t 6 /nobreak >nul

echo Opening dashboard...
start "" "http://127.0.0.1:8000/dashboard"

echo.
echo Dashboard started successfully.
exit /b 0