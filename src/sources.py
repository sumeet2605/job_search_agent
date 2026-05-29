from urllib.parse import quote_plus

import requests
from bs4 import BeautifulSoup

from scoring import score_job

HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120 Safari/537.36"}
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


def fetch_html(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=20)
        response.raise_for_status()
        return response.text
    except Exception as exc:
        print(f"Source fetch failed: {url} :: {exc}")
        return ""


def search_naukri():
    jobs = []
    for keyword in KEYWORDS:
        url = f"https://www.naukri.com/{quote_plus(keyword).replace('+', '-')}-jobs-in-bangalore"
        html = fetch_html(url)
        soup = BeautifulSoup(html, "html.parser")
        for card in soup.select("article, .srp-jobtuple-wrapper, .jobTuple")[:8]:
            title_el = card.select_one("a.title, .title a, a")
            if not title_el:
                continue
            title = clean(title_el.get_text(" "))
            link = title_el.get("href", "")
            snippet = clean(card.get_text(" "))
            if link and title:
                jobs.append(build_job(title, link, snippet, "Naukri"))
    return jobs


def search_indeed():
    jobs = []
    for keyword in KEYWORDS:
        url = f"https://in.indeed.com/jobs?q={quote_plus(keyword)}&l=Bengaluru%2C+Karnataka"
        html = fetch_html(url)
        soup = BeautifulSoup(html, "html.parser")
        for card in soup.select(".job_seen_beacon, .result, [data-jk]")[:8]:
            title_el = card.select_one("h2 a, a.jcs-JobTitle, a[data-jk]")
            if not title_el:
                continue
            title = clean(title_el.get_text(" "))
            href = title_el.get("href", "")
            link = href if href.startswith("http") else f"https://in.indeed.com{href}"
            company_el = card.select_one('[data-testid="company-name"], .companyName')
            location_el = card.select_one('[data-testid="text-location"], .companyLocation')
            snippet = clean(card.get_text(" "))
            jobs.append(build_job(title, link, snippet, "Indeed", clean(company_el.get_text(" ")) if company_el else "To verify", clean(location_el.get_text(" ")) if location_el else "Bangalore"))
    return jobs


def search_foundit():
    jobs = []
    for keyword in KEYWORDS:
        url = f"https://www.foundit.in/srp/results?query={quote_plus(keyword)}&locations=Bengaluru"
        html = fetch_html(url)
        soup = BeautifulSoup(html, "html.parser")
        for card in soup.select(".cardContainer, .jobTuple, .job-card, article")[:8]:
            title_el = card.select_one("a, .jobTitle a")
            if not title_el:
                continue
            title = clean(title_el.get_text(" "))
            href = title_el.get("href", "")
            link = href if href.startswith("http") else f"https://www.foundit.in{href}"
            snippet = clean(card.get_text(" "))
            jobs.append(build_job(title, link, snippet, "Foundit"))
    return jobs


def search_linkedin_public():
    jobs = []
    for keyword in KEYWORDS:
        url = f"https://www.linkedin.com/jobs/search?keywords={quote_plus(keyword)}&location=Bengaluru%2C%20Karnataka%2C%20India"
        html = fetch_html(url)
        soup = BeautifulSoup(html, "html.parser")
        for card in soup.select(".base-card, .jobs-search__results-list li")[:8]:
            title_el = card.select_one("h3, .base-search-card__title")
            link_el = card.select_one("a")
            company_el = card.select_one("h4, .base-search-card__subtitle")
            location_el = card.select_one(".job-search-card__location")
            if not title_el or not link_el:
                continue
            title = clean(title_el.get_text(" "))
            link = link_el.get("href", "")
            snippet = clean(card.get_text(" "))
            jobs.append(build_job(title, link, snippet, "LinkedIn", clean(company_el.get_text(" ")) if company_el else "To verify", clean(location_el.get_text(" ")) if location_el else "Bangalore"))
    return jobs


def search_greenhouse_lever_workday_fallback():
    jobs = []
    sites = ["greenhouse.io", "lever.co", "myworkdayjobs.com", "careers.microsoft.com", "careers.google.com", "careers.gehealthcare.com", "oracle.com", "salesforce.com", "servicenow.com"]
    for site in sites:
        for keyword in KEYWORDS[:4]:
            url = "https://www.bing.com/search?q=" + quote_plus(f"site:{site} {keyword} India job apply")
            html = fetch_html(url)
            soup = BeautifulSoup(html, "html.parser")
            for item in soup.select("li.b_algo")[:4]:
                title_el = item.select_one("h2")
                link_el = item.select_one("h2 a")
                snippet_el = item.select_one("p")
                if not title_el or not link_el:
                    continue
                title = clean(title_el.get_text(" "))
                link = link_el.get("href", "")
                snippet = clean(snippet_el.get_text(" ") if snippet_el else "")
                jobs.append(build_job(title, link, snippet, "Company Careers"))
    return jobs


def collect_jobs():
    all_jobs = []
    source_functions = [
        search_linkedin_public,
        search_naukri,
        search_indeed,
        search_foundit,
        search_greenhouse_lever_workday_fallback,
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
