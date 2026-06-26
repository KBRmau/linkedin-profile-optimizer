from __future__ import annotations

from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from ..audit.fix_prompts import build_ssi_fix_prompt
from ..audit.ssi import interpret_ssi
from ..dev_presets import DEV_ROLES
from ..models import MARKET_LABELS, SSI
from ..service import build_target, run_audit_from_pdf, save_upload

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR.parent.parent / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="DevProfile", description="LinkedIn audit for developers")
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")


def _index_context(request: Request, error: Optional[str] = None) -> dict:
    return {
        "request": request,
        "roles": DEV_ROLES,
        "ssi_url": "https://www.linkedin.com/sales/ssi",
        "error": error,
    }


def _parse_score(raw: str) -> Optional[float]:
    raw = (raw or "").strip().replace(",", ".")
    if not raw:
        return None
    try:
        score = float(raw)
    except ValueError:
        return None
    if 0 <= score <= 25:
        return score
    return None


def _build_ssi(brand: str, find_p: str, engage: str, relationships: str) -> tuple[Optional[SSI], Optional[str]]:
    values = {
        "Professional brand": _parse_score(brand),
        "Find the right people": _parse_score(find_p),
        "Engage with insights": _parse_score(engage),
        "Build relationships": _parse_score(relationships),
    }
    missing = [label for label, value in values.items() if value is None]
    if missing:
        return None, f"Preencha os 4 scores do SSI (0–25, decimais ok). Faltando: {', '.join(missing)}."

    return SSI(
        professional_brand=values["Professional brand"],
        find_people=values["Find the right people"],
        engage_insights=values["Engage with insights"],
        build_relationships=values["Build relationships"],
    ), None


@app.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "index.html", _index_context(request))


@app.post("/audit", response_class=HTMLResponse)
async def audit(
    request: Request,
    profile_pdf: UploadFile = File(..., description="LinkedIn Save to PDF"),
    role_key: str = Form("data-engineer"),
    custom_role: str = Form(""),
    market: str = Form("gringa"),
    seniority: str = Form("senior"),
    language: str = Form("en"),
    ssi_brand: str = Form(""),
    ssi_find: str = Form(""),
    ssi_engage: str = Form(""),
    ssi_relationships: str = Form(""),
) -> HTMLResponse:
    if not profile_pdf.filename or not profile_pdf.filename.lower().endswith(".pdf"):
        return templates.TemplateResponse(
            request,
            "index.html",
            _index_context(
                request,
                "Envie um arquivo PDF exportado do LinkedIn (Perfil → Salvar em PDF).",
            ),
            status_code=400,
        )

    if market not in MARKET_LABELS:
        return templates.TemplateResponse(
            request,
            "index.html",
            _index_context(request, "Selecione Brasil ou Gringa como mercado."),
            status_code=400,
        )

    ssi, ssi_error = _build_ssi(ssi_brand, ssi_find, ssi_engage, ssi_relationships)
    if ssi_error:
        return templates.TemplateResponse(
            request,
            "index.html",
            _index_context(request, ssi_error),
            status_code=400,
        )

    pdf_bytes = await profile_pdf.read()
    pdf_path = save_upload(pdf_bytes, ".pdf", UPLOAD_DIR)
    target = build_target(role_key, market, seniority, language, custom_role)

    try:
        result = run_audit_from_pdf(pdf_path, target, ssi)
    except Exception as exc:
        return templates.TemplateResponse(
            request,
            "index.html",
            _index_context(request, f"Não foi possível ler o PDF: {exc}"),
            status_code=400,
        )
    finally:
        pdf_path.unlink(missing_ok=True)

    ssi_interp = interpret_ssi(ssi)
    for pillar in ssi_interp.get("pillars", []):
        if pillar.get("rating") != "forte":
            pillar["fix_prompt"] = build_ssi_fix_prompt(pillar, result.profile, target)

    critical = [f for f in result.findings if f.severity == "critical"]
    warnings = [f for f in result.findings if f.severity == "warning"]
    infos = [f for f in result.findings if f.severity == "info"]

    return templates.TemplateResponse(
        request,
        "result.html",
        {
            "request": request,
            "result": result,
            "ssi_interp": ssi_interp,
            "critical": critical,
            "warnings": warnings,
            "infos": infos,
            "target": target,
            "market_label": MARKET_LABELS.get(target.market, target.market),
        },
    )
