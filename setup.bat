@echo off
setlocal enabledelayedexpansion

echo [1/4] Creating virtual environment...
if exist .venv (
    echo .venv already exists, skipping creation.
) else (
    python -m venv .venv
    if errorlevel 1 (
        echo ERROR: Python not found or venv could not be created.
        pause
        exit /b 1
    )
)

if defined VIRTUAL_ENV (
    echo Virtual environment already active, skipping activation.
) else (
    call .venv\Scripts\activate.bat
)

echo [2/4] Checking dependencies...
set ALL_INSTALLED=1
for /f "usebackq delims=" %%P in ("requirements.txt") do (
    if not "%%P"=="" (
        python -m pip show %%P >nul 2>&1
        if errorlevel 1 set ALL_INSTALLED=0
    )
)
if "!ALL_INSTALLED!"=="1" (
    echo All dependencies are already installed.
) else (
    echo Installing dependencies...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo ERROR: Failed to install dependencies.
        pause
        exit /b 1
    )
)

echo [3/4] Checking .env file...
if not exist .env (
    echo .env file not found, creating sample...
    echo OLLAMA_MODEL=llama3.2> .env
    echo OLLAMA_BASE_URL=http://localhost:11434>> .env
    echo .env file created.
) else (
    echo .env file already exists.
)

echo.
echo [4/4] Setup complete!
echo To run the project: run.bat
echo.
pause
