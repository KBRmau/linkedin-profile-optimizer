# Exemplo: Gabriel Pendiuk — perfil bem posicionado

Perfil de referência para **dev que recebe inbound de recrutadores** mesmo com SSI total moderado.

## Dados

| Campo | Valor |
|-------|-------|
| Cargo | Senior / Principal Data Engineer |
| Mercado | Global remote · inglês |
| SSI total | **54/100** (top 3% na indústria Data Infrastructure) |
| Score DevProfile | **~98/100** (posicionamento do perfil) |

## SSI — onde melhorar vs onde já está bom

| Cor | Pilar | Score | Status | Insight |
|-----|-------|-------|--------|---------|
| 🟠 Laranja | Professional brand | 17.4/25 | ok/forte | Headline + About em inglês com métricas — **perfil vende bem** |
| 🟣 Roxo | Find the right people | 10.0/25 | **fraco** | Adicionar mais recrutadores e devs da área |
| 🟢 Verde | Engage with insights | 11/25 | **fraco** | Postar e comentar mais (1 post técnico/semana mínimo) |
| 🩵 Teal | Build relationships | 15.6/25 | ok | Conversar com conexões, reativar rede |

**Lição:** SSI baixo em Roxo/Verde **não significa** perfil ruim. Gabriel recebe contatos porque **Laranja (marca)** está forte: headline clara, about com escala (petabyte, 2000 pipelines), bullets quantificados.

## O que o perfil faz certo (copie isso)

**Headline:**
```
Senior Data Engineer | Cloud Data Platforms & AI Automation | GCP · Azure · Airflow · Spark · BigQuery · Terraform
```

**About:** inglês, métricas (2,000+ pipelines, 66K events/day, 70% KTLO), stack explícita.

**Experiências:** bullets com ação + escala + ferramenta + resultado.

**Skills:** Cloud, K8s, AI — alinhadas ao cargo.

## Plano SSI para Gabriel (se quiser subir de 54 → 70+)

1. **Roxo:** buscar "Technical Recruiter Data" + conectar 15/semana
2. **Verde:** 1 post técnico/semana (Airflow, GCP, AI agents)
3. **Teal:** mensagem para ex-colegas e recrutadores que já conectaram

## Rodar auditoria

```bash
python -m linkedin_optimizer audit \
  --profile templates/profile.gabriel-pendiuk.yaml \
  --out examples/gabriel-report.md \
  --prompt examples/gabriel-prompt.md
```
