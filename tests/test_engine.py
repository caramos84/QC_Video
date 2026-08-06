from pathlib import Path

from rules.engine import run_qc, run_qc_from_paths
from rules.models import FindingStatus, Severity, Verdict

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def test_run_qc_all_pass_still_review_due_to_coverage(asset_pass, test_profile, catalog, scoring_config):
    # Con solo 18/26 reglas implementables, un asset perfecto NUNCA debe salir
    # PASS todavía -- es la decisión de negocio confirmada con el usuario.
    report = run_qc(asset_pass, test_profile, brief=None, catalog=catalog, scoring_config=scoring_config)
    implementable_findings = [f for f in report.findings if f.status != FindingStatus.NOT_EVALUATED]
    assert all(f.status == FindingStatus.PASS for f in implementable_findings)
    assert report.score_summary.score == 100
    assert report.score_summary.verdict == Verdict.REVIEW


def test_run_qc_critical_aspect_ratio_mismatch_fails(asset_fail_critical, test_profile, catalog, scoring_config):
    report = run_qc(asset_fail_critical, test_profile, brief=None, catalog=catalog, scoring_config=scoring_config)
    aspect_finding = next(f for f in report.findings if f.rule_id == "TECH_ASPECT_RATIO")
    assert aspect_finding.status == FindingStatus.FAIL
    assert aspect_finding.severity == Severity.CRITICO
    assert report.score_summary.verdict == Verdict.FAIL


def test_run_qc_missing_visual_audio_sections_degrades_gracefully(
    asset_missing_data, test_profile, catalog, scoring_config
):
    # No debe lanzar excepción aunque visual/audio sean null.
    report = run_qc(asset_missing_data, test_profile, brief=None, catalog=catalog, scoring_config=scoring_config)

    by_id = {f.rule_id: f for f in report.findings}
    # Metadata técnica sí existe -> se evalúa.
    assert by_id["TECH_ASPECT_RATIO"].status == FindingStatus.PASS
    # audio_present viene de asset.metadata, no de audio.summary -> se evalúa (y falla, es False).
    assert by_id["SONORA_AUDIO_PRESENT"].status == FindingStatus.FAIL
    # Todo lo que depende de visual.summary / audio.summary -> NOT_EVALUATED, no crash.
    assert by_id["VISUAL_TEXT_PRESENCE"].status == FindingStatus.NOT_EVALUATED
    assert by_id["SONORA_SPEECH_DETECTED"].status == FindingStatus.NOT_EVALUATED


def test_brief_severity_override_applies_even_when_not_evaluated(asset_pass, test_profile, test_brief, catalog, scoring_config):
    report = run_qc(asset_pass, test_profile, brief=test_brief, catalog=catalog, scoring_config=scoring_config)
    product_finding = next(f for f in report.findings if f.rule_id == "VISUAL_PRODUCT_DETECTION")
    assert product_finding.status == FindingStatus.NOT_EVALUATED  # sin CV pipeline (queda fuera de este paso)
    assert product_finding.severity == Severity.CRITICO  # pero la severidad ya refleja el override del brief
    assert report.brief_id == "test_brief"


def test_logo_presence_and_safe_zone_evaluated_and_pass_with_brief(asset_pass, test_profile, test_brief, catalog, scoring_config):
    report = run_qc(asset_pass, test_profile, brief=test_brief, catalog=catalog, scoring_config=scoring_config)
    presence = next(f for f in report.findings if f.rule_id == "VISUAL_LOGO_PRESENCE")
    safe_zone = next(f for f in report.findings if f.rule_id == "VISUAL_LOGO_SAFE_ZONE")
    assert presence.status == FindingStatus.PASS
    assert presence.severity == Severity.CRITICO  # el override del brief sigue aplicando una vez evaluado
    assert safe_zone.status == FindingStatus.PASS


def test_cta_detection_evaluated_and_passes_with_brief(asset_pass, test_profile, test_brief, catalog, scoring_config):
    report = run_qc(asset_pass, test_profile, brief=test_brief, catalog=catalog, scoring_config=scoring_config)
    cta_finding = next(f for f in report.findings if f.rule_id == "VISUAL_CTA_DETECTION")
    assert cta_finding.status == FindingStatus.PASS
    assert cta_finding.severity == Severity.ERROR_DE_MARCA  # el override del brief sigue aplicando una vez evaluado


def test_dominant_color_evaluated_and_passes_with_brief(asset_pass, test_profile, test_brief, catalog, scoring_config):
    report = run_qc(asset_pass, test_profile, brief=test_brief, catalog=catalog, scoring_config=scoring_config)
    color_finding = next(f for f in report.findings if f.rule_id == "VISUAL_DOMINANT_COLOR")
    assert color_finding.status == FindingStatus.PASS


def test_run_qc_from_paths_matches_run_qc(asset_missing_data, test_profile):
    report_from_paths = run_qc_from_paths(
        FIXTURES_DIR / "asset_knowledge_missing_data.json",
        FIXTURES_DIR / "profile_test.yaml",
    )
    assert report_from_paths.profile_id == "test_profile"
    assert report_from_paths.asset_id == "fixture_missing_data.mp4"
    assert len(report_from_paths.findings) == 26
