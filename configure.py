"""Create a fresh private Docker environment. Never overwrite an existing file."""
from pathlib import Path
import os,secrets
root=Path(__file__).resolve().parent
try:fd=os.open(root/'.env',os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
except FileExistsError:print('.env already exists; no values changed.')
else:
    values=(root/'.env.example').read_text().replace('GENERATE_SECRET_KEY',secrets.token_urlsafe(64)).replace('GENERATE_DATABASE_PASSWORD',secrets.token_urlsafe(32))
    with os.fdopen(fd,'w') as file:file.write(values)
    print('Created .env with new secret and database password. Add your API and email configuration privately.')
