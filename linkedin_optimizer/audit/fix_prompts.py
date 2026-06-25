from __future__ import annotations

from ..models import Profile, Target
from .content import ABOUT_EXAMPLE, BULLET_EXAMPLE, BULLET_FORMAT, MAX_BULLETS_PER_EXPERIENCE
from .headline import HEADLINE_EXAMPLE, suggest_headline
from .rules import Finding

LINKEDIN_WHERE: dict[str, str] = {
    "headline": "LinkedIn → seu perfil → ícone de lápis ao lado da foto → campo **Headline** (abaixo do nome).",
    "about": "LinkedIn → Perfil → seção **About** → ícone de lápis.",
    "experience": "LinkedIn → Perfil → seção **Experience** → ícone de lápis na experiência indicada → descrição/bullets.",
    "skills": "LinkedIn → Perfil → seção **Skills** → ícone de + → adicione e fixe as 3 principais.",
    "language": "LinkedIn → Perfil → seção **Languages** → ícone de + → adicione English.",
    "education": "LinkedIn → Perfil → seção **Education** → adicionar ou editar formação.",
    "featured": "LinkedIn → Perfil → seção **Featured / Em destaque** → botão + → adicione link de certificação (Credly), projeto GitHub, artigo ou post.",
    "open_to_work": "LinkedIn → seu perfil → botão **Open to** / **Disponível para** → **Finding a new job** → configure Job titles, Locations, Start date e Visibility.",
    "profile_language": "LinkedIn → seu perfil → ícone de lápis (editar introdução) → campo **Profile language** → defina o idioma principal igual ao dos países-alvo.",
    "ssi": "LinkedIn → [Social Selling Index](https://www.linkedin.com/sales/ssi) — ações fora do perfil (rede, posts, mensagens).",
}


def _target_block(target: Target) -> str:
    return f"""- Cargo-alvo: {target.role or "—"}
- Mercado: {target.market or "—"}
- Senioridade: {target.seniority or "—"}
- Idioma do perfil: {target.language or "—"}
- Keywords: {", ".join(target.keywords) or "—"}"""


def _profile_excerpt(profile: Profile, area: str) -> str:
    if area == "headline":
        return profile.headline or "(vazio)"
    if area == "about":
        text = profile.about or "(vazio)"
        return text[:1200] + ("…" if len(text) > 1200 else "")
    if area == "experience":
        lines = []
        for exp in profile.experiences[:4]:
            lines.append(f"### {exp.title} @ {exp.company}")
            for b in exp.bullets[:MAX_BULLETS_PER_EXPERIENCE]:
                lines.append(f"- {b}")
        return "\n".join(lines) if lines else "(sem experiências)"
    if area == "skills":
        return ", ".join(profile.skills) or "(nenhuma no PDF)"
    if area == "language":
        return ", ".join(profile.languages) or "(não listado)"
    if area == "education":
        parts = [f"{e.school} — {e.degree}" for e in profile.education]
        certs = ", ".join(profile.certifications) or "nenhuma"
        return ("Formação: " + "; ".join(parts) if parts else "Sem formação") + f"\nCertificações: {certs}"
    if area == "featured":
        return ", ".join(profile.featured) or "(vazio)"
    return ""


def build_fix_prompt(finding: Finding, profile: Profile, target: Target) -> str:
    where = LINKEDIN_WHERE.get(finding.area, "LinkedIn → seção correspondente do perfil.")
    excerpt = _profile_excerpt(profile, finding.area)
    headline_hint = suggest_headline(target)

    extra_rules = ""
    if finding.area == "headline":
        extra_rules = f"""
FORMATO OBRIGATÓRIO DA HEADLINE
Posição | Áreas de trabalho mais fortes | Tecnologias (separadas com ·)
Exemplo: {HEADLINE_EXAMPLE}
Sugestão para este perfil: {headline_hint}
"""
    elif finding.area == "about":
        extra_rules = f"""
MODELO DE ABOUT (narrativa com escala, empresas, domínios, stack no final)
{ABOUT_EXAMPLE[:600]}…
"""
    elif finding.area == "experience":
        extra_rules = f"""
FORMATO DE CADA BULLET (~3 linhas, máx {MAX_BULLETS_PER_EXPERIENCE} por experiência)
{BULLET_FORMAT}
Exemplo: {BULLET_EXAMPLE}
"""
    elif finding.area == "language" and target.market == "gringa":
        extra_rules = "\nPara mercado Gringa: adicione **English** em Languages e escreva headline/about/experiências em inglês.\n"

    return f"""Você é um especialista em otimização de perfil LinkedIn para desenvolvedores.

Quero corrigir UM ponto específico do meu perfil. Me entregue o texto pronto para colar no LinkedIn.

## Onde editar no LinkedIn
{where}

## Contexto do meu objetivo
{_target_block(target)}

## Problema encontrado na auditoria
- Área: {finding.area}
- Severidade: {finding.severity}
- Diagnóstico: {finding.message}
{f"- Sugestão: {finding.suggestion}" if finding.suggestion else ""}

## Conteúdo atual (extraído do meu PDF)
{excerpt}
{extra_rules}
## Sua tarefa
1. Explique em 1 frase o que mudar e por quê (para recrutadores do cargo-alvo).
2. Entregue o texto final pronto para colar — sem inventar experiências ou métricas que não aparecem acima.
3. Se faltar dado, use [ADICIONAR MÉTRICA] ou [ADICIONAR TECH] em vez de inventar.
4. Use o idioma do mercado-alvo ({target.language or "en"}).

## Formato da resposta
**O que mudar:** (1 frase)
**Texto para colar no LinkedIn:**
(texto final)
"""


def build_ssi_fix_prompt(
    pillar: dict,
    profile: Profile,
    target: Target,
) -> str:
    tips = "\n".join(f"- {t}" for t in pillar.get("tips", [])[:5])
    return f"""Você é um coach de LinkedIn para desenvolvedores que querem mais inbound de recrutadores.

Quero melhorar meu **Social Selling Index (SSI)** em um pilar específico.

## Pilar a melhorar
- {pillar.get("label")} ({pillar.get("color_pt")})
- Score atual: {pillar.get("score")}/25 — {pillar.get("rating")}
- O que significa: {pillar.get("meaning")}

## Meu contexto
{_target_block(target)}
- Nome: {profile.name or "—"}
- Headline atual: {profile.headline or "—"}

## Ações recomendadas para este pilar
{tips}

## Sua tarefa
Crie um **plano de 7 dias** com ações concretas e executáveis para subir este pilar do SSI.
Inclua:
1. 3 ações para fazer hoje (com exemplos de buscas, posts ou mensagens)
2. Rotina semanal mínima (tempo em minutos/dia)
3. 2 templates prontos (mensagem de conexão OU comentário em post OU ideia de post técnico)
4. Como medir se está funcionando

Foque em devs buscando vagas em mercado **{target.market}**.
Não invente experiências do meu currículo.
"""


def attach_fix_prompts(findings: list[Finding], profile: Profile) -> None:
    target = profile.target
    for finding in findings:
        if finding.severity in {"critical", "warning", "info"}:
            finding.fix_prompt = build_fix_prompt(finding, profile, target)
