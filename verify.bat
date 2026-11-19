@echo off
cd /d "%~dp0"
docker compose run --rm web python manage.py check
if errorlevel 1 exit /b 1
docker compose run --rm web python manage.py makemigrations --check --dry-run
if errorlevel 1 exit /b 1
docker compose run --rm web python manage.py test --settings=learngraph.test_settings
if errorlevel 1 exit /b 1
docker compose run --rm web python scripts/check_secrets.py
if errorlevel 1 exit /b 1
echo All checks passed.
pause
