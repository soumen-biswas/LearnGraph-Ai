# LearnGraph Pro — fresh installation

This is a NEW installation. Do not copy any old `.env`, database, virtual environment or Git history.

## Windows: local PostgreSQL setup

Install Python 3.10+ and Docker Desktop with Linux containers. Start Docker Desktop.

1. Extract `LearnGraph-Pro.zip` into a new folder.
2. Double-click `setup.bat`. It generates private credentials, builds the app, starts PostgreSQL/Redis and runs migrations. It creates no demo users or old records.
3. Open a terminal in that folder:

```bat
docker compose run --rm web python manage.py createsuperuser
```

4. Double-click `start.bat`. Open **http://localhost:8000**.
5. Open **http://localhost:8000/admin/** and sign in as the administrator.
6. Add a Subject and its Concepts. Then open **http://localhost:8000/teach/** and create your first class.
7. Students sign up and verify their accounts. Enroll them in the class using their account email.
8. Add/approve questions, create and publish an assessment, then release results after its closing time.

Local verification and password-reset emails appear in the server log:

```bat
docker compose logs -f web
```

For real email, edit `.env`: select the SMTP backend, add your email address and email provider's SMTP credential (Gmail uses an App Password). Add your Groq key if using AI. Restart after changes:

```bat
docker compose up -d --force-recreate web
```

No API key is needed to author/import questions or run approved-question exams. AI tutor and AI draft generation need a valid Groq key.

## Teacher accounts

Create the account through normal signup, then as administrator open Users in `/admin/`, enable **Staff status** and assign the **Teacher** group. Do not grant superuser status to a teacher. Teachers use `/teach/`; their assigned classes determine student/report access. They do not receive global Django model permissions.

Teachers own the classes they create. Administrators can assign or reassign a teacher using Create/Edit class and see all classes. Subject/concept structure is created by the administrator; teachers review shared question banks for the subjects of their own classes.

## Verification

Run `verify.bat` after setup. It checks Django configuration, migration consistency, tests against your PostgreSQL service, and the secret scanner. Django creates and destroys a separate test database; your application database is not used for test records.

Test the real AI connection separately:

```bat
docker compose run --rm web python manage.py check_ai
```

## Optional sample content

Fresh setup intentionally starts empty. For demonstration content only, you may run:

```bat
docker compose run --rm web python manage.py seed_data
docker compose run --rm web python manage.py seed_practice
```

These commands add subjects/concepts and authored starter questions, not student accounts. Do not run them unless you want sample content.

## Publish

Read **DEPLOYMENT.md** for a Docker-capable VPS with your own domain and HTTPS. GitHub stores the source; GitHub Pages cannot run this Django/PostgreSQL backend. You do not upload a database file to GitHub.
