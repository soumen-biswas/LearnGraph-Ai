# Role navigation update

Apply this update AFTER LearnGraph-Pro-Portal. Copy the learning and academy folders into your existing LearnGraph-Pro folder and replace matching files. Keep your .env and database.

Run: docker compose up -d --build web
Refresh with Ctrl+F5, sign out, then sign in at /auth/login/ with account email and password. Admin goes to /manage/, teacher to /teach/, student to /. The default sidebars are now role-specific. Existing backend administrator and teacher authorization remains enforced. This update changes landing pages and navigation, not a global ban on staff visiting student URLs.

Superusers created with a different username can now sign in using their unique account email. /admin/ still uses the Django username login.

No new database migration. If you have not yet applied the Portal upgrade, apply it and run upgrade.bat first.

Validation: 5 new role tests and 10 existing login/security tests passed using SQLite test settings. Live Docker/browser verification still required.
