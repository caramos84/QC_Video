"""Aplica rules/scoring_config.yaml a una lista de Findings: calcula score,
cobertura y veredicto final (PASS/REVIEW/FAIL)."""
from __future__ import annotations

from .models import Finding, FindingStatus, ScoreSummary, Severity, Verdict


def score_findings(findings: list[Finding], scoring_config: dict) -> ScoreSummary:
    score = scoring_config["score_start"]
    floor = scoring_config["score_floor"]
    severities_cfg = scoring_config["severities"]
    thresholds = scoring_config["thresholds"]
    coverage_cfg = scoring_config["coverage"]

    counts = {"pass": 0, "fail": 0, "warning": 0, "not_evaluated": 0}
    deductions: list[dict] = []
    has_critico_fail = False
    has_error_de_marca_fail = False

    for f in findings:
        if f.status == FindingStatus.NOT_EVALUATED:
            counts["not_evaluated"] += 1
            continue

        if f.status == FindingStatus.PASS:
            counts["pass"] += 1
            continue

        # f.status == FAIL
        sev_cfg = severities_cfg[f.severity.value]
        if f.severity == Severity.CRITICO:
            has_critico_fail = True
            counts["fail"] += 1
        elif f.severity == Severity.ERROR_DE_MARCA:
            has_error_de_marca_fail = True
            counts["fail"] += 1
        elif f.severity == Severity.ERROR_TECNICO:
            counts["fail"] += 1
        else:  # warning
            counts["warning"] += 1

        points = -sev_cfg["deduction"]
        if points != 0:
            score += points
            deductions.append({"rule_id": f.rule_id, "severity": f.severity.value, "points": points})

    score = max(floor, min(scoring_config["score_start"], score))

    evaluated = counts["pass"] + counts["fail"] + counts["warning"]
    applicable = evaluated + counts["not_evaluated"]
    coverage_pct = round(100.0 * evaluated / applicable, 1) if applicable else 0.0

    verdict = _determine_verdict(
        score=score,
        has_critico_fail=has_critico_fail,
        has_error_de_marca_fail=has_error_de_marca_fail,
        coverage_pct=coverage_pct,
        thresholds=thresholds,
        coverage_cfg=coverage_cfg,
    )

    return ScoreSummary(
        score=score,
        verdict=verdict,
        coverage_pct=coverage_pct,
        counts=counts,
        deductions=deductions,
    )


def _determine_verdict(
    *,
    score: int,
    has_critico_fail: bool,
    has_error_de_marca_fail: bool,
    coverage_pct: float,
    thresholds: dict,
    coverage_cfg: dict,
) -> Verdict:
    if has_critico_fail:
        return Verdict.FAIL
    if score < thresholds["review_min_score"]:
        return Verdict.FAIL
    if (
        score >= thresholds["pass_min_score"]
        and not has_error_de_marca_fail
        and coverage_pct >= coverage_cfg["pass_min_coverage_pct"]
    ):
        return Verdict.PASS
    # score >= review_min_score pero no cumple los 3 requisitos de PASS
    # (incluye el caso confirmado con el usuario: score alto + cobertura baja).
    return Verdict.REVIEW
