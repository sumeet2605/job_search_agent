import os

SPREADSHEET_ID = (os.environ.get("SPREADSHEET_ID") or "1ONHPQREesHZYJJxX3BldQthwyrFqxoHBizWGhjlUM5o").strip()
SHEET_NAME = (os.environ.get("SHEET_NAME") or "Sheet1").strip()
MIN_WRITE_SCORE = int(os.environ.get("MIN_WRITE_SCORE", "62"))
MAX_RESULTS_TO_WRITE = int(os.environ.get("MAX_RESULTS_TO_WRITE", "25"))

HEADERS = [
    "Date Found", "Company", "Role / Title", "Location", "Work Mode", "Portal",
    "Job Link", "Match %", "Salary / CTC", "Priority", "Why It Matches",
    "Missing / Risk Areas", "Resume Version Needed", "Application Status", "Notes"
]

TARGET_ROLE_TERMS = [
    "associate director", "director", "principal architect", "enterprise architect",
    "solution architect", "ai architect", "cloud architect", "practice lead",
    "head of ai", "ai transformation", "platform engineering"
]

NEGATIVE_TERMS = [
    "intern", "internship", "fresher", "junior", "graduate trainee", "student", "entry level",
    "bpo", "sales executive", "telecaller", "data entry"
]

PROFILE_KEYWORDS = {
    "associate director": 16, "director": 12, "principal architect": 16,
    "enterprise architect": 13, "solution architect": 11, "ai architect": 16,
    "cloud architect": 12, "genai": 15, "generative ai": 15, "llm": 12,
    "agentic": 11, "rag": 11, "llmops": 10, "mlops": 9, "langgraph": 10,
    "openai": 9, "python": 7, "gcp": 11, "aws": 7, "azure": 8,
    "healthcare": 11, "digital transformation": 8, "platform engineering": 8,
    "conversational ai": 9, "dialogflow": 9, "stakeholder": 6, "leadership": 7
}

SEARCH_QUERIES = [
    "site:linkedin.com/jobs Associate Director GenAI Architect Bangalore",
    "site:linkedin.com/jobs Principal AI Architect GenAI Bangalore",
    "site:naukri.com GenAI Architect Director Bangalore",
    "site:naukri.com Principal AI Architect Bangalore",
    "site:foundit.in Associate Director AI Architect GenAI Bangalore",
    "site:foundit.in Principal GenAI Architect India",
    "site:indeed.com Principal AI Architect Bangalore GenAI",
    "site:greenhouse.io GenAI Architect India",
    "site:lever.co GenAI Architect India",
    "site:myworkdayjobs.com Principal AI Architect India",
    "site:careers.microsoft.com GenAI Architect India",
    "site:careers.google.com AI Architect India",
    "site:oracle.com careers Principal Architect AI GenAI Bangalore",
    "site:careers.gehealthcare.com AI Architect Bangalore",
    "site:salesforce.com careers Generative AI Architect India",
    "site:servicenow.com careers AI Architect India",
    "Associate Director GenAI Architect Bangalore jobs",
    "Principal AI Architect GenAI Bangalore jobs",
    "Director AI Transformation GenAI India jobs",
    "Enterprise AI Architect LLM RAG Bangalore jobs",
    "Cloud AI Architect GCP GenAI Bangalore jobs",
    "Healthcare GenAI Architect Bangalore jobs",
    "GenAI Practice Lead Bangalore jobs",
    "LLMOps Architect India jobs",
]
