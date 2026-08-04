"""Tipos de datos del Motor de QC: reglas, findings, score y reporte."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class Severity(str, Enum):
    CRITICO = "critico"
    ERROR_DE_MARCA = "error_de_marca"
    ERROR_TECNICO = "error_tecnico"
    WARNING = "warning"


class FindingStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    NOT_EVALUATED = "NOT_EVALUATED"


class Verdict(str, Enum):
    PASS = "PASS"
    REVIEW = "REVIEW"
    FAIL = "FAIL"


@dataclass(frozen=True)
class Rule:
    """Una entrada de rules/catalog.yaml."""

    rule_id: str
    layer: str
    default_severity: Severity
    implementable: bool
    description: str
    requires_fields: list[str] = field(default_factory=list)
    requires_profile_fields: list[str] = field(default_factory=list)
    check_fn: str | None = None
    not_evaluated_reason: str | None = None


@dataclass
class Finding:
    """Resultado de evaluar una regla contra un asset."""

    rule_id: str
    layer: str
    status: FindingStatus
    severity: Severity
    message: str
    evidence: dict[str, Any] | None = None
    reason: str | None = None  # solo cuando status == NOT_EVALUATED

    def to_dict(self) -> dict:
        d = {
            "rule_id": self.rule_id,
            "layer": self.layer,
            "status": self.status.value,
            "severity": self.severity.value,
            "message": self.message,
            "evidence": self.evidence,
        }
        if self.reason is not None:
            d["reason"] = self.reason
        return d


@dataclass
class ScoreSummary:
    score: int
    verdict: Verdict
    coverage_pct: float
    counts: dict[str, int]
    deductions: list[dict[str, Any]]

    def to_dict(self) -> dict:
        return {
            "score": self.score,
            "verdict": self.verdict.value,
            "coverage_pct": self.coverage_pct,
            "counts": self.counts,
            "deductions": self.deductions,
        }


@dataclass
class QCReport:
    asset_id: str
    profile_id: str
    brief_id: str | None
    engine_version: str
    generated_at: str
    findings: list[Finding]
    score_summary: ScoreSummary

    def to_dict(self) -> dict:
        return {
            "asset_id": self.asset_id,
            "profile_id": self.profile_id,
            "brief_id": self.brief_id,
            "engine_version": self.engine_version,
            "generated_at": self.generated_at,
            "findings": [f.to_dict() for f in self.findings],
            "score_summary": self.score_summary.to_dict(),
        }
