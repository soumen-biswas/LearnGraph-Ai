#!/bin/sh
set -eu
cd "$(dirname "$0")"
python3 configure.py
docker compose build web
docker compose up -d db redis
docker compose run --rm web python manage.py migrate
docker compose run --rm web python manage.py setup_roles
printf 'Create an administrator: docker compose run --rm web python manage.py createsuperuser\nStart: docker compose up -d web\n'
