# Update your existing LearnGraph installation

This release extends the ZIP you supplied. It preserves the collapsible subject
menu, Home-first navigation, AI practice quizzes, chat initialization fix and
Learning Path popup. It does not contain your credentials, virtual environment
or database. Your Docker PostgreSQL volume remains the source of your data.

## Windows / Docker Desktop

1. Keep a copy of your current source folder. Keep your existing `.env` private.
2. Extract this ZIP. Copy the contents of its `LearnGraph-Pro` folder into your
   current `LearnGraph-Pro` folder and replace matching source files. Do not
   delete or regenerate the existing `.env`.
3. Keep Docker Desktop running. In that project folder run `upgrade.bat`
   (PowerShell: `.\upgrade.bat`). Python and Docker must be on PATH.
4. The script builds the web image, backs up PostgreSQL into `backups/`, stops
   the web service, applies the additive migration, sets up roles and restarts
   the website. If backup or migration fails it stops; read the error.
5. Refresh the browser with Ctrl+F5. Log in with your existing superuser at
   `/admin/`, then open `/manage/`. You do not need another superuser account.

Do not run `docker compose down -v`. Do not change the Compose project name
`learngraph-pro` or generated PostgreSQL credentials. The upgrade script is for
the local `compose.yml`; deployed servers should follow the existing production
backup and migration workflow with `-f compose.prod.yml`.

## Administration inside the website

- `/manage/`: overview and links to all learning operations.
- `/manage/accounts/`: search accounts, edit names/emails, enable/disable access,
  promote registered accounts to teachers. Superusers cannot be changed here.
  Reassign classes before demoting or disabling a teacher.
- `/manage/curriculum/`: create/edit subjects and concepts, set prerequisites.
  Circular prerequisite relationships are rejected. Content deletion remains in
  the advanced Django admin console so existing learning evidence is preserved.
- `/teach/`: classes, enrollments, assignments and exams.
- `/teach/questions/`: AI drafts, edit, review and approval; CSV import is linked.
- `/teach/reports/`, `/teach/usage/`, `/teach/audit/`: existing scoped reports,
  actual AI telemetry and mutation history. AI usage is superuser-only.
- `/teach/completion/`: combined certificate register, download and revocation.

Role restrictions are enforced by backend views. Students cannot open the admin
portal by entering its URLs; teachers are limited to their assigned classes.

## AI-generated assignments

Open a class and choose **Generate AI assignment**. Set a title, 1–3 concepts,
difficulty, opening and closing time (UTC). AI creates five MCQs per concept.
The complete response is validated before saving. There is a daily limit of
10 generation submissions per teacher/admin. This can take a few minutes.

The assignment is an unpublished draft and its questions are pending. Check
answers and explanations in Question review, edit if necessary, approve, then
publish the assignment on the class page. This keeps an incorrect AI answer from
silently deciding a student's certificate. Assignments are MCQ-based, not essay
or uploaded-file grading. Student marks are computed on the server. Release
results after closing; unreleased scores do not contribute to eligibility.

## Combined course certificate policy (v1)

Enable course certificates from the class page. Students see their checklist at
`/completion/`.

- Quiz contributes 40%; assignment contributes 60%.
- Overall score must be at least 70%, with at least 50% in each component.
- A submitted quiz is required for every concept in the class subject, created
  after the class was created. The latest submitted quiz per concept counts.
- Every currently published assignment in that class must have a submitted
  attempt and released results. Latest submitted attempt per assignment counts.
- Each concept / assignment has equal weight within its component. At least one
  concept and one published assignment are required. Exams are separate.
- Checklists change if teachers change the curriculum or published assignments.
  Finish configuring the class before enabling certificates.
- On issuance the computed scores, attempt IDs, requirements and policy text are
  frozen. Later practice does not rewrite an issued certificate. One certificate
  per student per class. Revoked certificates cannot be reissued via this flow.
- English display name and consent are required. Public QR verification shows
  name, course, issue date and status, not email or individual assessment marks.

These are learning completion records, not proctored or accredited qualifications.
Existing exam certificates continue to work independently. Auto-generated practice
questions can be wrong and this limitation also applies to their contribution.

## Design

Mint/blue accents, a new graph-inspired SVG mark, layered dark backgrounds,
responsive administration cards, clearer forms and a unified navigation system.
The existing animated authentication pages and popup learning guides are retained.

## Before GitHub / public hosting

Only push source and `.env.example`. Never push `.env`, backups or virtual
environments. This archive omits those uploaded items. Keep the existing working
Groq key/model in your private `.env`. The example now defaults to
`openai/gpt-oss-120b`; provider availability depends on your account.

Read `VALIDATION-PORTAL.md` for what was tested and the remaining deployment gates.
