from __future__ import annotations

from ..audit.content import ABOUT_EXAMPLE, BULLET_EXAMPLE, BULLET_FORMAT, MAX_BULLETS_PER_EXPERIENCE
from ..audit.headline import HEADLINE_EXAMPLE, HEADLINE_FORMAT, suggest_headline
from ..audit.rules import Finding
from ..audit.ssi import interpret_ssi
from ..models import Profile

SEVERITY_ICON = {"critical": "[CRÍTICO]", "warning": "[ALERTA]", "info": "[INFO]", "ok": "[OK]"}
SEVERITY_ORDER = {"critical": 0, "warning": 1, "info": 2, "ok": 3}


def _score(findings: list[Finding]) -> int:
    penalty = 0
    for f in findings:
        if f.severity == "critical":
            penalty += 15
        elif f.severity == "warning":
            penalty += 6
        elif f.severity == "info":
            penalty += 2
    return max(0, 100 - penalty)


def render_report(profile: Profile, findings: list[Finding]) -> str:
    t = profile.target
    score = _score(findings)
    lines: list[str] = []
    lines.append(f"# LinkedIn Positioning Audit — {profile.name or 'Perfil'}")
    lines.append("")
    lines.append(f"**Cargo-alvo:** {t.role or '—'}  ")
    lines.append(f"**Público:** {t.audience or '—'} · **Mercado:** {t.market or '—'} · "
                 f"**Senioridade:** {t.seniority or '—'} · **Idioma:** {t.language or '—'} · "
                 f"**Tom:** {t.tone or '—'}")
    lines.append("")
    lines.append(f"**Score de posicionamento (heurístico):** {score}/100")
    lines.append("")

    ssi = interpret_ssi(profile.ssi)
    lines.append("## SSI")
    if ssi["total"] is None:
        lines.append("SSI não informado. Acesse https://www.linkedin.com/sales/ssi e preencha os 4 pilares.")
    else:
        lines.append(f"**Total:** {ssi['total']}/100")
        lines.append("")
        lines.append("| Pilar | Score | Status | Ação |")
        lines.append("|-------|-------|--------|------|")
        for p in ssi["pillars"]:
            lines.append(f"| {p['label']} ({p['color_pt']}) | {p['score']}/25 | {p['rating']} | {p['advice']} |")
        if ssi["weakest"]:
            lines.append("")
            w = ssi["weakest"]
            lines.append(f"**Prioridade SSI:** {w['label']} ({w['color_pt']}) — {w['advice']}")
        lines.append("")
        lines.append("### Dicas por pilar SSI")
        for p in ssi["pillars"]:
            lines.append("")
            lines.append(f"#### {p['color_pt']} — {p['label']} ({p['score']}/25 · {p['rating']})")
            lines.append(f"_{p['meaning']}_")
            for tip in p["tips"]:
                lines.append(f"- {tip}")
        if ssi.get("action_plan"):
            lines.append("")
            lines.append("### Plano rápido SSI (2 pilares mais fracos)")
            for tip in ssi["action_plan"]:
                lines.append(f"- {tip}")
    lines.append("")

    lines.append("## Diagnóstico por área")
    grouped: dict[str, list[Finding]] = {}
    for f in findings:
        grouped.setdefault(f.area, []).append(f)
    for area in grouped:
        items = sorted(grouped[area], key=lambda x: SEVERITY_ORDER[x.severity])
        lines.append("")
        lines.append(f"### {area.capitalize()}")
        for f in items:
            icon = SEVERITY_ICON[f.severity]
            line = f"- {icon} {f.message}"
            if f.suggestion:
                line += f" → {f.suggestion}"
            lines.append(line)

    crit = [f for f in findings if f.severity == "critical"]
    warn = [f for f in findings if f.severity == "warning"]
    lines.append("")
    lines.append("## Plano de ação (prioridade)")
    n = 1
    for f in crit + warn:
        lines.append(f"{n}. {f.message} {('— ' + f.suggestion) if f.suggestion else ''}".rstrip())
        n += 1
    if n == 1:
        lines.append("Nenhum item crítico ou de alerta. Foque em otimizações `info` e em conteúdo.")
    lines.append("")
    return "\n".join(lines)


