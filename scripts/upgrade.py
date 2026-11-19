"""Upgrade the local Docker stack without replacing credentials or volumes."""
from datetime import datetime, timezone
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]

def run(*args, **kwargs):
    return subprocess.run(['docker', 'compose', *args], cwd=ROOT, check=True, **kwargs)

def main():
    if not (ROOT / '.env').exists():
        raise RuntimeError('Keep your existing .env in this folder before upgrading. Do not generate new database credentials.')
    run('build', 'web')
    run('up', '-d', 'db', 'redis')
    folder = ROOT / 'backups'
    folder.mkdir(exist_ok=True)
    backup = folder / ('before-portal-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ') + '.dump')
    with backup.open('xb') as output:
        try:
            run('exec', '-T', 'db', 'sh', '-c', 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc', stdout=output)
        except Exception:
            backup.unlink(missing_ok=True)
            raise
    print('Database backup saved:', backup.name)
    run('stop', 'web')
    run('run', '--rm', 'web', 'python', 'manage.py', 'migrate', '--noinput')
    run('run', '--rm', 'web', 'python', 'manage.py', 'setup_roles')
    run('up', '-d', 'web')
    print('Upgrade completed. Open http://localhost:8000/manage/ with your superuser account.')

if __name__ == '__main__':
    try:
        main()
    except (OSError, RuntimeError, subprocess.CalledProcessError) as exc:
        print('Upgrade stopped:', exc, file=sys.stderr)
        print('Keep the database volume and backup. Resolve the error before retrying.', file=sys.stderr)
        sys.exit(1)
