import json
import os
import re
from datetime import datetime, timezone
from urllib.parse import quote_plus

import requests
from bs4 import BeautifulSoup
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

SPREADSHEET_ID = (os.environ.get("SPREADSHEET_ID") or "1ONHPQREesHZYJJxX3BldQthwyrFqxoHBizWGhjlUM5o").strip()
SHEET_NAME = (os.environ.get("SHEET_NAME") or "Sheet1").strip()

HEADERS = [
    "Date Found", "Company", "Role / Title", "Location", "Work Mode", "Portal",
    "Job Link", "Match %", "Salary / CTC", "Priority", "Why It Matches",
    "Missing / Risk Areas", "Resume Version Needed", "Application Status", "Notes"
]

PROFILE_KEYWORDS = {
    "genai": 12, "generative ai": 12, "llm": 10, "agentic": 10, "rag": 9,
    "ai architect": 12, "solution architect": 9, "principal architect": 12,
    "enterprise architect": 10, "director": 10, "associate director": 12,
    "cloud architect": 10, "gcp": 9, "aws": 6, "azure": 7,
    "python": 6, "langgraph": 8, "openai": 8, "mlops": 7, "llmops": 8,
    "healthcare": 9, "digital transformation": 7, "platform engineering": 7,
    "conversational ai": 8, "dialogflow": 9, "architect": 8, "lead": 6
}

SEARCH_QUERIES = [
    "Associate Director GenAI Architect Bangalore jobs",
    "Principal AI Architect GenAI Bangalore jobs",
    "Director AI Transformation GenAI India jobs",
    "Enterprise AI Architect LLM RAG Bangalore jobs",
    "Cloud AI Architect GCP GenAI Bangalore jobs",
    "Healthcare GenAI Architect Bangalore jobs",
    "GenAI Practice Lead Bangalore jobs",
    "LLMOps Architect India jobs",
    "Generative AI Solution Architect India jobs",
    "AI Transformation Director Bangalore jobs",
]


def get_sheets_service():
    raw = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")
    if not raw:
        raise RuntimeError("Missing GOOGLE_SERVICE_ACCOUNT_JSON secret")
    info = json.loads(raw)
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = Credentials.from_service_account_info(info, scopes=scopes)
    return build("sheets", "v4", credentials=creds)


def ensure_headers(service):
    service.spreadsheets().values().update(
        spreadsheetId=SPREADSHEET_ID,
        range=f"{SHEET_NAME}!A1:O1",
        valueInputOption="USER_ENTERED",
        body={"values": [HEADERS]},
    ).execute()


def existing_links(service):
    result = service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID,
        range=f"{SHEET_NAME}!G2:G10000",
    ).execute()
    return {row[0].strip() for row in result.get("values", []) if row}


def clean(text):
    return re.sub(r"\s+", " ", text or "").strip()


def score_job(title, snippet):
    text = f"{title} {snippet}".lower()
    score = 45
    reasons = []
    for keyword, weight in PROFILE_KEYWORDS.items():
        if keyword in text:
            score += weight
            reasons.append(keyword)
    if "intern" in text or "fresher" in text or "junior" in text:
        score -= 35
    score = max(0, min(98, score))
    priority = "P1" if score >= 85 else "P2" if score >= 70 else "P3"
    why = ", ".join(reasons[:10]) if reasons else "General senior AI/cloud architecture keyword match"
    risk = "Validate seniority, compensation, and hands-on GenAI depth"
    resume_version = "GenAI + Cloud Executive Resume"
    return score, priority, why, risk, resume_version


def infer_company(title):
    for sep in [" - ", " | ", " at "]:
        if sep in title:
            return clean(title.split(sep)[-1])[:80]
    return "To verify"


def search_jobs():
    jobs = []
    for query in SEARCH_QUERIES:
        url = "https://www.bing.com/search?q=" + quote_plus(query + " apply")
        resp = requests.get(url, timeout=20, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(resp.text, "html.parser")
        for item in soup.select("li.b_algo")[:10]:
            title_el = item.select_one("h2")
            link_el = item.select_one("h2 a")
            snippet_el = item.select_one("p")
            if not title_el or not link_el:
                continue
            title = clean(title_el.get_text(" "))
            link = link_el.get("href")
            snippet = clean(snippet_el.get_text(" ") if snippet_el else "")
            lower = f"{title} {snippet} {link}".lower()
            if not any(term in lower for term in ["job", "career", "linkedin", "naukri", "foundit", "indeed", "greenhouse", "lever", "workday", "apply"]):
                continue
            score, priority, why, risk, resume_version = score_job(title, snippet)
            jobs.append({
                "company": infer_company(title),
                "title": title,
                "location": "Bangalore / India / Remote",
                "work_mode": "Hybrid/Remote/On-site to verify",
                "portal": "Bing/Public web",
                "link": link,
                "score": score,
                "priority": priority,
                "why": why,
                "risk": risk,
                "resume_version": resume_version,
                "notes": snippet[:450],
            })
    unique = {job["link"]: job for job in jobs}
    return sorted(unique.values(), key=lambda x: x["score"], reverse=True)[:30]


def append_jobs(service, jobs):
    known = existing_links(service)
    today = datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d")
    rows = []
    for job in jobs:
        print(f"Candidate score={job['score']} priority={job['priority']} title={job['title'][:100]}")
        if job["link"] in known:
            print("Skipping duplicate link")
            continue
        # Always write the top discovered public candidates; later stages can hard-filter.
        rows.append([
            today,
            job["company"],
            job["title"],
            job["location"],
            job["work_mode"],
            job["portal"],
            job["link"],
            job["score"],
            "Not listed",
            job["priority"],
            job["why"],
            job["risk"],
            job["resume_version"],
            "Not Applied",
            job["notes"],
        ])
    if rows:
        service.spreadsheets().values().append(
            spreadsheetId=SPREADSHEET_ID,
            range=f"{SHEET_NAME}!A:O",
            valueInputOption="USER_ENTERED",
            insertDataOption="INSERT_ROWS",
            body={"values": rows},
        ).execute()
    return len(rows)


def main():
    print(f"Using spreadsheet={SPREADSHEET_ID}, sheet={SHEET_NAME}")
    service = get_sheets_service()
    ensure_headers(service)
    jobs = search_jobs()
    added = append_jobs(service, jobs)
    print(f"Found {len(jobs)} candidate jobs; added {added} new rows.")


if __name__ == "__main__":
    main()
