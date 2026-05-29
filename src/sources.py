from urllib.parse import quote_plus

import requests
from bs4 import BeautifulSoup

from scoring import score_job

HEADERS = {"User-Agent": "Mozilla/5.0"}
KEYWORDS = [
    "Associate Director GenAI Architect",
    "Principal AI Architect GenAI",
    "Director AI Transformation",
    "Enterprise AI Architect LLM RAG",
    "Cloud AI Architect GCP GenAI",
    "Healthcare GenAI Architect",
    "GenAI Practice Lead",
    "LLMOps Architect",
]


def clean(text):
    return " ".join((text or "").split())


def build_job(title, link, snippet, portal, company="To verify", location="Bangalore / India / Remote"):
    score, priority, why, risk, resume_version = score_job(title, snippet, link)
    return {
        "company": company or "To verify",
        "title": clean(title),
        "location": location or "Bangalore / India / Remote",
        "work_mode": "Hybrid/Remote/On-site to verify",
        "portal": portal,
        "link": link,
        "score": score,
        "priority": priority,
        "why": why,
        "risk": risk,
        "resume_version": resume_version,
        "salary": "Not listed",
        "status": "Not Applied",
        "notes": clean(snippet)[:450],
    }


def get_json(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=25)
        r.raise_for_status()
        return r.json()
    except Exception as exc:
        print(f"API fetch failed: {url} :: {exc}")
        return None


def fetch_html(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=20)
        r.raise_for_status()
        return r.text
    except Exception as exc:
        print(f"Source fetch failed: {url} :: {exc}")
        return ""


def keyword_match(text):
    t = (text or "").lower()
    return any(k.lower().split()[0] in t for k in KEYWORDS) or any(x in t for x in ["genai", "llm", "architect", "cloud", "ai"])


def search_remotive_api():
    jobs = []
    data = get_json("https://remotive.com/api/remote-jobs?search=ai%20architect")
    for item in (data or {}).get("jobs", [])[:80]:
        title = item.get("title", "")
        desc = item.get("description", "")
        if not keyword_match(title + " " + desc):
            continue
        jobs.append(build_job(title, item.get("url", ""), desc, "Remotive API", item.get("company_name", "To verify"), item.get("candidate_required_location", "Remote")))
    return jobs


def search_remoteok_api():
    jobs = []
    data = get_json("https://remoteok.com/api")
    if not isinstance(data, list):
        return jobs
    for item in data[1:120]:
        title = item.get("position", "")
        desc = " ".join([item.get("description", ""), " ".join(item.get("tags", []) or [])])
        if not keyword_match(title + " " + desc):
            continue
        jobs.append(build_job(title, item.get("url", ""), desc, "RemoteOK API", item.get("company", "To verify"), item.get("location", "Remote")))
    return jobs


def search_arbeitnow_api():
    jobs = []
    data = get_json("https://www.arbeitnow.com/api/job-board-api")
    for item in (data or {}).get("data", [])[:100]:
        title = item.get("title", "")
        desc = item.get("description", "")
        if not keyword_match(title + " " + desc):
            continue
        jobs.append(build_job(title, item.get("url", ""), desc, "Arbeitnow API", item.get("company_name", "To verify"), item.get("location", "Remote/Global")))
    return jobs


def search_linkedin_public():
    jobs = []
    for keyword in KEYWORDS:
        url = f"https://www.linkedin.com/jobs/search?keywords={quote_plus(keyword)}&location=Bengaluru%2C%20Karnataka%2C%20India"
        soup = BeautifulSoup(fetch_html(url), "html.parser")
        for card in soup.select(".base-card, .jobs-search__results-list li")[:6]:
            title_el = card.select_one("h3, .base-search-card__title")
            link_el = card.select_one("a")
            company_el = card.select_one("h4, .base-search-card__subtitle")
            location_el = card.select_one(".job-search-card__location")
            if title_el and link_el:
                jobs.append(build_job(clean(title_el.get_text(" ")), link_el.get("href", ""), clean(card.get_text(" ")), "LinkedIn", clean(company_el.get_text(" ")) if company_el else "To verify", clean(location_el.get_text(" ")) if location_el else "Bangalore"))
    return jobs


