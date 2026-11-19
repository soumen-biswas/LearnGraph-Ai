# Project-based assignments

This release includes all previous Portal, role-navigation and Bangladesh-time
updates, plus practical projects alongside existing MCQ assignments. These are
separate assignment cards in the same class; an MCQ assignment is not silently
converted into a project.

## Upgrade existing Docker installation

1. Back up your source folder. Copy this ZIP's LearnGraph-Pro contents into your
   existing project and replace matching source files. Keep your existing .env.
2. Keep Docker Desktop running. Run `upgrade.bat` (PowerShell: `.\upgrade.bat`).
   It backs up PostgreSQL before applying the new additive migration 0003.
3. Refresh the browser with Ctrl+F5. Existing students, grades and certificates
   are preserved. Never delete the Docker database volume.

## Teacher / admin

Open Classes, then a class. Scroll to Project-based assignments.

- Generate AI project: enter topic, difficulty, title and Bangladesh opening /
  closing time. AI writes a practical problem with deliverables, testing
  expectations and 3–6 rubric criteria totaling 100. Maximum 10 generation
  requests per teacher per day. It does not produce a complete solution.
- Write project brief: create the problem and rubric yourself.
- Review the draft and edit before publishing. Publish is an explicit teacher
  review action. AI-generated rubric structure is validated before saving.
- A published project or one containing saved student work cannot be edited.
- Submitted work appears on the project's management page. Read the solution,
  evaluate the rubric and enter total marks (0–100) plus criterion-based feedback.
- Release results after closing, once all final submissions are graded. Released
  marks are locked. Saved drafts are not final submissions and cannot be graded.

Example project: build a Python expense tracker with add/list/delete operations,
file persistence, validation, category summaries and tests. A sample rubric is
functionality 40, validation 20, tests 25, explanation/documentation 15.

## Student

Open Assignments and choose a Project assignment. Read the brief and rubric.
Submit an explanation and relevant code, with an optional HTTPS GitHub/demo link.
Save draft to return later, then Submit final project before the closing time.
Final submissions cannot be changed or submitted twice. Submitted text is stored
as plain content and never executed. Links are not fetched by the server.

This version accepts text/code and repository/demo links, not uploaded ZIP/PDF
files. Use a commit-specific repository link when you want a stable reference;
the platform does not archive external repository content. Code execution,
plagiarism detection and AI automatic grading are not included. The teacher
assigns the marks; AI only helps author the project problem and rubric.

## Certificates

Quiz remains 40%; assignment remains 60%. The assignment component is the equal
average of all published MCQ assignments AND projects in the class. Every required
activity must be submitted, graded and released. Projects can be the only type of
assignment in a class. Overall threshold remains 70%, with 50% minimum in each
component. Drafts, missing submissions and unreleased marks do not earn eligibility.

New certificate evidence records project submission IDs and policy v2. Previously
issued certificates retain their frozen scores and evidence. Finish setting the
class curriculum before enabling certificates; publishing another required project
changes the checklist for students who have not earned a certificate yet.

## Validation

33 targeted tests passed covering projects, portal/certificate rules, role login
and Bangladesh time. This includes draft/final submission, replay, deadline,
ownership, CSRF, unsafe URLs, teacher grading, result-release gates, locked marks,
AI draft validation and project contribution to certificate eligibility.
Migration drift and credential-pattern checks passed. AI requests were mocked;
live Groq, Docker/PostgreSQL concurrency and browser interactions were not tested
in this environment. Validate the real workflow locally before public deployment.
