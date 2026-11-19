#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
umask 077
mkdir -p backups
backup_file="backups/learngraph-$(date -u +%Y%m%dT%H%M%SZ).dump"
docker compose -f compose.prod.yml exec -T db sh -c 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc' > "$backup_file"
test -s "$backup_file"
printf 'Backup created: %s\n' "$backup_file"
