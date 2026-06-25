from __future__ import annotations

import re
from pathlib import Path

from ..models import Education, Experience, Profile

# Canonical section -> header variants (EN / PT / ES) as exported by LinkedIn "Save to PDF".
SECTION_ALIASES: dict[str, list[str]] = {
    "summary": ["Summary", "About", "Resumo", "Sobre", "Extracto", "Acerca de"],
    "experience": ["Experience", "Experiência", "Experiencia"],
    "education": ["Education", "Formação acadêmica", "Formacao academica", "Educación", "Educacion", "Formación"],
    "certifications": [
        "Licenses & Certifications", "Licenses and Certifications", "Certifications",
        "Licenças e certificados", "Licencas e certificados", "Certificações", "Certificacoes",
        "Licencias y certificaciones", "Certificaciones",
    ],
    "skills": ["Skills", "Top Skills", "Competências", "Competencias", "Principais competências", "Aptitudes"],
    "languages": ["Languages", "Idiomas"],
    "honors": ["Honors & Awards", "Honras e prêmios", "Honras e premios", "Honores y premios"],
    "projects": ["Projects", "Projetos", "Proyectos"],
    "recommendations": ["Recommendations", "Recomendações", "Recomendacoes", "Recomendaciones"],
    "contact": ["Contact", "Contato", "Contacto"],
}

# Lowercased header text -> canonical section key.
HEADER_TO_CANONICAL: dict[str, str] = {
    variant.lower(): canonical
    for canonical, variants in SECTION_ALIASES.items()
    for variant in variants
}

PAGE_NOISE = re.compile(r"^(--\s*\d+\s+of\s+\d+\s*--|Page\s+\d+\s+of\s+\d+|Página\s+\d+\s+de\s+\d+)$", re.I)

MONTHS = (
    # English
    "January|February|March|April|May|June|July|August|September|October|November|December|"
    "Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Oct|Nov|Dec|"
    # Portuguese
    "janeiro|fevereiro|março|marco|abril|maio|junho|julho|agosto|setembro|outubro|novembro|dezembro|"
    "jan|fev|mar|abr|mai|jun|jul|ago|set|out|nov|dez|"
    # Spanish
    "enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre|"
    "ene|feb|abr|may|ago|sep|oct|nov|dic"
)
PRESENT_WORDS = r"Present|Presente|Atual|Actual|Actualidad|o momento|hoje|hoy"
DATE_LINE = re.compile(
    rf"({MONTHS})" rf".*\d{{4}}.*({PRESENT_WORDS}|\d{{4}})",
    re.I,
)
BULLET_START = re.compile(r"^[•\uf0b7\u2022\-–]\s*|^\uFFFD\s*")
TITLE_HINT = re.compile(
    r"\b(Engineer|Developer|Architect|Manager|Lead|Director|Analyst|Consultant|Intern|Specialist|"
    r"Engenheiro|Engenheira|Desenvolvedor|Desenvolvedora|Arquiteto|Arquiteta|Gerente|Analista|"
    r"Consultor|Consultora|Estagiário|Estagiaria|Especialista|Líder|Diretor|Diretora|"
    r"Ingeniero|Ingeniera|Desarrollador|Arquitecto|Gerente|Analista|Consultor|Becario|Especialista)\b",
    re.I,
)
ACTION_START = re.compile(
    r"^(Led|Built|Created|Implemented|Migrated|Re-architected|Productionized|Designed|"
    r"Developed|Managed|Owned|Automated|Reduced|Improved|Architected|Delivered|Established|"
    r"Liderei|Construí|Construi|Criei|Implementei|Migrei|Desenvolvi|Gerenciei|Automatizei|"
    r"Reduzi|Aumentei|Otimizei|Entreguei|Projetei|Arquitetei|Implementé|Desarrollé|Creé|Lideré)",
    re.I,
)
LOCATION_LINE = re.compile(
    r",\s*(Brazil|Brasil|United States|Estados Unidos|IL|SP|RJ|PR|UK|Remote|Remoto|"
    r"Portugal|España|Espanha|Mexico|México|Argentina)\s*$",
    re.I,
)


def _extract_text(path: str | Path) -> str:
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise RuntimeError(
            "pypdf is required for PDF parsing. Install with: pip install pypdf"
        ) from exc

    reader = PdfReader(str(path))
    pages = [page.extract_text() or "" for page in reader.pages]
    return "\n".join(pages)


def _split_sections(text: str) -> dict[str, str]:
    lines = text.splitlines()
    sections: dict[str, str] = {}
    current = "_top"
    buffer: list[str] = []

    for line in lines:
        canonical = HEADER_TO_CANONICAL.get(line.strip().lower())
        if canonical:
            # Preserve any text already collected for this section (e.g. sidebar split).
            existing = sections.get(current, "")
            sections[current] = (existing + "\n" + "\n".join(buffer)).strip() if existing else "\n".join(buffer).strip()
            current = canonical
            buffer = []
        else:
            buffer.append(line)
    existing = sections.get(current, "")
    sections[current] = (existing + "\n" + "\n".join(buffer)).strip() if existing else "\n".join(buffer).strip()
    return sections


