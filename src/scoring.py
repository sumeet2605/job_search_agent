from config import PROFILE_KEYWORDS, TARGET_ROLE_TERMS

EXCLUDE_TERMS = ["intern", "internship", "fresher", "trainee", "student", "entry level", "sales", "regional vice president", "account executive"]
SENIOR_TERMS = ["principal", "director", "associate director", "enterprise architect", "solution architect", "solutions architect", "ai architect", "cloud architect", "practice lead", "head of"]
AI_TERMS = ["genai", "generative ai", "llm", "rag", "agentic", "machine learning", "artificial intelligence", "ai/ml", "ai & ml", "mlops", "llmops"]
CLOUD_TERMS = ["cloud", "gcp", "aws", "azure", "platform", "architecture", "infrastructure"]
BAD_ENGINEERING_ONLY = ["software engineer", "fullstack", "full stack", "frontend", "backend", "data engineer", "site reliability"]


def normalize(text: str) -> str:
    return (text or "").lower()


def has_any(text, terms):
    return any(term in text for term in terms)


def score_job(title: str, snippet: str, link: str = ""):
    title_text = normalize(title)
    text = normalize(f"{title} {snippet} {link}")
    score = 25
    reasons = []
    risks = []

    senior_fit = has_any(title_text, SENIOR_TERMS) or has_any(text, TARGET_ROLE_TERMS)
    ai_fit = has_any(text, AI_TERMS)
    cloud_fit = has_any(text, CLOUD_TERMS)

    if senior_fit:
        score += 24
        reasons.append("senior architect/director level")
    else:
        risks.append("Role seniority may be below target")

    if ai_fit:
        score += 24
        reasons.append("AI/GenAI/LLM fit")
    else:
        risks.append("AI/GenAI requirement unclear")

    if cloud_fit:
        score += 14
        reasons.append("cloud/platform architecture fit")
    else:
        risks.append("Cloud/platform architecture unclear")

    for keyword, weight in PROFILE_KEYWORDS.items():
        if keyword in text:
            score += min(weight, 6)
            reasons.append(keyword)

    if "bangalore" in text or "bengaluru" in text or "india" in text or "remote" in text:
        score += 5
        reasons.append("location fit")

    for term in EXCLUDE_TERMS:
        if term in text:
            score -= 40
            risks.append(f"Unsuitable indicator: {term}")

    if has_any(title_text, BAD_ENGINEERING_ONLY) and not has_any(title_text, ["architect", "director", "principal", "staff", "solutions"]):
        score -= 22
        risks.append("Engineering-only role, not architecture/director focused")

    if not (senior_fit and (ai_fit or cloud_fit)):
        score = min(score, 69)

    score = max(0, min(98, score))
    priority = "P1" if score >= 85 else "P2" if score >= 72 else "P3"
    resume_version = "GenAI + Cloud Executive Resume" if score >= 75 else "Cloud/AI Architect Resume"
    why = ", ".join(dict.fromkeys(reasons[:12])) or "Partial keyword match"
    risk_text = "; ".join(dict.fromkeys(risks[:6])) or "Validate compensation and exact seniority before applying"
    return score, priority, why, risk_text, resume_version


def should_write(job: dict, min_score: int) -> bool:
    title = normalize(job.get("title", ""))
    text = normalize(f"{job.get('title', '')} {job.get('notes', '')}")
    if any(term in text for term in EXCLUDE_TERMS):
        return False
    if job.get("score", 0) < min_score:
        return False
    return has_any(title, SENIOR_TERMS) and (has_any(text, AI_TERMS) or has_any(text, CLOUD_TERMS))
