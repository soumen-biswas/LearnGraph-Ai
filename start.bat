@echo off
cd /d "%~dp0"
docker compose up -d web
if errorlevel 1 exit /b 1
echo Open http://localhost:8000
pause
