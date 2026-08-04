from rules.models import Finding, FindingStatus, Severity, Verdict
from rules.scoring import score_findings


def _finding(rule_id, status, severity, layer="tecnica"):
    return Finding(rule_id=rule_id, layer=layer, status=status, severity=severity, message="x")


def test_all_pass_high_coverage_yields_pass(scoring_config):
    # 10 reglas evaluadas, todas PASS, 0 NOT_EVALUATED -> cobertura 100%.
    findings = [_finding(f"R{i}", FindingStatus.PASS, Severity.WARNING) for i in range(10)]
    summary = score_findings(findings, scoring_config)
    assert summary.score == 100
    assert summary.coverage_pct == 100.0
    assert summary.verdict == Verdict.PASS


def test_critico_fail_forces_fail_regardless_of_score(scoring_config):
    findings = [_finding("CRIT", FindingStatus.FAIL, Severity.CRITICO)]
    findings += [_finding(f"OK{i}", FindingStatus.PASS, Severity.WARNING) for i in range(20)]
    summary = score_findings(findings, scoring_config)
    assert summary.verdict == Verdict.FAIL


def test_low_coverage_caps_verdict_at_review_even_with_perfect_score(scoring_config):
    # Decisión confirmada con el usuario: score alto + cobertura baja -> REVIEW, nunca PASS.
    findings = [_finding("R1", FindingStatus.PASS, Severity.WARNING)]
    findings += [_finding(f"NE{i}", FindingStatus.NOT_EVALUATED, Severity.WARNING) for i in range(9)]
    summary = score_findings(findings, scoring_config)
    assert summary.score == 100
    assert summary.coverage_pct == 10.0
    assert summary.verdict == Verdict.REVIEW


def test_error_de_marca_without_critico_yields_review_not_pass(scoring_config):
    findings = [_finding("MARCA", FindingStatus.FAIL, Severity.ERROR_DE_MARCA)]
    findings += [_finding(f"OK{i}", FindingStatus.PASS, Severity.WARNING) for i in range(20)]
    summary = score_findings(findings, scoring_config)
    assert summary.verdict != Verdict.PASS
    assert summary.verdict != Verdict.FAIL  # score sigue alto (80), no cae a FAIL


def test_score_never_goes_below_floor(scoring_config):
    findings = [_finding(f"MARCA{i}", FindingStatus.FAIL, Severity.ERROR_DE_MARCA) for i in range(10)]
    summary = score_findings(findings, scoring_config)
    assert summary.score == scoring_config["score_floor"]
    assert summary.verdict == Verdict.FAIL


def test_deductions_recorded_per_fail_finding(scoring_config):
    findings = [
        _finding("A", FindingStatus.FAIL, Severity.WARNING),
        _finding("B", FindingStatus.FAIL, Severity.ERROR_TECNICO),
        _finding("C", FindingStatus.PASS, Severity.WARNING),
    ]
    summary = score_findings(findings, scoring_config)
    assert {d["rule_id"] for d in summary.deductions} == {"A", "B"}
    assert summary.score == 100 - 5 - 15


def test_not_evaluated_excluded_from_deductions(scoring_config):
    findings = [_finding("NE", FindingStatus.NOT_EVALUATED, Severity.CRITICO)]
    summary = score_findings(findings, scoring_config)
    assert summary.score == 100
    assert summary.deductions == []
    assert summary.verdict != Verdict.FAIL  # critico NOT_EVALUATED no fuerza FAIL, solo un critico FAIL lo hace
