import jsonschema
import pytest

from rules.loaders import (
    get_field,
    has_field,
    load_brief,
    load_catalog,
    load_profile,
    missing_fields,
)


def test_get_field_navigates_nested_dict():
    data = {"a": {"b": {"c": 5}}}
    assert get_field(data, "a.b.c") == 5


def test_get_field_returns_none_for_missing_key():
    assert get_field({"a": {}}, "a.b.c") is None


def test_get_field_returns_none_for_null_intermediate():
    assert get_field({"a": None}, "a.b.c") is None


def test_get_field_preserves_falsy_values():
    # 0, False, [] son valores presentes reales -- no deben confundirse con "faltante".
    assert get_field({"a": {"b": 0}}, "a.b") == 0
    assert get_field({"a": {"b": False}}, "a.b") is False
    assert get_field({"a": {"b": []}}, "a.b") == []


def test_has_field_true_for_falsy_present_values():
    assert has_field({"a": {"b": 0}}, "a.b") is True
    assert has_field({"a": {"b": False}}, "a.b") is True


def test_has_field_false_for_missing():
    assert has_field({"a": {}}, "a.b") is False


def test_missing_fields_reports_only_absent_paths():
    data = {"a": {"b": 1, "c": None}}
    result = missing_fields(data, ["a.b", "a.c", "a.d"])
    assert result == ["a.c", "a.d"]


def test_load_catalog_returns_all_rules():
    rules = load_catalog()
    assert len(rules) == 26
    implementable = [r for r in rules if r.implementable]
    stubs = [r for r in rules if not r.implementable]
    assert len(implementable) == 20
    assert len(stubs) == 6


def test_load_catalog_implementable_rules_have_check_fn():
    for rule in load_catalog():
        if rule.implementable:
            assert rule.check_fn, f"{rule.rule_id} implementable pero sin check_fn"
        else:
            assert rule.not_evaluated_reason, f"{rule.rule_id} stub sin not_evaluated_reason"


def test_load_profile_valid(tmp_path):
    profile = load_profile("profiles/meta_instagram_reels.yaml")
    assert profile["profile_id"] == "meta_instagram_reels"
    assert profile["technical"]["aspect_ratios"] == ["9:16"]


def test_load_profile_rejects_invalid_document(tmp_path):
    bad = tmp_path / "bad_profile.yaml"
    bad.write_text("schema_version: 1\nprofile_id: x\n")  # faltan platform/channel/placement/technical
    with pytest.raises(jsonschema.ValidationError):
        load_profile(bad)


def test_load_brief_none_when_no_path():
    assert load_brief(None) is None


def test_load_brief_valid():
    brief = load_brief("samples/briefs/example_campaign_brief.yaml")
    assert brief["brief_id"] == "campaign_oferta_escolar_2026"
    assert brief["severity_overrides"]["VISUAL_CTA_DETECTION"] == "error_de_marca"
