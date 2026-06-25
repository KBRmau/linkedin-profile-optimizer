from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


MARKETS = {"brasil", "gringa"}

MARKET_LABELS = {
    "brasil": "Brasil",
    "gringa": "Gringa",
}
SENIORITIES = {"junior", "mid", "senior", "staff", "lead", "manager", "executive"}
AUDIENCES = {"recruiters", "hiring-managers", "founders", "clients", "investors", "partners"}
TONES = {"technical", "executive", "sales", "founder", "recruiter-friendly"}
LANGUAGES = {"pt", "en", "bilingual"}


@dataclass
class Target:
    """The opportunity the profile should attract."""

    role: str = ""
    audience: str = ""
    market: str = ""
    seniority: str = ""
    language: str = ""
    tone: str = ""
    keywords: list[str] = field(default_factory=list)
    job_descriptions: list[str] = field(default_factory=list)

    @property
    def expects_english(self) -> bool:
        return self.market == "gringa" or self.language in {"en", "bilingual"}


@dataclass
class Experience:
    title: str = ""
    company: str = ""
    start: str = ""
    end: str = ""
    description: str = ""
    bullets: list[str] = field(default_factory=list)
    skills: list[str] = field(default_factory=list)


@dataclass
class Education:
    school: str = ""
    degree: str = ""
    field_of_study: str = ""
    start: str = ""
    end: str = ""


@dataclass
class SSI:
    """Social Selling Index, each pillar 0-25, total 0-100."""

    professional_brand: Optional[float] = None
    find_people: Optional[float] = None
    engage_insights: Optional[float] = None
    build_relationships: Optional[float] = None

    @property
    def total(self) -> Optional[float]:
        parts = [
            self.professional_brand,
            self.find_people,
            self.engage_insights,
            self.build_relationships,
        ]
        if any(p is None for p in parts):
            return None
        return round(sum(p for p in parts if p is not None), 1)


@dataclass
class Profile:
    name: str = ""
    headline: str = ""
    about: str = ""
    current_title: str = ""
    location: str = ""
    experiences: list[Experience] = field(default_factory=list)
    education: list[Education] = field(default_factory=list)
    skills: list[str] = field(default_factory=list)
    certifications: list[str] = field(default_factory=list)
    languages: list[str] = field(default_factory=list)
    featured: list[str] = field(default_factory=list)
    recent_posts: list[str] = field(default_factory=list)
    ssi: SSI = field(default_factory=SSI)
    target: Target = field(default_factory=Target)
