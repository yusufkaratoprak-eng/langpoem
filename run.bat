@echo off

:: ── Ollama Check ──────────────────────────────────────────────────────────────
echo Checking Ollama...

where ollama >nul 2>&1
if errorlevel 1 (
    echo Ollama not found. Installing...
    winget install Ollama.Ollama --silent
    if errorlevel 1 (
        echo ERROR: Failed to install Ollama. Please install manually from https://ollama.com
        pause
        exit /b 1
    )
    echo Ollama installed successfully.
)

:: Check if Ollama is already running
curl -s http://localhost:11434 >nul 2>&1
if errorlevel 1 (
    echo Starting Ollama...
    start "" ollama serve
    :: Wait for Ollama to be ready
    :wait_loop
    timeout /t 1 >nul
    curl -s http://localhost:11434 >nul 2>&1
    if errorlevel 1 goto wait_loop
    echo Ollama is running.
) else (
    echo Ollama is already running.
)

:: ── Project Check ─────────────────────────────────────────────────────────────
if not exist .venv (
    echo Virtual environment not found. Please run setup.bat first.
    pause
    exit /b 1
)

if not exist .env (
    echo .env file not found. Please run setup.bat first.
    pause
    exit /b 1
)

call .venv\Scripts\activate.bat

for /f "tokens=1,2 delims==" %%A in (.env) do (
    set %%A=%%B
)

:: ── Run App ───────────────────────────────────────────────────────────────────
python app.py
if errorlevel 1 (
    echo ERROR: Application failed to run.
    pause
    exit /b 1
)

pause
