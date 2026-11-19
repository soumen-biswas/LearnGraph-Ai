#!/bin/sh
set -eu
python manage.py collectstatic --noinput
exec gunicorn learngraph.wsgi:application --bind 0.0.0.0:8000 --workers 3 --threads 2 --timeout 90 --access-logfile - --error-logfile -
