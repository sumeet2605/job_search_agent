import re
from urllib.parse import quote_plus

import requests
from bs4 import BeautifulSoup

from config import MAX_RESULTS_TO_WRITE, MIN_WRITE_SCORE, SEARCH_QUERIES, SHEET_NAME, SPREADSHEET_ID
from scoring import score_job, should_write
from sheets_client import append_unique, get_service, setup_workbook


def clean(text):
    return re.sub(r"\s+", " ", text or "").strip()


def infer_company(title):
    for sep in [" - ", " | ", " at "]:
        if sep in title:
            return clean(title.split(sep)[-1])[:80]
    return "To verify"


def infer_portal(link):
    lower = (link or "").lower()
    if "linkedin" in lower:
        return "LinkedIn"
    if "naukri" in lower:
        return "Naukri"
    if "foundit" in lower or "monster" in lower:
        return "Foundit"
    if "indeed" in lower:
        return "Indeed"
    if "greenhouse" in lower:
        return "Greenhouse"
    if "lever" in lower:
        return "Lever"
    if "workday" in lower or "myworkdayjobs" in lower:
        return "Workday"
    if "careers" in lower:
        return "Company Careers"
    return "Public web"


def infer_location(title, snippet):
    text = f"{title} {snippet}".lower()
    if "remote" in text:
        return "Remote / India"
    if "bengaluru" in text or "bangalore" in text:
        return "Bangalore"
    if "india" in text:
        return "India"
    return "Bangalore / India / Remote"


def search_jobs():
    jobs = []
    for query in SEARCH_QUERIES:
        url = "https://www.bing.com/search?q=" + quote_plus(query + " apply")
        print(f"Searching: {query}")
        try:
            resp = requests.get(url, timeout=20, headers={"User-Agent": "Mozilla/5.0"})
            resp.raise_for_status()
        except Exception as exc:
            print(f"Search failed for query={query}: {exc}")
            continue

        soup = BeautifulSoup(resp.text, "html.parser")
        for item in soup.select("li.b_algo")[:10]:
            title_el = item.select_one("h2")
            link_el = item.select_one("h2 a")
            snippet_el = item.select_one("p")
            if not title_el or not link_el:
                continue

            title = clean(title_el.get_text(" "))
            link = link_el.get("href") or ""
            snippet = clean(snippet_el.get_text(" ") if snippet_el else "")
            lower = f"{title} {snippet} {link}".lower()

            if not any(term in lower for term in ["job", "career", "linkedin", "naukri", "foundit", "indeed", "greenhouse", "lever", "workday", "apply"]):
                continue

            score, priority, why, risk, resume_version = score_job(title, snippet, link)
            jobs.append({
                "company": infer_company(title),
                "title": title,
                "location": infer_location(title, snippet),
                "work_mode": "Hybrid/Remote/On-site to verify",
                "portal": infer_portal(link),
                "link": link,
                "score": score,
                "priority": priority,
                "why": why,
                "risk": risk,
                "resume_version": resume_version,
                "salary": "Not listed",
                "status": "Not Applied",
                "notes": snippet[:450],
            })

    unique = {job["link"]: job for job in jobs if job.get("link")}
    ranked = sorted(unique.values(), key=lambda x: x["score"], reverse=True)
    return ranked[:MAX_RESULTS_TO_WRITE]


def main():
    print(f"Using spreadsheet={SPREADSHEET_ID}, primary_sheet={SHEET_NAME}, min_score={MIN_WRITE_SCORE}")
    service = get_service()
    setup_workbook(service)

    jobs = search_jobs()
    recommended = [job for job in jobs if should_write(job, MIN_WRITE_SCORE)]
    top_recommended = [job for job in recommended if job.get("priority") in ["P1", "P2"]]

    for job in jobs:
        print(f"Candidate score={job['score']} priority={job['priority']} portal={job['portal']} title={job['title'][:120]}")

    added_all = append_unique(service, SHEET_NAME, jobs)
    added_rec = append_unique(service, "Recommended", top_recommended)

    print(f"Found {len(jobs)} candidate jobs; added_all={added_all}; recommended={len(top_recommended)}; added_recommended={added_rec}")


if __name__ == "__main__":
    main()
