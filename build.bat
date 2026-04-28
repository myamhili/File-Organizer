@echo off
cd /d "%~dp0"

echo ==========================================
echo Setting up environment and building executables...
echo ==========================================

echo.
echo [1/4] Checking/Creating virtual environment...
if not exist venv goto create_venv

:: Check if the existing venv works in this environment
venv\Scripts\python.exe -c "import sys" >nul 2>&1
if %errorlevel% equ 0 goto skip_venv

echo Existing virtual environment is broken (likely copied to a new environment). Recreating...
rmdir /s /q venv

:create_venv
echo Creating new virtual environment...
python -m venv venv
if %errorlevel% neq 0 (
    echo ERROR: Failed to create virtual environment
    pause
    exit /b 1
)

:skip_venv
echo.
echo [2/4] Activating virtual environment...
call venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo ERROR: Failed to activate virtual environment
    pause
    exit /b 1
)

echo.
echo [3/4] Installing requirements...
python -m pip install --upgrade pip
python -m pip install -r "%~dp0requirements.txt"
if %errorlevel% neq 0 (
    echo ERROR: Failed to install requirements
    pause
    exit /b 1
)

echo.
echo [4/4] Building executables...
echo Building CLI version...
python -m PyInstaller "%~dp0file-organizer.spec" --log-level DEBUG
if %errorlevel% neq 0 (
    echo ERROR: Failed to build CLI executable
    pause
    exit /b 1
)

echo Building GUI version...
python -m PyInstaller "%~dp0file-organizer-gui.spec" --log-level DEBUG
if %errorlevel% neq 0 (
    echo ERROR: Failed to build GUI executable
    pause
    exit /b 1
)

echo.
echo ==========================================
echo Done! Executables are in the dist/ folder.
echo ==========================================
pause