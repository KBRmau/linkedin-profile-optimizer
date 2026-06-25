# DevProfile

**LinkedIn audit para desenvolvedores** — receba mais contatos de recrutadores.

Envie o PDF do seu perfil + scores do [SSI](https://www.linkedin.com/sales/ssi) e receba um diagnóstico de posicionamento com plano de ação e prompt pronto para reescrever headline, About e experiências.

Sem scraping. Sem risco de ban. Seus dados não ficam salvos permanentemente.

## Instalação

```bash
pip install -r requirements.txt
```

## Interface web (recomendado)

```bash
python -m linkedin_optimizer serve
```

Abra **http://127.0.0.1:8000**

### Fluxo na página

1. **Escolha o cargo-alvo** — Backend, Data Engineer, DevOps, etc.
2. **Mercado** — Brasil ou Gringa
3. **Upload do PDF** — LinkedIn → Perfil → Mais → *Salvar em PDF*
4. **SSI** — abra [linkedin.com/sales/ssi](https://www.linkedin.com/sales/ssi) e digite os 4 scores com decimais (ex: 17.42, 10.01, 11, 15.6)
5. **Analisar** → score, pilares fracos, correções críticas, **prompt por erro** + relatório + prompt LLM completo

## CLI (alternativa)

```bash
# PDF → YAML draft
python -m linkedin_optimizer ingest --pdf perfil.pdf --out profile.yaml

# Auditar YAML
python -m linkedin_optimizer audit --profile profile.yaml --out report.md --prompt llm_prompt.md
```

## O que é analisado (foco dev)

| Área | Para devs |
|------|-----------|
| Headline | `Posição \| Áreas fortes \| Tecnologias` — ex: `Senior Data Engineer \| Data Platform, CDP & Reliability \| GCP · Airflow · BigQuery · Spark` |
| Idioma | Gringa → exige perfil em inglês |
| About | provas técnicas, métricas, CTA para recrutadores |
| Experiências | bullets quantificados, verbos de ação, alinhamento com cargo |
| Skills | PDF exporta só top 3 — não auditar quantidade; fixe as mais relevantes no LinkedIn |
| Experiências | máx 5 bullets · ~3 linhas · ação + métrica + tech + impacto |
| About | narrativa com escala, empresas, domínios e stack no final |
| Idioma | Gringa → English em Languages + perfil em inglês |
| SSI | qual pilar está travando inbound (brand, network, engage, relationships) |

## Escala SSI (total 0–100)

| Faixa | Classificação |
|-------|---------------|
| &lt; 30 | Fraco |
| 30–49 | Mediano |
| 50+ | Bom |

## Estrutura

```
linkedin-profile-optimizer/
├── linkedin_optimizer/
│   ├── web/           # interface DevProfile
│   │   ├── app.py
│   │   ├── templates/
│   │   └── static/
│   ├── dev_presets.py # cargos de dev + keywords
│   ├── service.py
│   ├── ingest/
│   ├── audit/
│   └── report/
└── templates/profile.example.yaml
```

## Privacidade

PDFs são processados e apagados após o parse.

## Limitações

- Parse de PDF é best-effort — layouts do LinkedIn variam.
- Scores do SSI são digitados manualmente (copie do LinkedIn).
- Reescrita criativa (headlines, About) via prompt LLM, não por regras.
