# LearnGraph Pro — Administration & Completion Update

**Latest: project-based assignments are included.** See [PROJECT-ASSIGNMENTS.md](PROJECT-ASSIGNMENTS.md) for upgrade and usage. AI generates practical briefs and rubrics; students submit code/explanations and optional repository links. Teachers grade and release results. Project marks contribute to the assignment component of course certificates. Role navigation and Bangladesh time updates are bundled.

A Django/PostgreSQL learning platform with an integrated administration dashboard, AI assignment drafts, reviewed question banks and combined quiz/assignment certificates.

**Existing installation: follow [UPGRADE-PORTAL.md](UPGRADE-PORTAL.md) and run `upgrade.bat`. Keep your existing `.env` and PostgreSQL volume.** New installations can follow [START-HERE.md](START-HERE.md). No user accounts, passwords or database contents are bundled.

## New in this update

- `/manage/`: integrated administration, account roles/access and curriculum editing.
- Class pages: generate an AI assignment draft, review/edit questions and publish.
- `/completion/`: student checklist, weighted marks and course certificate downloads.
- `/teach/completion/`: certificate register, PDF access and revocation.
- Mint/blue interface, graph logo and improved backgrounds/cards. Existing AI practice quizzes and Learning Path popup are retained.

Course certificates use 40% quiz + 60% assignment, minimum 70% overall and 50% per component. Complete all required concepts and published assignments; teacher release is required. See the upgrade guide for the full evidence policy and [VALIDATION-PORTAL.md](VALIDATION-PORTAL.md) for validation limits.

## Included

| Requested area | Delivered implementation |
|---|---|
| Student overview | Class roster, per-student subject mastery and assessment history, scoped to assigned teachers |
| Class/batch management | Create/rename classes, administrator teacher assignment, email-based enrollment and removal |
| Question approval | Pending/approved/rejected workflow with reviewer/time; AI and CSV content require review |
| Assignments & exams | Scheduled MCQ assignments; server-timed exams, saved answers, attempt limits, immutable answer snapshots, result release |
| Bulk import | UTF-8 CSV template, row validation, 1 MB / 500-row limit, atomic import into pending review |
| AI usage | Administrator dashboard for provider calls, successful/failed requests, latency and token counts |
| Audit log | Scoped portal records for management actions and content-admin edits, without prompts/passwords |
| Reports | Filter by class, review submitted results, export formula-safe CSV |
| Certificates | Passing-score eligibility, release gate, English-name PDF, unique UUID, QR verification and revocation |
| PostgreSQL | Production/default database through DATABASE_URL; migrations and persistent Docker volume |
| Production stack | Gunicorn, WhiteNoise, Redis counters, Caddy HTTPS, private backend ports, container configuration |
| GitHub | Clean source, secret exclusions/scanner, pinned dependency lock, PostgreSQL CI and Dependabot configuration |

The previous learning capabilities remain: animated sign-in/signup, password recovery, personal concept graph/progress, practice quizzes, saved chat, private text notes, note-reference retrieval, study goals and revision scheduling. No old accounts, database files, keys or Git history are included.

## Main routes

| Route | Who uses it |
|---|---|
| `/` | Signed-in learning overview |
| `/workspace/` | Student goals, private notes and saved conversations |
| `/assessments/` | Enrolled assessments, attempt results and certificates |
| `/teach/` | Teacher/admin overview |
| `/teach/questions/` | Review drafts or generate AI drafts for class subjects |
| `/teach/reports/` | Class-scoped reports and certificate revocation |
| `/teach/usage/` | Administrator-only AI metrics |
| `/teach/audit/` | Scoped action records |
| `/admin/` | Administrator accounts, subjects/concepts and content records |
| `/certificates/<uuid>/verify/` | Public certificate status after recipient consent |

## Installation and publication

- Local: Python + Docker Desktop, then `setup.bat` and `start.bat`.
- Linux: `sh setup.sh`, then `docker compose up -d web`.
- Production VPS/domain: follow [DEPLOYMENT.md](DEPLOYMENT.md).
- Application services use PostgreSQL and Redis; normal mode does not fall back to SQLite.
- Developer-only test settings can use in-memory SQLite when no DATABASE_URL is supplied. CI uses PostgreSQL 16.
- Real email and AI require your own SMTP/Groq settings. No external messages or API calls are made by installation.

## Fresh content flow

1. Administrator creates subjects and concepts in Django admin.
2. Administrator creates teacher accounts (or promotes verified signups to Staff + Teacher group).
3. Teacher creates a class, or administrator creates and assigns it.
4. Student signs up and verifies email; teacher enrolls the account.
5. Teacher authors/imports/generates draft questions and reviews them.
6. Teacher creates and publishes an assignment/exam.
7. Student attempts it. The server grades answers; the browser cannot supply the score.
8. After closing, teacher releases results, finalizing any unfinished attempts using saved answers.
9. A student who passes a certificate-enabled exam may consent to public verification, choose an English certificate name and download the PDF.

Certificates are completion records for the assessment, not accredited qualifications. Assignments are MCQ-based; file submission, essay grading and lesson-completion certification are not included. Course-note retrieval accepts pasted text, not PDF uploads. Approved question banks are shared by subject; teachers can review subjects of their assigned classes. Student records remain class-scoped.

## GitHub push

From the newly extracted project folder:

```bash
git init
git add .
python scripts/check_secrets.py
git status --short
git diff --cached --stat
git check-ignore .env backups/
git commit -m "Initial LearnGraph Pro platform"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPOSITORY.git
git push -u origin main
```

Use your own new repository URL. Never force-add `.env`, backup dumps or private data. GitHub hosts the source and CI; it does not itself run the Django website. You need the deployment described above.

## Validation

See [VALIDATION.md](VALIDATION.md) for performed checks and remaining deployment checks. Run `verify.bat` against your local Docker/PostgreSQL environment. The included CI workflow repeats the application tests using PostgreSQL when pushed to GitHub.

Dependencies are pinned in `requirements.lock.txt`, which Docker and CI use. `requirements.txt` records the intended direct version ranges. Review dependency updates and regenerate the lock after testing. Certificate fonts are bundled with their license in `academy/fonts/`.
