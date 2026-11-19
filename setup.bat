@echo off
cd /d "%~dp0"
python configure.py
if errorlevel 1 exit /b 1
docker compose build web
if errorlevel 1 exit /b 1
docker compose up -d db redis
if errorlevel 1 exit /b 1
docker compose run --rm web python manage.py migrate
if errorlevel 1 exit /b 1
docker compose run --rm web python manage.py setup_roles
if errorlevel 1 exit /b 1
echo Fresh database initialized. Create your administrator next:
echo docker compose run --rm web python manage.py createsuperuser
echo Then run start.bat
pause
