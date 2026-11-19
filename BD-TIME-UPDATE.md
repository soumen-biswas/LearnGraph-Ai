# Bangladesh time update

Apply on top of LearnGraph-Pro-Portal + Role Update. Copy these folders into your existing LearnGraph-Pro folder and replace matching files. Keep your .env and database.

Run: docker compose up -d --build web
Then Ctrl+F5 in your browser. No migration is required.

Django TIME_ZONE is Asia/Dhaka, with USE_TZ=True retained. Assessment and AI assignment forms take Bangladesh local time (UTC+6). Class, student assessment, AI usage and audit timestamps render in Bangladesh time. Edit forms use datetime-local compatible values.

Existing database timestamps represent the SAME instant as before: nothing is shifted in storage. For example an old opening time of 11 September 21:20 UTC now displays as 12 September 03:20 BDT. If that was entered incorrectly, unpublish and edit the draft opening time explicitly (only assessments without attempts can be edited). This update does not automatically open scheduled assessments.

CSV exports retain explicitly labeled UTC ISO timestamps for interchange. Server timestamps and deadline comparisons remain timezone-aware.

Three targeted timezone tests passed: BD form input conversion, existing timestamp edit roundtrip and template date conversion. Live browser/Docker testing was not performed here.
