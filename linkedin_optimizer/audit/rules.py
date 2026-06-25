from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

from ..models import Profile, Target
from .content import (
    ABOUT_EXAMPLE,
    BULLET_EXAMPLE,
    BULLET_FORMAT,
    MAX_BULLETS_PER_EXPERIENCE,
)
from .experience_quality import experience_label, is_malformed_experience
from .headline import HEADLINE_EXAMPLE, suggest_headline, validate_headline_structure

Severity = Literal["critical", "warning", "ok", "info"]

BUZZWORDS = {
    "passionate", "results-driven", "results driven", "hard-working", "hardworking",
    "team player", "self-motivated", "guru", "ninja", "rockstar", "wizard",
    "thought leader", "synergy", "go-getter", "detail-oriented", "motivated",
    "apaixonado", "proativo", "dinâmico", "comprometido", "esforçado",
}

ACTION_VERBS = {
    "led", "built", "designed", "shipped", "launched", "scaled", "reduced",
    "increased", "improved", "automated", "migrated", "delivered", "owned",
    "drove", "created", "implemented", "optimized", "architected", "managed",
    "liderei", "construí", "criei", "reduzi", "aumentei", "automatizei",
    "entreguei", "implementei", "otimizei", "escalei", "desenvolvi",
}

PT_STOPWORDS = {"de", "que", "para", "com", "uma", "não", "você", "como", "dos", "das", "meu", "minha"}
EN_STOPWORDS = {"the", "and", "with", "for", "your", "you", "this", "that", "from", "have", "are"}

METRIC_RE = re.compile(r"(\d+[\d.,]*\s?%|\$\s?\d|\bR\$\s?\d|\b\d[\d.,]*\s?(k|m|mi|mil|million|million|users|clientes|x)\b|\b\d+\b)", re.IGNORECASE)


@dataclass
class Finding:
    area: str
    severity: Severity
    message: str
    suggestion: str = ""
    fix_prompt: str = ""


def _tokens(text: str) -> set[str]:
    return set(re.findall(r"[a-zA-ZÀ-ÿ]+", (text or "").lower()))


def detect_language(text: str) -> str:
    toks = _tokens(text)
    if not toks:
        return "unknown"
    pt = len(toks & PT_STOPWORDS)
    en = len(toks & EN_STOPWORDS)
    if pt == en == 0:
        return "unknown"
    return "pt" if pt >= en else "en"


def _target_keywords(target: Target) -> set[str]:
    kws: set[str] = set()
    for source in [target.role, " ".join(target.keywords)]:
        kws |= _tokens(source)
    kws -= PT_STOPWORDS | EN_STOPWORDS
    return {k for k in kws if len(k) > 2}


def _has_metric(text: str) -> bool:
    return bool(METRIC_RE.search(text or ""))


def _has_action_verb(text: str) -> bool:
    return bool(_tokens(text) & ACTION_VERBS)


def _audit_headline(p: Profile, kws: set[str], findings: list[Finding]) -> None:
    h = p.headline or ""
    example = suggest_headline(p.target)
    if not h.strip():
        findings.append(Finding(
            "headline", "critical", "Headline vazia.",
            f"Use: Posição | Áreas fortes | Tecnologias (com ·). Ex: {example}",
        ))
        return

    valid_format, format_msg = validate_headline_structure(h)
    if not valid_format:
        findings.append(Finding("headline", "critical", "Headline fora do padrão.", format_msg))
    else:
        parts = h.split("|")
        tech_block = parts[2].strip()
        if "·" not in tech_block and "," in tech_block:
            findings.append(Finding(
                "headline", "warning",
                "No 3º bloco, prefira separar tecnologias com · em vez de vírgulas.",
                f"Ex: {HEADLINE_EXAMPLE.split('|')[2].strip()}",
            ))

    if len(h) < 40:
        findings.append(Finding("headline", "warning", f"Headline curta ({len(h)} chars).",
                                 "LinkedIn permite 220 chars; preencha os 3 blocos com detalhe."))
    found_kw = _tokens(h) & kws
    if kws and not found_kw:
        findings.append(Finding("headline", "critical",
                                 "Headline não contém palavras-chave do cargo-alvo.",
                                 f"Inclua termos como: {', '.join(sorted(kws)[:6])}."))
    buzz = {b for b in BUZZWORDS if b in h.lower()}
    if buzz:
        findings.append(Finding("headline", "warning",
                                 f"Buzzwords vazias na headline: {', '.join(sorted(buzz))}.",
                                 "Troque por stack, domínio e áreas concretas."))
    if valid_format and found_kw and len(h) >= 40 and not buzz:
        findings.append(Finding("headline", "ok", "Headline no padrão Posição | Áreas | Tecnologias."))


