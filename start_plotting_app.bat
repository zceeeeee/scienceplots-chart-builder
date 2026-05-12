@echo off
cd /d "%~dp0"

set URL=http://127.0.0.1:8050/

start "" cmd /c "timeout /t 2 /nobreak >nul && start "" "%URL%""

python ".\plotting_web_app\app.py"

pause