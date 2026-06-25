from __future__ import annotations

import re

from ..models import Experience

DATE_LINE = re.compile(
    r"(January|February|March|April|May|June|July|August|September|October|November|December|"
    r"Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Oct|Nov|Dec)"
    r".*\d{4}.*(Present|\d{4})",
    re.I,
)
BULLET_START = re.compile(r"^[•\uf0b7\u2022\-–]\s*|^\uFFFD\s*")
TITLE_HINT = re.compile(
    r"\b(Engineer|Developer|Architect|Manager|Lead|Director|Analyst|Consultant|Intern|Specialist)\b",
    re.I,
)
ACTION_START = re.compile(
    r"^(Led|Built|Created|Implemented|Migrated|Re-architected|Productionized|Designed|"
    r"Developed|Managed|Owned|Automated|Reduced|Improved|Architected|Delivered|Established)",
    re.I,
)


def is_malformed_experience(exp: Experience) -> bool:
    """Detect experiences broken by PDF parsing (avoid false-positive audit flags)."""
    title = (exp.title or "").strip()
    company = (exp.company or "").strip()

    if DATE_LINE.search(title) or re.search(r"\(\d+\s+years?\)", title, re.I):
        return True
    if len(title) > 90 or len(company) > 90:
        return True
    if title and ACTION_START.match(title):
        return True
    if company and (company[0].isdigit() or ACTION_START.match(company)):
        return True
    if company.count(",") >= 2 and not TITLE_HINT.search(company):
        return True
    if title in {"and Keboola.", "Silver, and Gold layers."}:
        return True
    return False


def experience_label(exp: Experience) -> str:
    if is_malformed_experience(exp):
        return "experiência (revise título/empresa — PDF pode ter quebrado o parse)"
    return f"{exp.title or 'cargo sem título'} @ {exp.company or '—'}"