def _has_english_listed(languages: list[str]) -> bool:
    return any(re.search(r"\benglish\b", lang, re.I) for lang in languages)


def _audit_language(p: Profile, target: Target, findings: list[Finding]) -> None:
    if not target.expects_english:
        return

    if not _has_english_listed(p.languages):
        findings.append(Finding(
            "language", "critical",
            "Mercado Gringa, mas English não está listado em Languages.",
            "Adicione English (Professional working proficiency ou superior) no perfil.",
        ))

    sample = f"{p.headline}\n{p.about}"
    lang = detect_language(sample)
    if lang == "pt":
        findings.append(Finding(
            "language", "critical",
            "Mercado-alvo internacional, mas headline/about parecem estar em português.",
            "Traduza headline, about e experiências para inglês.",
        ))
    elif lang == "en" and _has_english_listed(p.languages):
        findings.append(Finding("language", "ok", "Perfil em inglês com English listado em Languages."))


def _audit_about(p: Profile, kws: set[str], findings: list[Finding]) -> None:
    a = p.about or ""
    about_guide = (
        "Modelo: abertura com anos + foco → empresa atual com escala/métricas → "
        "áreas de atuação → experiência anterior com provas → lista de domínios/stack."
    )
    if not a.strip():
        findings.append(Finding(
            "about", "critical", "Seção About vazia.",
            f"{about_guide} Ex: {ABOUT_EXAMPLE[:200]}…",
        ))
        return
    if len(a) < 300:
        findings.append(Finding(
            "about", "warning", f"About curto ({len(a)} chars).",
            "Aprofunde para ~1000-2000 chars com contexto, escala, empresas e stack.",
        ))
    if kws and not (_tokens(a) & kws):
        findings.append(Finding(
            "about", "warning",
            "About não menciona palavras-chave do cargo-alvo.",
            "Inclua termos do mercado-alvo para busca de recruiters.",
        ))
    if not _has_metric(a):
        findings.append(Finding(
            "about", "warning", "About sem números/provas concretas.",
            "Inclua pipelines, escala, % de melhoria, anos de experiência, clientes.",
        ))


BULLET_SUGGESTION = (
    f"{BULLET_FORMAT}. Ex: {BULLET_EXAMPLE}"
)


