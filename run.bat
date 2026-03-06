@echo off
REM Fast Archive & Split — launch on Windows
cd /d "%~dp0"
python -c "import sys; sys.path.insert(0, '.'); from src.main import main; main()"
pause
