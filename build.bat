@echo off
echo Setting up environment and building executables...
python -m venv venv
call venv\Scripts\activate.bat
pip install -r requirements.txt
pyinstaller file-organizer.spec
pyinstaller file-organizer-gui.spec
echo Done! Executables are in the dist/ folder.
pause
