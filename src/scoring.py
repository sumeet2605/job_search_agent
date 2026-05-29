from config import PROFILE_KEYWORDS, TARGET_ROLE_TERMS

EXCLUDE_TERMS = ["intern", "internship", "fresher", "trainee", "student", "entry level"]


def normalize(text: str) -> str:
    return (text or "").lower()


def score_job(title: str, snippet: str, link: str = ""):
    text = normalize(f"{title} {snippet} {link}")
    score = 35
    reasons = []
    risks = []

    for keyword, weight in PROFILE_KEYWORDS.items():
        if keyword in text:
            score += weight
            reasons.append(keyword)

    if any(term in text for term in TARGET_ROLE_TERMS):
        score += 12
        reasons.append("senior architecture or leadership title")
    else:
        risks.append("Seniority may need review")

    if "bangalore" in text or "bengaluru" in text or "india" in text or "remote" in text:
        score += 6
        reasons.append("location fit")

    for term in EXCLUDE_TERMS:
        if term in text:
            score -= 45
            risks.append(f"Unsuitable level indicator: {term}")

    if not any(term in text for term in ["genai", "generative ai", "llm", "ai architect", "rag", "machine learning", "artificial intelligence"]):
        risks.append("AI or GenAI depth unclear")

    if not any(term in text for term in ["gcp", "aws", "azure", "cloud"]):
        risks.append("Cloud platform requirement unclear")

    score = max(0, min(98, score))
    priority = "P1" if score >= 85 else "P2" if score >= 70 else "P3"
    resume_version = "GenAI + Cloud Executive Resume" if score >= 75 else "Cloud/AI Architect Resume"
    why = ", ".join(dict.fromkeys(reasons[:12])) or "General senior AI and cloud architecture keyword match"
    risk_text = "; ".join(dict.fromkeys(risks[:5])) or "Validate compensation and exact seniority before applying"
    return score, priority, why, risk_text, resume_version


def should_write(job: dict, min_score: int) -> bool:
    if job.get("score", 0) < min_score:
        return False
    title = normalize(job.get("title", ""))
    if any(term in title for term in EXCLUDE_TERMS):
        return False
    return True
