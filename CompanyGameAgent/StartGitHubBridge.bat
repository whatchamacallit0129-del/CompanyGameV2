@echo off
setlocal
cd /d "%~dp0"
python bridge_poll_github.py
pause
