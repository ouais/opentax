@echo off
setlocal

echo =====================================
echo   Welcome to OpenTax! Launching...   
echo =====================================

:: Check for npm
where npm >nul 2>nul
if %errorlevel% neq 0 (
    echo [X] Error: npm is not installed. Please install Node.js.
    pause
    exit /b 1
)

:: Check for python
set "PYTHON_CMD=python"
where python >nul 2>nul
if %errorlevel% neq 0 (
    set "PYTHON_CMD=python3"
    where python3 >nul 2>nul
    if %errorlevel% neq 0 (
        echo [X] Error: python is not installed. Please install Python.
        pause
        exit /b 1
    )
)

:: 1. Setup Backend
echo --^> Checking Backend Dependencies...
cd backend

if not exist venv\ (
    echo     Creating Python virtual environment...
    %PYTHON_CMD% -m venv venv
)

:: Activate venv
call venv\Scripts\activate.bat

:: Install requirements
pip install -r requirements.txt >nul 2>&1

cd ..

:: 2. Setup Frontend
echo --^> Checking Frontend Dependencies...
cd frontend

if not exist node_modules\ (
    echo     Installing Node modules (this might take a minute)...
    call npm install >nul 2>&1
)

echo     Building Frontend application...
call npm run build >nul 2>&1

cd ..

:: 3. Launch App
echo --^> Starting Server...
echo.
echo     App is starting! It will open in your browser automatically.
echo     (Keep this window open while using OpenTax. Press Ctrl+C to quit)
echo =====================================

cd backend

:: Start a new hidden process to open the browser after a short delay
start /b "" cmd /c "timeout /t 2 >nul & start http://localhost:8000"

:: Start the FastAPI server
%PYTHON_CMD% main.py

endlocal
