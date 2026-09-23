@echo off
rem Double-click: writes and opens a local status page that refreshes every 30 s. Read-only.
cd /d "%~dp0..\.."
:loop
python tools\orch.py --config orchestration.toml live-view --out "%TEMP%\{{PROJECT_NAME}}-live-view.html" >nul
if not defined OPENED (start "" "%TEMP%\{{PROJECT_NAME}}-live-view.html" & set OPENED=1)
timeout /t 30 /nobreak >nul
goto loop
