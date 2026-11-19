# Validation record

Checked on 10 September 2026.

## Executed successfully

- **55 Django tests passed** using isolated in-memory SQLite test settings. Coverage includes teacher/class isolation, student ownership, CSV import validation/atomicity, pending question controls, exam timing, saved-answer grading, attempt limits, result-release gates, certificate issuance/ownership/revocation, AI telemetry, CSRF, authentication, account deletion protection and page rendering.
- Django application system checks: no issues.
- Migration consistency: `makemigrations --check --dry-run` reported no changes.
- Python source syntax and 12 template JavaScript blocks checked.
- Compose/CI YAML parsed successfully; shell scripts passed syntax checks.
- Production settings loaded with a PostgreSQL DATABASE_URL and HTTPS configuration.
- `check --deploy` exited successfully with two deliberate warnings: `security.W005` (HSTS subdomains) and `security.W021` (preload). These are not silently enabled because the operator must confirm HTTPS readiness for every relevant subdomain before opting in.
- WhiteNoise/collectstatic: 129 static files copied and 387 processed outputs generated.
- Certificate PDF generated through the application, rendered to PNG and visually inspected. Embedded font spacing was corrected. Download response, public verification and revocation are covered by tests.
- Release archive exclusions and credential-pattern scan passed. No private environment file, database, cache, virtual environment, backup or Git history is shipped.

## Not executed here

- No live PostgreSQL or Redis server was available in the editing environment. SQLite test success does not prove PostgreSQL locking/concurrency behavior. The included GitHub workflow and `verify.bat` are configured to run against PostgreSQL; run those before production.
- Docker/Compose services and Caddy HTTPS issuance were not launched here. YAML parsing is not a deployment test.
- No real SMTP delivery, Groq account request, live domain or browser-based end-to-end test was performed.
- No penetration test, external dependency vulnerability certification, load test or accessibility certification is claimed.

## Release acceptance

Follow DEPLOYMENT.md on a staging domain, run the PostgreSQL tests, verify real email/AI, inspect responsive UI in your browsers, complete an assessment and scan its certificate QR. Back up and test restore before allowing real student records. Publish only after those checks pass.