def _audit_experiences(p: Profile, kws: set[str], findings: list[Finding]) -> None:
    if not p.experiences:
        findings.append(Finding("experience", "critical", "Nenhuma experiência cadastrada.", ""))
        return

    malformed_count = sum(1 for exp in p.experiences if is_malformed_experience(exp))
    if malformed_count:
        findings.append(Finding(
            "experience", "info",
            f"{malformed_count} experiência(s) com parse incompleto do PDF.",
            "Revise título, empresa e bullets manualmente antes de confiar no diagnóstico.",
        ))

    for i, exp in enumerate(p.experiences, 1):
        if is_malformed_experience(exp):
            continue

        label = experience_label(exp)
        content = " ".join(exp.bullets) + " " + (exp.description or "")

        if not exp.bullets and not exp.description.strip():
            findings.append(Finding(
                "experience", "warning",
                f"[{label}] sem bullet points.",
                BULLET_SUGGESTION,
            ))
            continue

        if len(exp.bullets) > MAX_BULLETS_PER_EXPERIENCE:
            findings.append(Finding(
                "experience", "warning",
                f"[{label}] tem {len(exp.bullets)} bullets (máx {MAX_BULLETS_PER_EXPERIENCE}).",
                "Mantenha só os 5 impactos mais fortes por experiência.",
            ))

        quantified = sum(1 for b in exp.bullets if _has_metric(b))
        if exp.bullets and quantified == 0:
            findings.append(Finding(
                "experience", "warning",
                f"[{label}] nenhum bullet quantificado.",
                "Inclua métricas: %, tempo, escala, volume, redução de custo.",
            ))

        with_verb = sum(1 for b in exp.bullets if _has_action_verb(b))
        if exp.bullets and with_verb < max(1, len(exp.bullets) // 2):
            findings.append(Finding(
                "experience", "info",
                f"[{label}] poucos bullets começam com verbo de ação.",
                "Inicie com: Led, Built, Productionized, Migrated, Implemented…",
            ))

        long_bullets = [b for b in exp.bullets if len(b) > 320]
        if long_bullets:
            findings.append(Finding(
                "experience", "info",
                f"[{label}] bullet(s) muito longo(s).",
                "Mantenha ~3 linhas por bullet. Formato: ação + métrica + tech + impacto.",
            ))

        if i == 1 and kws and not (_tokens(exp.title) & kws) and not (_tokens(content) & kws):
            findings.append(Finding(
                "experience", "warning",
                f"[{label}] título atual não bate com o cargo-alvo.",
                "Alinhe o título (ou subtítulo) ao role buscado.",
            ))


def _audit_skills(p: Profile, kws: set[str], findings: list[Finding]) -> None:
    # PDF do LinkedIn exporta só "Top Skills" (geralmente 3) — não auditar quantidade.
    if not p.skills:
        return
    skill_tokens = _tokens(" ".join(p.skills))
    if kws and len(p.skills) > 3 and not (skill_tokens & kws):
        findings.append(Finding(
            "skills", "info",
            "Top skills do PDF podem não refletir todas as skills do perfil.",
            f"Fixe no LinkedIn as skills mais relevantes ao alvo: {', '.join(sorted(kws)[:6])}.",
        ))


def _audit_education(p: Profile, findings: list[Finding]) -> None:
    if not p.education:
        findings.append(Finding("education", "info", "Nenhuma formação conectada.",
                                 "Conecte a faculdade/instituição (mesmo em andamento) para credibilidade e rede de alumni."))
    if not p.certifications:
        findings.append(Finding(
            "education", "info",
            "Nenhuma certificação detectada no PDF (pode não ter sido capturada).",
            "Se não tiver, adicione certificações relevantes ao cargo-alvo.",
        ))


def _audit_featured(p: Profile, findings: list[Finding]) -> None:
    # Featured não é exportado no PDF do LinkedIn — sempre tratamos como dica.
    findings.append(Finding(
        "featured", "info",
        "Featured não vem no PDF — verifique manualmente se você tem uma seção em Destaque.",
        "Vale muito ter um Featured: certificação (ex: Azure Data Engineer no Credly), "
        "projeto no GitHub, artigo técnico ou case. Veja o exemplo na página.",
    ))


def _audit_job_preferences(p: Profile, findings: list[Finding]) -> None:
    # "Open to work" e Start date não vêm no PDF — dicas fixas de configuração.
    findings.append(Finding(
        "open_to_work", "info",
        "Open to Work: ative como \"Recruiters only\" para receber mais contatos.",
        "Evite \"All LinkedIn members\" (o badge #OpenToWork passa impressão de desespero). "
        "Recruiters only mostra disponibilidade só para quem usa o LinkedIn Recruiter. "
        "Veja o exemplo de configuração na página.",
    ))
    findings.append(Finding(
        "open_to_work", "info",
        "Start date: marque \"Immediately, I am actively applying\".",
        "Geralmente traz mais contatos do que \"Flexible / casually looking\", "
        "porque recrutadores priorizam quem está pronto para começar.",
    ))
    lang_hint = "inglês" if p.target.market == "gringa" else "do país onde você busca vaga"
    findings.append(Finding(
        "profile_language", "info",
        f"Profile language principal: use o idioma dos países-alvo ({lang_hint}).",
        "O Profile language principal deve ser o mesmo idioma dos países onde você busca "
        "emprego — tende a trazer melhores resultados na busca de recrutadores. "
        "Veja o exemplo na página.",
    ))


def audit_profile(profile: Profile) -> list[Finding]:
    kws = _target_keywords(profile.target)
    findings: list[Finding] = []
    _audit_headline(profile, kws, findings)
    _audit_language(profile, profile.target, findings)
    _audit_about(profile, kws, findings)
    _audit_experiences(profile, kws, findings)
    _audit_skills(profile, kws, findings)
    _audit_education(profile, findings)
    _audit_featured(profile, findings)
    _audit_job_preferences(profile, findings)

    from .fix_prompts import attach_fix_prompts
    attach_fix_prompts(findings, profile)
    return findings