def _clean_lines(block: str) -> list[str]:
    lines = []
    for ln in block.splitlines():
        s = ln.strip()
        if not s or PAGE_NOISE.match(s):
            continue
        lines.append(s)
    return lines


NAME_RE = re.compile(r"^[A-ZÀ-Ý][a-zà-ÿ'’.-]+(?:\s+[A-ZÀ-Ý][a-zà-ÿ'’.-]+){1,3}$")
SECTION_HEADER_SET = set(HEADER_TO_CANONICAL.keys())
SIDEBAR_MARKERS = SECTION_HEADER_SET | {"canonical"}


def _looks_like_name(line: str) -> bool:
    if not NAME_RE.match(line):
        return False
    if line.lower() in SIDEBAR_MARKERS:
        return False
    if any(ch.isdigit() for ch in line):
        return False
    return 2 <= len(line.split()) <= 4


def _find_name_and_headline(sections: dict[str, str]) -> tuple[str, str]:
    """Scan all sections for the 'Name' + 'Headline (with |)' pair.

    The LinkedIn PDF sidebar (Contact/Top Skills/Certifications) often flows
    into the main column, so name/headline can land in any section. The
    headline frequently wraps across lines (continuation starts with ·).
    """
    for block in sections.values():
        lines = _clean_lines(block)
        for idx, line in enumerate(lines):
            if "|" in line and len(line) > 15 and idx > 0:
                if _looks_like_name(lines[idx - 1]):
                    headline_parts = [line]
                    k = idx + 1
                    while k < len(lines):
                        nxt = lines[k]
                        low = nxt.lower()
                        if low in SECTION_HEADER_SET or low in SIDEBAR_MARKERS:
                            break
                        if nxt.startswith(("·", "•", "|")) or (
                            "·" in nxt and not DATE_LINE.match(nxt)
                        ):
                            headline_parts.append(nxt)
                            k += 1
                            continue
                        break
                    headline = " ".join(p.strip() for p in headline_parts)
                    headline = re.sub(r"\s{2,}", " ", headline).strip()
                    return lines[idx - 1].strip(), headline
    return "", ""


def _parse_identity(block: str) -> tuple[str, str, list[str], list[str]]:
    lines = _clean_lines(block)
    name, headline = "", ""
    skills: list[str] = []
    certifications: list[str] = []

    markers = {"top skills", "languages", "certifications", "licenses & certifications"}
    i = 0
    while i < len(lines):
        low = lines[i].lower()
        if low == "top skills":
            i += 1
            while i < len(lines) and lines[i].lower() not in markers and "|" not in lines[i]:
                if lines[i] and not lines[i].startswith("www."):
                    skills.append(lines[i])
                i += 1
            continue
        if low in ("certifications", "licenses & certifications", "licenses and certifications"):
            i += 1
            while i < len(lines) and lines[i].lower() not in markers and "|" not in lines[i]:
                if lines[i] and len(lines[i]) > 3:
                    certifications.append(lines[i])
                i += 1
            continue
        if "|" in lines[i] and len(lines[i]) > 25:
            headline = lines[i].replace("  ", " ").strip()
            if i > 0 and not lines[i - 1].startswith(("+", "www.", "http")):
                name = lines[i - 1]
            break
        i += 1

    if not name:
        for j, line in enumerate(lines):
            if re.match(r"^[A-Z][a-zA-Z''-]+ [A-Z][a-zA-Z''-]+", line) and len(line.split()) <= 5:
                if j + 1 >= len(lines):
                    continue
                parts: list[str] = []
                k = j + 1
                while k < len(lines):
                    if re.search(r",\s*(Brazil|United States|IL)\s*$", lines[k]):
                        break
                    if lines[k].lower().startswith("www.") or lines[k].startswith("+"):
                        k += 1
                        continue
                    parts.append(lines[k])
                    k += 1
                joined = " ".join(parts)
                if parts and ("Engineer" in joined or "Developer" in joined or "|" in joined or "·" in joined):
                    name = line
                    headline = joined.replace("  ", " ").strip()
                    break

    return name, headline, skills, certifications


def _strip_bullet(line: str) -> str:
    return BULLET_START.sub("", line).strip()


def _looks_like_company(name: str) -> bool:
    if not name or len(name) > 60:
        return False
    if name[0].isdigit() or ACTION_START.match(name):
        return False
    if re.search(r"\d", name):
        return False
    if BULLET_START.match(name):
        return False
    return True


