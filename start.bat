@echo off
echo Starting MIDAS AI Platform...
echo.

REM Check if .env exists
if not exist .env (
    echo Creating .env file from .env.example...
    copy .env.example .env
    echo.
    echo IMPORTANT: Please edit .env file and add your API keys!
    echo.
    pause
)

REM Check if frontend dependencies are installed
if not exist "frontend\node_modules" (
    echo Installing frontend dependencies...
    cd frontend
    call npm install
    cd ..
    echo.
)

REM Start backend
echo Starting backend server...
start "MIDAS Backend" cmd /k ".venv\Scripts\python.exe -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000"

REM Wait a bit for backend to start
timeout /t 3 /nobreak > nul

REM Start frontend
echo Starting frontend...
start "MIDAS Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo MIDAS is starting...
echo Backend: http://localhost:8000
echo Frontend: http://localhost:3000
echo.
echo Press any key to stop all servers...
pause > nul

REM Kill processes
taskkill /FI "WindowTitle eq MIDAS Backend*" /F
taskkill /FI "WindowTitle eq MIDAS Frontend*" /F
