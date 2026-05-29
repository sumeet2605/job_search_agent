# Job Search Agent

Automated GitHub Actions agent for Sumeet Bhardwaj's senior GenAI, AI Architecture, Cloud Architecture, and Enterprise AI Transformation job search.

## What it does

- Runs daily at 9:00 AM IST via GitHub Actions.
- Searches public job listings for senior AI/cloud roles.
- Scores roles against the target resume profile.
- Writes matched jobs to Google Sheets.
- Avoids duplicate job links.

## Required GitHub Secrets

- `SPREADSHEET_ID`
- `SHEET_NAME`
- `GOOGLE_SERVICE_ACCOUNT_JSON`

## Manual test

Go to Actions → Daily Job Search → Run workflow.
