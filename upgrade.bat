@echo off
cd /d "%~dp0"
python scripts\upgrade.py
if errorlevel 1 exit /b 1
