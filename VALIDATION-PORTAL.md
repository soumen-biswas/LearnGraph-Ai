# Portal release validation

This is an incremental release candidate, not a claim of audited production readiness.

- 71 automated tests passed (70 regression/portal tests plus the final question-edit gate test).
- Automated Django regression and portal tests run with SQLite test settings.
  Coverage includes administrator access, role changes, superuser protection,
  teacher reassignment constraints, curriculum cycle checks, weighted certificate
  eligibility, unreleased scores, consent, ownership, revocation and public privacy.
- AI assignment generation tested with mocked valid and invalid responses;
  incomplete output saves no assessment or questions. Pending AI questions block
  publication. Practice fallback/grading tests use mocked AI failures.
- Django migration drift check and static collection pass.
- Combined certificate PDF rendered and visually inspected at A4 landscape.
- Credentials, local database, virtual environment and IDE metadata excluded.

Not exercised here: Docker Desktop, live PostgreSQL/Redis concurrency, backup
restore, real SMTP/Groq requests, full browser interactions, accessibility audit,
load testing or a penetration test. Test the real stack before public launch.
The local Docker upgrade script is supplied but could not be executed here.

Run the provided `verify.bat` after upgrading to exercise the existing PostgreSQL
test workflow in your Docker environment. Check assignment generation/review,
student submission, result release, certificate eligibility and PDF verification
end to end with separate student and teacher accounts.
