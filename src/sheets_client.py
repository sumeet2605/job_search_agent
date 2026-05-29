import json
import os
from datetime import datetime, timezone

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

from config import HEADERS, SHEET_NAME, SPREADSHEET_ID

CRM_TABS = ["Recommended", "Applied", "Interviews", "Offers"]


def get_service():
    raw = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")
    if not raw:
        raise RuntimeError("Missing GOOGLE_SERVICE_ACCOUNT_JSON secret")
    info = json.loads(raw)
    creds = Credentials.from_service_account_info(
        info,
        scopes=["https://www.googleapis.com/auth/spreadsheets"],
    )
    return build("sheets", "v4", credentials=creds)


def ensure_tab(service, title):
    meta = service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute()
    existing = {s["properties"]["title"] for s in meta.get("sheets", [])}
    if title in existing:
        return
    service.spreadsheets().batchUpdate(
        spreadsheetId=SPREADSHEET_ID,
        body={"requests": [{"addSheet": {"properties": {"title": title}}}]},
    ).execute()


def ensure_headers(service, title):
    service.spreadsheets().values().update(
        spreadsheetId=SPREADSHEET_ID,
        range=f"{title}!A1:O1",
        valueInputOption="USER_ENTERED",
        body={"values": [HEADERS]},
    ).execute()


def setup_workbook(service):
    ensure_headers(service, SHEET_NAME)
    for tab in CRM_TABS:
        ensure_tab(service, tab)
        ensure_headers(service, tab)


def existing_links(service, title):
    result = service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID,
        range=f"{title}!G2:G10000",
    ).execute()
    return {row[0].strip() for row in result.get("values", []) if row}


def job_to_row(job):
    today = datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d")
    return [
        today,
        job.get("company", "To verify"),
        job.get("title", ""),
        job.get("location", "Bangalore / India / Remote"),
        job.get("work_mode", "Hybrid/Remote/On-site to verify"),
        job.get("portal", "Public web"),
        job.get("link", ""),
        job.get("score", 0),
        job.get("salary", "Not listed"),
        job.get("priority", "P3"),
        job.get("why", ""),
        job.get("risk", ""),
        job.get("resume_version", "GenAI + Cloud Executive Resume"),
        job.get("status", "Not Applied"),
        job.get("notes", ""),
    ]


def append_unique(service, title, jobs):
    known = existing_links(service, title)
    rows = []
    for job in jobs:
        link = job.get("link", "").strip()
        if not link or link in known:
            continue
        rows.append(job_to_row(job))
    if rows:
        service.spreadsheets().values().append(
            spreadsheetId=SPREADSHEET_ID,
            range=f"{title}!A:O",
            valueInputOption="USER_ENTERED",
            insertDataOption="INSERT_ROWS",
            body={"values": rows},
        ).execute()
    return len(rows)
