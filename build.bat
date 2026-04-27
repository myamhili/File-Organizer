@echo off
echo ==========================================
echo Setting up environment and building executables...
echo ==========================================

echo.
echo [1/4] Checking/Creating virtual environment...
if exist venv goto skip_venv
python -m venv venv
if %errorlevel% neq 0 goto error_venv
:skip_venv

echo.
echo [2/4] Activating virtual environment...
call venv\Scripts\activate.bat
if %errorlevel% neq 0 goto error_activate

echo.
echo [3/4] Installing requirements...
python -m pip install -r requirements.txt
if %errorlevel% neq 0 goto error_pip

echo.
echo [4/4] Building executables...
python -m PyInstaller file-organizer.spec
if %errorlevel% neq 0 goto error_build1

python -m PyInstaller file-organizer-gui.spec
if %errorlevel% neq 0 goto error_build2

echo.
echo ==========================================
echo Done! Executables are in the dist/ folder.
echo ==========================================
pause
exit /b 0

:error_venv
echo Failed to create virtual environment. Make sure Python is installed and in your PATH.
pause
exit /b 1

:error_activate
echo Failed to activate virtual environment.
pause
exit /b 1

:error_pip
echo Failed to install requirements.
pause
exit /b 1

:error_build1
echo Failed to build CLI executable.
pause
exit /b 1

:error_build2
echo Failed to build GUI executable.
pause
exit /b 1


