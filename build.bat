@echo off
echo Setting up environment and building executables...

echo [1/4] Checking/Creating virtual environment...
if not exist venv (
    python -m venv venv
    if errorlevel 1 (
        echo Failed to create virtual environment. Make sure Python is installed and in your PATH.
        pause
        exit /b 1
    )
)

echo [2/4] Activating virtual environment...
call venv\Scripts\activate.bat

echo [3/4] Installing requirements...
python -m pip install -r requirements.txt
if errorlevel 1 (
    echo Failed to install requirements.
    pause
    exit /b 1
)

echo [4/4] Building executables...
python -m PyInstaller file-organizer.spec
if errorlevel 1 (
    echo Failed to build CLI executable.
    pause
    exit /b 1
)

python -m PyInstaller file-organizer-gui.spec
if errorlevel 1 (
    echo Failed to build GUI executable.
    pause
    exit /b 1
)

echo ==========================================
echo Done! Executables are in the dist/ folder.
echo ==========================================
pause

