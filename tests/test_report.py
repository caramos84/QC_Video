import json

from rules.engine import run_qc
from rules.report import write_report


def test_write_report_creates_three_artifacts(tmp_path, asset_pass, test_profile, catalog, scoring_config):
    report = run_qc(asset_pass, test_profile, brief=None, catalog=catalog, scoring_config=scoring_config)
    paths = write_report(report, tmp_path / "outputs")

    assert paths["qc_report"].exists()
    assert paths["qc_score"].exists()
    assert paths["qc_summary"].exists()


def test_qc_report_json_matches_report_dict(tmp_path, asset_pass, test_profile, catalog, scoring_config):
    report = run_qc(asset_pass, test_profile, brief=None, catalog=catalog, scoring_config=scoring_config)
    paths = write_report(report, tmp_path / "outputs")

    doc = json.loads(paths["qc_report"].read_text(encoding="utf-8"))
    assert doc["asset_id"] == report.asset_id
    assert len(doc["findings"]) == 26


def test_qc_score_json_has_expected_shape(tmp_path, asset_pass, test_profile, catalog, scoring_config):
    report = run_qc(asset_pass, test_profile, brief=None, catalog=catalog, scoring_config=scoring_config)
    paths = write_report(report, tmp_path / "outputs")

    doc = json.loads(paths["qc_score"].read_text(encoding="utf-8"))
    assert doc["score"] == 100
    assert doc["verdict"] == "REVIEW"
    assert "coverage_pct" in doc
    assert "counts" in doc


def test_qc_summary_md_flags_not_evaluated_rules_explicitly(
    tmp_path, asset_missing_data, test_profile, catalog, scoring_config
):
    report = run_qc(asset_missing_data, test_profile, brief=None, catalog=catalog, scoring_config=scoring_config)
    paths = write_report(report, tmp_path / "outputs")

    text = paths["qc_summary"].read_text(encoding="utf-8")
    assert "Cobertura y brechas conocidas" in text
    assert "no equivale a 'aprobado'" in text
    assert "VISUAL_TEXT_PRESENCE" in text
