from __future__ import annotations

from ..dev_presets import DEV_ROLES
from ..models import Target

HEADLINE_EXAMPLE = (
    "Senior Data Engineer | Data Platform, CDP & Reliability | "
    "GCP · Airflow · BigQuery · Spark · Terraform · AI Automation"
)

HEADLINE_FORMAT = (
    "{Posição} | {Áreas de trabalho mais fortes} | {Tecnologias com ·}"
)

SENIORITY_LABELS = {
    "junior": "Junior",
    "mid": "",
    "senior": "Senior",
    "staff": "Staff",
    "lead": "Tech Lead",
    "manager": "",
    "executive": "",
}


def headline_segments(text: str) -> list[str]:
    return [part.strip() for part in (text or "").split("|")]


def find_preset(target: Target) -> dict:
    role_lower = (target.role or "").lower()
    for preset in DEV_ROLES.values():
        preset_role = preset.get("role", "").lower()
        if preset_role and (preset_role in role_lower or role_lower in preset_role):
            return preset
    for key, preset in DEV_ROLES.items():
        if key.replace("-", " ") in role_lower:
            return preset
    return {}


def suggest_headline(target: Target, preset: dict | None = None) -> str:
    preset = preset or find_preset(target)
    seniority = SENIORITY_LABELS.get(target.seniority or "", "")
    role = target.role or preset.get("role", "Engineer")
    position = f"{seniority} {role}".strip() if seniority else role
    areas = preset.get("headline_areas", "Core domain & specialty")
    techs = preset.get("headline_tech")
    if not techs and target.keywords:
        techs = " · ".join(word.upper() if len(word) <= 4 else word.title() for word in target.keywords[:6])
    if not techs:
        techs = "Tech stack · Tools · Platforms"
    return f"{position} | {areas} | {techs}"


def validate_headline_structure(text: str) -> tuple[bool, str]:
    parts = headline_segments(text)
    if len(parts) != 3:
        return False, (
            f"Use 3 blocos separados por |: {HEADLINE_FORMAT}. "
            f"Ex: {HEADLINE_EXAMPLE}"
        )
    if any(not part for part in parts):
        return False, "Cada bloco entre | precisa ter conteúdo."
    if len(parts[0]) < 5:
        return False, "1º bloco: cargo/posição (ex: Senior Data Engineer)."
    if len(parts[1]) < 5:
        return False, "2º bloco: áreas de trabalho mais fortes (ex: Data Platform, CDP & Reliability)."
    if len(parts[2]) < 5:
        return False, (
            "3º bloco: tecnologias que você usa ou quer ser contactado por, "
            "separadas com · (ex: GCP · Airflow · BigQuery)."
        )
    return True, ""
