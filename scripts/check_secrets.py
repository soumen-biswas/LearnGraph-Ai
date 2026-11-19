"""Scan tracked files (or clean source before git init). Never prints secret values."""
from pathlib import Path
import re
import subprocess
import sys

root = Path(__file__).resolve().parents[1]
patterns = [re.compile(rb'gsk_[A-Za-z0-9]{20,}'), re.compile(rb'AIza[A-Za-z0-9_-]{30,}'), re.compile(rb'sk-[A-Za-z0-9_-]{20,}'), re.compile(rb'gh[pousr]_[A-Za-z0-9]{20,}'), re.compile(rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----')]
try:
    names = subprocess.check_output(['git', '-C', str(root), 'ls-files', '-z'], stderr=subprocess.DEVNULL).decode().split('\0')
    paths = [root / n for n in names if n]
except (OSError, subprocess.CalledProcessError):
    paths = [p for p in root.rglob('*') if p.is_file() and not any(x in p.parts for x in ('.git', '.venv', '__pycache__')) and p.name != '.env']
errors = []
for p in paths:
    if not p.is_file(): continue
    if (p.name.startswith('.env') and p.name != '.env.example') or p.suffix in ('.sqlite3', '.db', '.pem', '.key', '.log'):
        errors.append(str(p.relative_to(root)) + ': private file')
    if any(pattern.search(p.read_bytes()) for pattern in patterns):
        errors.append(str(p.relative_to(root)) + ': potential credential')
for error in errors: print(error)
print('Secret scan:', 'FAILED' if errors else 'PASS (pattern-based; manually review staged changes too)')
sys.exit(bool(errors))
