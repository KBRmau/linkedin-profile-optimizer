from __future__ import annotations

import uuid
from dataclasses import dataclass
from pathlib import Path

from .audit.rules import Finding, audit_profile
from .dev_presets import DEFAULT_TARGET, DEV_ROLES
from .ingest.pdf_parser import parse_pdf
from .models import Profile, SSI, Target
from .report.render import render_llm_prompt, render_report


@dataclass
class AuditResult:
    profile: Profile
    findings: list[Finding]
    report_md: str
    prompt_md: str
    score: int
    critical_count: int
    warning_count: int


def _positioning_score(findings: list[Finding]) -> int:
    penalty = 0
    for f in findings:
        if f.severity == "critical":
            penalty += 15
        elif f.severity == "warning":
            penalty += 6
        elif f.severity == "info":
            penalty += 2
    return max(0, 100 - penalty)


def build_target(
    role_key: str,
    market: str,
    seniority: str,
    language: str,
    custom_role: str = "",
) -> Target:
    preset = DEV_ROLES.get(role_key, {})
    role = custom_role.strip() or preset.get("role", role_key.replace("-", " ").title())
    keywords = list(preset.get("keywords", []))
    return Target(
        role=role,
        audience=DEFAULT_TARGET["audience"],
        market=market,
        seniority=seniority,
        language=language,
        tone=DEFAULT_TARGET["tone"],
        keywords=keywords,
    )


def run_audit_from_pdf(
    pdf_path: str | Path,
    target: Target,
    ssi: SSI,
) -> AuditResult:
    profile = parse_pdf(pdf_path)
    profile.target = target
    profile.ssi = ssi
    findings = audit_profile(profile)
    report_md = render_report(profile, findings)
    prompt_md = render_llm_prompt(profile, findings)
    return AuditResult(
        profile=profile,
        findings=findings,
        report_md=report_md,
        prompt_md=prompt_md,
        score=_positioning_score(findings),
        critical_count=sum(1 for f in findings if f.severity == "critical"),
        warning_count=sum(1 for f in findings if f.severity == "warning"),
    )


def save_upload(file_bytes: bytes, suffix: str, upload_dir: Path) -> Path:
    upload_dir.mkdir(parents=True, exist_ok=True)
    path = upload_dir / f"{uuid.uuid4().hex}{suffix}"
    path.write_bytes(file_bytes)
    return path
