# Production deployment

## Architecture

Browser → Caddy HTTPS reverse proxy → Gunicorn/Django → PostgreSQL 16.
Redis provides shared request counters and daily AI-request quotas. WhiteNoise serves collected CSS/JavaScript. Certificates are generated on demand from verified database records.

The supplied production stack is for a Docker-capable Linux VPS with a domain. Standard static hosting or PHP-only cPanel cannot run it. Domain, server, email service and Groq account are supplied by you; no deployment or paid infrastructure has been created by this package.

## 1. Prepare your server

Install Docker Engine with the Compose plugin. Point your domain's DNS A/AAAA records to the server. Permit inbound 80 and 443, and restrict SSH as appropriate. PostgreSQL, Redis and Gunicorn must stay off public ports; the production compose file exposes only Caddy.

Clone your new GitHub repository on the server. Create a DIFFERENT production `.env` using `python3 configure.py`. Never reuse a development secret or old project credentials.

Set these production values in `.env`:

```env
DEBUG=False
ALLOWED_HOSTS=your-real-domain.com
CSRF_TRUSTED_ORIGINS=https://your-real-domain.com
PUBLIC_BASE_URL=https://your-real-domain.com
DOMAIN=your-real-domain.com
ACME_EMAIL=your-admin-email@example.com
TRUST_PROXY=True
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-sending-address@gmail.com
EMAIL_HOST_PASSWORD=your-new-smtp-app-password
DEFAULT_FROM_EMAIL=your-sending-address@gmail.com
GROQ_API_KEY=your-new-groq-key
```

Retain the newly generated SECRET_KEY, POSTGRES_PASSWORD and DATABASE_URL. Local Compose PostgreSQL uses an isolated Docker network. If connecting to managed PostgreSQL instead, set DATABASE_URL to the provider URL with its required TLS options (normally `sslmode=require`); remove the unused local database service and adjust dependencies before deployment. Do not expose the local database to make managed hosting work.

`TRUST_PROXY=True` is safe only when the application is reachable through a trusted proxy that overwrites the headers. The provided Caddy configuration overwrites scheme and client-IP headers, and Gunicorn has no public port. Do not expose port 8000 on the production host.

## 2. Initialize and start

Run from the repository root:

```bash
docker compose -f compose.prod.yml build web
docker compose -f compose.prod.yml up -d db redis
docker compose -f compose.prod.yml run --rm web python manage.py migrate
docker compose -f compose.prod.yml run --rm web python manage.py setup_roles
docker compose -f compose.prod.yml run --rm web python manage.py check --deploy
docker compose -f compose.prod.yml run --rm web python manage.py createsuperuser
docker compose -f compose.prod.yml up -d web caddy
```

Caddy obtains/renews HTTPS certificates when domain DNS and inbound ports are correct. The app collects static files on container start. Keep migrations as an explicit release step; they are not run concurrently by Gunicorn workers.

Use `docker compose -f compose.prod.yml logs --tail=100 web caddy` to diagnose startup. Do not paste environment values, passwords or private email content into support messages.

## 3. First-launch acceptance

Verify on the real domain:

- HTTP redirects to HTTPS; static styling loads; secure cookies are set.
- Signup, real verification email, sign-in and password recovery work.
- A teacher cannot open another teacher's class, roster or report.
- Imported/AI questions stay pending until approval.
- A timed assessment saves answers, respects server expiry, grades only once, and hides review until release.
- A passing result yields a downloadable PDF after consent; QR opens the correct public verification URL; revocation blocks new downloads.
- Real AI calls succeed and token/error records appear in the administrator usage dashboard.

Automated CI runs the test suite on PostgreSQL. Also run it against a staging stack before production releases. There is no browser automation or deployment success claim in this ZIP.

## 4. Backups and maintenance

Run `sh deploy/backup.sh` from the repository root for a PostgreSQL custom-format backup. Backups are private, ignored by Git, and may contain student data. Copy them to encrypted off-server storage and test restore on a separate staging database. A backup on the same server alone is not disaster recovery.

To inspect an archive: `pg_restore --list your-backup.dump`. Restore only into a separate, explicitly selected empty database first; do not experiment on production. Docker volumes hold PostgreSQL/Redis data. `docker compose down` retains volumes, while `down -v` destroys them—do not use it on data you want to keep.

Set up a host scheduler to run backups and `python manage.py clearsessions` periodically. Monitor disk space, PostgreSQL health, application errors, SMTP failures and provider spending. Dependency update proposals are configured through Dependabot; review and test updates before deployment.

## Limits

Assignments in this release are scheduled MCQ assessments, not file uploads or essay grading. Certificates certify passing an enabled assessment; they do not imply accreditation or lesson-completion checks. There is no proctoring, plagiarism detection, SSO, payment billing or asynchronous AI job queue. AI token metrics record provider-returned counts, not money spent. Calls execute synchronously with timeouts.

Audit entries are append-only in the UI, not cryptographically tamper-proof against database administrators. Raw Django user/group changes also have Django's native admin history. Public certificate verification intentionally displays the certificate name/course/date after the student's explicit consent.

References: [Django deployment checklist](https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/), [Docker startup dependencies](https://docs.docker.com/compose/how-tos/startup-order/), [Caddy reverse proxy](https://caddyserver.com/docs/caddyfile/directives/reverse_proxy).