def _looks_like_job_start(lines: list[str], i: int) -> bool:
    if i + 2 >= len(lines):
        return False
    company, title, third = lines[i], lines[i + 1], lines[i + 2]
    if not _looks_like_company(company):
        return False
    if BULLET_START.match(title):
        return False
    if DATE_LINE.match(title):
        return False
    if DATE_LINE.match(third):
        return bool(TITLE_HINT.search(title))
    if i + 3 < len(lines) and DATE_LINE.match(lines[i + 3]):
        return bool(TITLE_HINT.search(lines[i + 2]))
    return False


def _parse_experiences(block: str) -> list[Experience]:
    lines = _clean_lines(block)
    experiences: list[Experience] = []
    i = 0

    while i < len(lines):
        if BULLET_START.match(lines[i]) or DATE_LINE.match(lines[i]):
            i += 1
            continue
        if not _looks_like_job_start(lines, i):
            i += 1
            continue

        company = lines[i]
        title = lines[i + 1]
        i += 2

        while i < len(lines) and (
            DATE_LINE.match(lines[i])
            or LOCATION_LINE.search(lines[i])
            or (lines[i].endswith("Brazil") and "," in lines[i])
            or (lines[i].endswith("IL") and "," in lines[i])
        ):
            i += 1

        bullets: list[str] = []
        current: list[str] = []

        def flush() -> None:
            nonlocal current
            if current:
                bullets.append(" ".join(current).strip())
                current = []

        while i < len(lines):
            if _looks_like_job_start(lines, i):
                break
            line = lines[i]
            if BULLET_START.match(line):
                flush()
                current = [_strip_bullet(line)]
            elif ACTION_START.match(line) and (current or bullets):
                flush()
                current = [line]
            elif current:
                current.append(line)
            elif bullets and not _looks_like_job_start(lines, i):
                bullets[-1] = bullets[-1] + " " + line
            else:
                break
            i += 1

        flush()
        if title and not BULLET_START.match(title):
            experiences.append(Experience(company=company, title=title, bullets=bullets))

    return experiences


def _parse_languages(block: str) -> list[str]:
    lines = _clean_lines(block)
    languages: list[str] = []
    skip = {
        "elementary", "limited", "professional", "full", "native", "bilingual",
        "working", "proficiency", "professional working proficiency",
        "native or bilingual proficiency", "full professional proficiency",
    }
    for line in lines:
        low = line.lower()
        if low in skip or len(line) > 60:
            continue
        if re.match(r"^[A-Za-zÀ-ÿ ()-]+$", line):
            languages.append(line)
    return languages


def _parse_skills(block: str, name: str, headline: str) -> list[str]:
    head_fragments = {p.strip() for p in headline.split("|")} if headline else set()
    skills: list[str] = []
    for line in _clean_lines(block):
        if line == name or "|" in line or line.startswith(("·", "www.", "+", "http")):
            continue
        if line in head_fragments or len(line) <= 1 or len(line) > 60:
            continue
        if line == name or LOCATION_LINE.search(line):
            continue
        skills.append(line)
    return skills


def _parse_certifications(block: str, name: str, headline: str) -> list[str]:
    head_fragments = {p.strip() for p in headline.split("|")} if headline else set()
    certs: list[str] = []
    for line in _clean_lines(block):
        if line == name or "|" in line or line.startswith("·"):
            continue
        if line in head_fragments or len(line) <= 3:
            continue
        if _looks_like_name(line) or LOCATION_LINE.search(line):
            continue
        certs.append(line)
    return certs


def _parse_education(block: str) -> list[Education]:
    lines = _clean_lines(block)
    if not lines:
        return []
    school = lines[0]
    degree = lines[1] if len(lines) > 1 else ""
    return [Education(school=school, degree=degree)]


def parse_pdf(path: str | Path) -> Profile:
    """Best-effort parse of a LinkedIn 'Save to PDF' export."""
    text = _extract_text(path)
    sections = _split_sections(text)

    name, headline, skills, certs = _parse_identity(sections.get("_top", ""))

    # Name/headline often flow into another section (sidebar overflow). Scan globally.
    if not headline or "|" not in headline:
        scan_name, scan_headline = _find_name_and_headline(sections)
        if scan_headline:
            headline = scan_headline
            if scan_name:
                name = scan_name

    # Skills and certifications live in their own (canonical) sections.
    section_skills = _parse_skills(sections.get("skills", ""), name, headline)
    if section_skills:
        skills = section_skills

    section_certs = _parse_certifications(sections.get("certifications", ""), name, headline)
    if section_certs:
        certs = section_certs

    about = sections.get("summary", "")
    experiences = _parse_experiences(sections.get("experience", ""))
    education = _parse_education(sections.get("education", ""))
    languages = _parse_languages(sections.get("languages", ""))

    return Profile(
        name=name,
        headline=headline,
        about=about,
        current_title=experiences[0].title if experiences else "",
        experiences=experiences,
        education=education,
        skills=skills,
        certifications=certs,
        languages=languages,
    )
