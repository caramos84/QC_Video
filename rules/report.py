"""Genera los 3 artefactos de salida documentados en el README del repo:
qc_report.json, qc_score.json, qc_summary.md."""
from __future__ import annotations

import json
from pathlib import Path

from .models import FindingStatus, QCReport

LAYER_LABELS = {
    "tecnica": "Técnica",
    "visual": "Visual",
    "sonora": "Sonora",
    "semantica": "Semántica",
}


def write_report(report: QCReport, output_dir: str | Path) -> dict[str, Path]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    paths = {
        "qc_report": output_dir / "qc_report.json",
        "qc_score": output_dir / "qc_score.json",
        "qc_summary": output_dir / "qc_summary.md",
    }

    paths["qc_report"].write_text(
        json.dumps(report.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8"
    )

    score_doc = {
        "asset_id": report.asset_id,
        "profile_id": report.profile_id,
        "brief_id": report.brief_id,
        "generated_at": report.generated_at,
        **report.score_summary.to_dict(),
    }
    paths["qc_score"].write_text(json.dumps(score_doc, indent=2, ensure_ascii=False), encoding="utf-8")

    paths["qc_summary"].write_text(render_summary_md(report), encoding="utf-8")

    return paths


def render_summary_md(report: QCReport) -> str:
    s = report.score_summary
    lines: list[str] = []

    lines.append(f"# QC Summary — {report.asset_id}")
    lines.append("")
    lines.append(f"**Perfil:** `{report.profile_id}`  ")
    if report.brief_id:
        lines.append(f"**Brief:** `{report.brief_id}`  ")
    lines.append(f"**Generado:** {report.generated_at}  ")
    lines.append(f"**Motor:** v{report.engine_version}")
    lines.append("")
    lines.append(f"## Veredicto: {s.verdict.value}")
    lines.append("")
    lines.append(f"- Score: **{s.score}/100**")
    lines.append(f"- Cobertura: **{s.coverage_pct}%** de reglas aplicables evaluadas")
    lines.append(
        f"- PASS: {s.counts['pass']} · FAIL: {s.counts['fail']} · "
        f"WARNING: {s.counts['warning']} · NOT_EVALUATED: {s.counts['not_evaluated']}"
    )
    lines.append("")

    if s.deductions:
        lines.append("## Deducciones")
        lines.append("")
        lines.append("| Regla | Severidad | Puntos |")
        lines.append("|---|---|---|")
        for d in s.deductions:
            lines.append(f"| {d['rule_id']} | {d['severity']} | {d['points']} |")
        lines.append("")

    for layer_key, layer_label in LAYER_LABELS.items():
        layer_findings = [f for f in report.findings if f.layer == layer_key]
        if not layer_findings:
            continue
        lines.append(f"## Capa {layer_label}")
        lines.append("")
        lines.append("| Regla | Estado | Severidad | Mensaje |")
        lines.append("|---|---|---|---|")
        for f in layer_findings:
            lines.append(f"| {f.rule_id} | {f.status.value} | {f.severity.value} | {f.message} |")
        lines.append("")

    not_evaluated = [f for f in report.findings if f.status == FindingStatus.NOT_EVALUATED]
    lines.append("## Cobertura y brechas conocidas")
    lines.append("")
    if not not_evaluated:
        lines.append("Todas las reglas del catálogo fueron evaluadas.")
    else:
        lines.append(
            f"{len(not_evaluated)} de {len(report.findings)} reglas del catálogo NO fueron evaluadas "
            "porque el dato de origen todavía no existe en el pipeline (sin CV, sin análisis de "
            "calidad de audio, sin capa semántica). **Esto no equivale a 'aprobado' — son brechas "
            "de cobertura, no validaciones exitosas.**"
        )
        lines.append("")
        lines.append("| Regla | Capa | Motivo |")
        lines.append("|---|---|---|")
        for f in not_evaluated:
            lines.append(f"| {f.rule_id} | {f.layer} | {f.reason or f.message} |")
    lines.append("")

    return "\n".join(lines)
