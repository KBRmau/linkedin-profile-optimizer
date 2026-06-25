from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .audit.rules import audit_profile
from .ingest.manual import load_profile_yaml, save_profile_yaml
from .ingest.pdf_parser import parse_pdf
from .report.render import render_llm_prompt, render_report


def _cmd_ingest(args: argparse.Namespace) -> int:
    profile = parse_pdf(args.pdf)
    out = Path(args.out)
    save_profile_yaml(profile, out)
    print(f"Draft escrito em {out}")
    print("Revise e complete: headline, about, bullets, skills, ssi e target antes do audit.")
    return 0


def _cmd_audit(args: argparse.Namespace) -> int:
    profile = load_profile_yaml(args.profile)
    findings = audit_profile(profile)

    report = render_report(profile, findings)
    report_path = Path(args.out)
    report_path.write_text(report, encoding="utf-8")
    print(f"Relatório escrito em {report_path}")

    if args.prompt:
        prompt = render_llm_prompt(profile, findings)
        prompt_path = Path(args.prompt)
        prompt_path.write_text(prompt, encoding="utf-8")
        print(f"Prompt LLM escrito em {prompt_path}")

    crit = sum(1 for f in findings if f.severity == "critical")
    warn = sum(1 for f in findings if f.severity == "warning")
    print(f"Findings: {crit} críticos, {warn} alertas.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="linkedin-optimizer",
        description="Audita e otimiza um perfil do LinkedIn (manual + semi-auto, sem scraping).",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_ingest = sub.add_parser("ingest", help="Parse de PDF 'Save to PDF' do LinkedIn para YAML draft.")
    p_ingest.add_argument("--pdf", required=True, help="Caminho do PDF exportado do LinkedIn.")
    p_ingest.add_argument("--out", default="profile.yaml", help="YAML de saída (default: profile.yaml).")
    p_ingest.set_defaults(func=_cmd_ingest)

    p_audit = sub.add_parser("audit", help="Audita o perfil a partir do YAML e gera relatório.")
    p_audit.add_argument("--profile", required=True, help="YAML do perfil.")
    p_audit.add_argument("--out", default="report.md", help="Relatório markdown (default: report.md).")
    p_audit.add_argument("--prompt", default="llm_prompt.md",
                         help="Arquivo de prompt LLM (default: llm_prompt.md). Use '' para pular.")
    p_audit.set_defaults(func=_cmd_audit)

    p_serve = sub.add_parser("serve", help="Sobe a interface web DevProfile (upload PDF + SSI).")
    p_serve.add_argument("--host", default="127.0.0.1")
    p_serve.add_argument("--port", type=int, default=8000)
    p_serve.set_defaults(func=_cmd_serve)

    return parser


def _cmd_serve(args: argparse.Namespace) -> int:
    import uvicorn

    print(f"DevProfile: http://{args.host}:{args.port}")
    uvicorn.run(
        "linkedin_optimizer.web.app:app",
        host=args.host,
        port=args.port,
        reload=False,
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if getattr(args, "prompt", None) == "":
        args.prompt = None
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