def render_llm_prompt(profile: Profile, findings: list[Finding]) -> str:
    t = profile.target
    diag = "\n".join(
        f"- [{f.severity}] {f.area}: {f.message}" for f in findings if f.severity != "ok"
    )

    def exp_block() -> str:
        out = []
        for e in profile.experiences:
            out.append(f"### {e.title} @ {e.company} ({e.start}–{e.end})")
            if e.description:
                out.append(e.description)
            for b in e.bullets:
                out.append(f"- {b}")
        return "\n".join(out) if out else "(sem experiências)"

    headline_example = suggest_headline(profile.target)

    return f"""You are a LinkedIn positioning strategist, recruiter, personal branding expert, and career copywriter.

Transform this profile into a targeted sales page for a specific opportunity.

TARGET
- Role/opportunity: {t.role or "(ask user)"}
- Audience to attract: {t.audience or "(ask user)"}
- Market: {t.market or "(ask user)"}
- Seniority: {t.seniority or "(ask user)"}
- Output language: {t.language or "(ask user)"}
- Tone: {t.tone or "(ask user)"}
- Keywords: {", ".join(t.keywords) or "(none provided)"}

CURRENT PROFILE
- Name: {profile.name}
- Headline: {profile.headline}
- About:
{profile.about or "(empty)"}

- Experiences:
{exp_block()}

- Skills: {", ".join(profile.skills) or "(none)"}
- Languages: {", ".join(profile.languages) or "(none)"}
- Certifications: {", ".join(profile.certifications) or "(none)"}
- Education: {", ".join(e.school for e in profile.education) or "(none)"}
- Featured: {", ".join(profile.featured) or "(none)"}

RULE-BASED AUDIT FINDINGS
{diag or "(none)"}

PRODUCE
1. Positioning diagnosis (2-3 sentences).
2. Best target persona for this profile.
3. 5 optimized headline options (use the target language/market).
   MANDATORY FORMAT for every headline option:
   {HEADLINE_FORMAT}
   Canonical example: {HEADLINE_EXAMPLE}
   Suggested for this profile: {headline_example}
   - Block 1: position/title (include seniority when relevant)
   - Block 2: strongest work areas / domains
   - Block 3: technologies separated by middle dot (·) — tools you use or want recruiters to contact you for
4. 3 About versions: short, balanced, strong.
   Follow this narrative model (scale, companies, domains, stack list at end):
   {ABOUT_EXAMPLE}
5. Rewritten experience sections — max {MAX_BULLETS_PER_EXPERIENCE} bullets per role.
   Each bullet (~3 lines max): what you did + highlighted metrics + technologies + business impact.
   Canonical bullet example:
   {BULLET_EXAMPLE}
   Format rule: {BULLET_FORMAT}
6. Recommended skills and keyword clusters (note: LinkedIn PDF only exports top 3 skills).
7. Featured section recommendations.
8. Banner / visual direction.
9. 5 post ideas to reinforce the positioning.
10. Final LinkedIn optimization checklist.

RULES
- Do NOT invent experience or metrics. If a metric is missing, mark it as [ADD METRIC].
- Do NOT make the profile generic.
- Every headline MUST follow: Posição | Áreas | Tecnologias (with · in block 3).
- Max {MAX_BULLETS_PER_EXPERIENCE} bullets per experience; keep each bullet ~3 lines.
- For Gringa market: profile must list English in Languages section.
- Prioritize clarity, credibility, and market fit.
- Use the language of the target role and market.
- Make it readable for humans and searchable for recruiters.
"""
