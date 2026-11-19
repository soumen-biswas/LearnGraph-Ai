# Security operations

Keep `.env`, database credentials and backups private. Rotate credentials if previously shared or committed. Use a separate production secret, HTTPS, the supplied isolated service network and a least-privilege operator account.

Teachers should have Staff status and the Teacher group only, not superuser privileges. Course content is shared per subject; student records and reports are restricted to class ownership. Only administrators may access global AI usage. Audit history is application-recorded, not tamper-proof against the database administrator.

Enable private vulnerability reporting on your GitHub repository. Do not post student records, credentials, verification codes or private report exports in public issues. Review updates and run the pinned dependency/test pipeline before deploying changes.

`python scripts/check_secrets.py` detects selected credential patterns; it is not a guarantee that all sensitive data is absent. Review `git diff --cached` before pushing. Review deployment and backup guidance in DEPLOYMENT.md.
