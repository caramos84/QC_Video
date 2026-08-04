"""Orquestador del Motor de QC: loaders -> checks -> scoring -> report."""
from __future__ import annotations

import datetime
from pathlib import Path

from .checks import CHECK_REGISTRY, not_evaluated
from .loaders import (
    get_field,
    load_asset_knowledge,
    load_brief,
    load_catalog,
    load_profile,
    load_scoring_config,
    missing_fields,
)
from .models import Finding, QCReport, Rule, Severity
from .scoring import score_findings

ENGINE_VERSION = "0.1.0"

PathLike = str | Path


def _severity_for(rule: Rule, brief: dict | None) -> Severity:
    """La severidad de una regla puede ser escalada/degradada por el brief
    de campaña (samples/briefs/*.yaml -> severity_overrides), per el ejemplo
    del board de Miro: 'CTA no aparece -> warning/error según brief'."""
    if brief:
        override = brief.get("severity_overrides", {}).get(rule.rule_id)
        if override:
            return Severity(override)
    return rule.default_severity


def evaluate_rule(rule: Rule, asset_knowledge: dict, profile: dict, brief: dict | None) -> Finding:
    severity = _severity_for(rule, brief)

    if not rule.implementable:
        status, message, evidence = not_evaluated(rule.not_evaluated_reason or "sin implementar todavía")
        return Finding(
            rule_id=rule.rule_id, layer=rule.layer, status=status, severity=severity,
            message=message, evidence=evidence, reason=rule.not_evaluated_reason,
        )

    missing_asset = missing_fields(asset_knowledge, rule.requires_fields)
    missing_profile = missing_fields(profile, rule.requires_profile_fields)
    if missing_asset or missing_profile:
        reason_parts = []
        if missing_asset:
            reason_parts.append("faltan en asset_knowledge: " + ", ".join(missing_asset))
        if missing_profile:
            reason_parts.append("faltan en profile: " + ", ".join(missing_profile))
        reason = "; ".join(reason_parts)
        status, message, evidence = not_evaluated(reason)
        return Finding(
            rule_id=rule.rule_id, layer=rule.layer, status=status, severity=severity,
            message=message, evidence=evidence, reason=reason,
        )

    check_fn = CHECK_REGISTRY[rule.check_fn]
    status, message, evidence = check_fn(asset_knowledge, profile, brief)
    return Finding(rule_id=rule.rule_id, layer=rule.layer, status=status, severity=severity,
                   message=message, evidence=evidence)


def run_qc(
    asset_knowledge: dict,
    profile: dict,
    brief: dict | None = None,
    catalog: list[Rule] | None = None,
    scoring_config: dict | None = None,
    asset_id: str | None = None,
) -> QCReport:
    """Función principal, pura (sin I/O) para facilitar tests unitarios."""
    catalog = catalog if catalog is not None else load_catalog()
    scoring_config = scoring_config if scoring_config is not None else load_scoring_config()
    asset_id = asset_id or get_field(asset_knowledge, "asset.metadata.filename") or "unknown_asset"

    findings = [evaluate_rule(rule, asset_knowledge, profile, brief) for rule in catalog]
    score_summary = score_findings(findings, scoring_config)

    return QCReport(
        asset_id=asset_id,
        profile_id=profile["profile_id"],
        brief_id=(brief or {}).get("brief_id"),
        engine_version=ENGINE_VERSION,
        generated_at=datetime.datetime.now(datetime.UTC).isoformat(),
        findings=findings,
        score_summary=score_summary,
    )


def run_qc_from_paths(
    asset_knowledge_path: PathLike,
    profile_path: PathLike,
    brief_path: PathLike | None = None,
    asset_id: str | None = None,
) -> QCReport:
    """Wrapper de conveniencia con I/O — usado por Notebook 04 y por CLIs."""
    return run_qc(
        asset_knowledge=load_asset_knowledge(asset_knowledge_path),
        profile=load_profile(profile_path),
        brief=load_brief(brief_path),
        asset_id=asset_id,
    )