def search_naukri():
    jobs = []
    for keyword in KEYWORDS:
        url = f"https://www.naukri.com/{quote_plus(keyword).replace('+', '-')}-jobs-in-bangalore"
        soup = BeautifulSoup(fetch_html(url), "html.parser")
        for card in soup.select("article, .srp-jobtuple-wrapper, .jobTuple")[:6]:
            title_el = card.select_one("a.title, .title a, a")
            if title_el:
                jobs.append(build_job(clean(title_el.get_text(" ")), title_el.get("href", ""), clean(card.get_text(" ")), "Naukri"))
    return jobs


def search_indeed():
    jobs = []
    for keyword in KEYWORDS:
        url = f"https://in.indeed.com/jobs?q={quote_plus(keyword)}&l=Bengaluru%2C+Karnataka"
        soup = BeautifulSoup(fetch_html(url), "html.parser")
        for card in soup.select(".job_seen_beacon, .result, [data-jk]")[:6]:
            title_el = card.select_one("h2 a, a.jcs-JobTitle, a[data-jk]")
            if title_el:
                href = title_el.get("href", "")
                link = href if href.startswith("http") else f"https://in.indeed.com{href}"
                jobs.append(build_job(clean(title_el.get_text(" ")), link, clean(card.get_text(" ")), "Indeed"))
    return jobs


def search_foundit():
    jobs = []
    for keyword in KEYWORDS:
        url = f"https://www.foundit.in/srp/results?query={quote_plus(keyword)}&locations=Bengaluru"
        soup = BeautifulSoup(fetch_html(url), "html.parser")
        for card in soup.select(".cardContainer, .jobTuple, .job-card, article")[:6]:
            title_el = card.select_one("a, .jobTitle a")
            if title_el:
                href = title_el.get("href", "")
                link = href if href.startswith("http") else f"https://www.foundit.in{href}"
                jobs.append(build_job(clean(title_el.get_text(" ")), link, clean(card.get_text(" ")), "Foundit"))
    return jobs


def search_company_fallback():
    jobs = []
    sites = ["greenhouse.io", "lever.co", "myworkdayjobs.com", "careers.microsoft.com", "careers.google.com", "careers.gehealthcare.com", "oracle.com", "salesforce.com", "servicenow.com"]
    for site in sites:
        for keyword in KEYWORDS[:4]:
            url = "https://www.bing.com/search?q=" + quote_plus(f"site:{site} {keyword} India job apply")
            soup = BeautifulSoup(fetch_html(url), "html.parser")
            for item in soup.select("li.b_algo")[:3]:
                title_el = item.select_one("h2")
                link_el = item.select_one("h2 a")
                snippet_el = item.select_one("p")
                if title_el and link_el:
                    jobs.append(build_job(clean(title_el.get_text(" ")), link_el.get("href", ""), clean(snippet_el.get_text(" ") if snippet_el else ""), "Company Careers"))
    return jobs


def collect_jobs():
    all_jobs = []
    source_functions = [
        search_remotive_api,
        search_remoteok_api,
        search_arbeitnow_api,
        search_linkedin_public,
        search_naukri,
        search_indeed,
        search_foundit,
        search_company_fallback,
    ]
    for fn in source_functions:
        try:
            found = fn()
            print(f"{fn.__name__}: found {len(found)} jobs")
            all_jobs.extend(found)
        except Exception as exc:
            print(f"{fn.__name__} failed: {exc}")
    unique = {job["link"]: job for job in all_jobs if job.get("link")}
    return sorted(unique.values(), key=lambda x: x["score"], reverse=True)
