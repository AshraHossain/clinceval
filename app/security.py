"""Input validation at the trust boundary: prompt-injection guard, PII redaction,
size limits. Applied to every query before it reaches the pipeline."""
import re

MAX_QUERY_CHARS = 2000

# Patterns that indicate an attempt to break out of the clinical-query context.
# Deliberately narrow: clinical text ("ignore the previous dose") must not trip them.
INJECTION_PATTERNS = [
    re.compile(r"ignore\s+(all\s+)?(previous|prior|above)\s+(instructions|prompts)", re.I),
    re.compile(r"\bsystem\s+prompt\b", re.I),
    re.compile(r"\byou\s+are\s+now\b.{0,40}\b(unrestricted|jailbroken|DAN)\b", re.I),
    re.compile(r"<\s*/?(script|iframe)\b", re.I),
    re.compile(r"\bdisregard\s+(your|the)\s+(rules|guidelines|rubric)\b", re.I),
]

# PII patterns — used to redact logs, never to block a query (a real clinical
# question may legitimately contain identifiers; we just must not persist them).
PII_PATTERNS = {
    "ssn": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    "mrn": re.compile(r"\bMRN[:\s#]*\d{5,10}\b", re.I),
    "email": re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.]+\b"),
    "phone": re.compile(r"\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]\d{3}[-.\s]\d{4}\b"),
}


def validate_query(query: str) -> str:
    """Return the stripped query or raise ValueError with a user-safe reason."""
    query = query.strip()
    if not query:
        raise ValueError("query must not be empty")
    if len(query) > MAX_QUERY_CHARS:
        raise ValueError(f"query exceeds {MAX_QUERY_CHARS} characters")
    for pattern in INJECTION_PATTERNS:
        if pattern.search(query):
            raise ValueError("query contains disallowed instruction-override content")
    return query


def redact_pii(text: str) -> str:
    """Replace PII with typed placeholders. Used on anything that gets logged."""
    for name, pattern in PII_PATTERNS.items():
        text = pattern.sub(f"[REDACTED-{name.upper()}]", text)
    return text
