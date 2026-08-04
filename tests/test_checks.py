from rules import checks
from rules.models import FindingStatus


def _ak(**overrides):
    """Construye un asset_knowledge mínimo, sobreescribible por test."""
    base = {
        "asset": {"metadata": {
            "width": 1080, "height": 1920, "duration": 15.0,
            "orientation": "vertical", "audio_present": True,
        }},
        "visual": {"summary": {"frames_with_text": 2, "frames_processed": 3, "max_words_in_frame": 10}},
        "audio": {"summary": {"speech_detected": True, "language": "es", "word_count": 20}},
    }
    for path, value in overrides.items():
        node = base
        parts = path.split(".")
        for p in parts[:-1]:
            node = node[p]
        node[parts[-1]] = value
    return base


PROFILE = {
    "technical": {
        "aspect_ratios": ["9:16"],
        "resolution_min": [500, 500],
        "duration_min_s": 3,
        "duration_max_s": 60,
    }
}


def test_check_aspect_ratio_pass():
    status, _, _ = checks.check_aspect_ratio(_ak(), PROFILE, None)
    assert status == FindingStatus.PASS


def test_check_aspect_ratio_fail():
    ak = _ak(**{"asset.metadata.width": 1920, "asset.metadata.height": 1080})
    status, _, _ = checks.check_aspect_ratio(ak, PROFILE, None)
    assert status == FindingStatus.FAIL


def test_check_resolution_min_pass():
    status, _, _ = checks.check_resolution_min(_ak(), PROFILE, None)
    assert status == FindingStatus.PASS


def test_check_resolution_min_fail_partial_dimension():
    ak = _ak(**{"asset.metadata.width": 100})
    status, _, evidence = checks.check_resolution_min(ak, PROFILE, None)
    assert status == FindingStatus.FAIL
    assert "min_w" in evidence


def test_check_duration_min_and_max():
    assert checks.check_duration_min(_ak(), PROFILE, None)[0] == FindingStatus.PASS
    assert checks.check_duration_max(_ak(), PROFILE, None)[0] == FindingStatus.PASS

    too_short = _ak(**{"asset.metadata.duration": 1.0})
    assert checks.check_duration_min(too_short, PROFILE, None)[0] == FindingStatus.FAIL

    too_long = _ak(**{"asset.metadata.duration": 999.0})
    assert checks.check_duration_max(too_long, PROFILE, None)[0] == FindingStatus.FAIL


def test_check_orientation_consistent_and_inconsistent():
    assert checks.check_orientation(_ak(), PROFILE, None)[0] == FindingStatus.PASS
    bad = _ak(**{"asset.metadata.orientation": "horizontal"})
    assert checks.check_orientation(bad, PROFILE, None)[0] == FindingStatus.FAIL


def test_check_text_presence():
    assert checks.check_text_presence(_ak(), PROFILE, None)[0] == FindingStatus.PASS
    no_text = _ak(**{"visual.summary.frames_with_text": 0})
    assert checks.check_text_presence(no_text, PROFILE, None)[0] == FindingStatus.FAIL


def test_check_text_density_threshold():
    assert checks.check_text_density(_ak(), PROFILE, None)[0] == FindingStatus.PASS
    dense = _ak(**{"visual.summary.max_words_in_frame": checks.TEXT_DENSITY_WARN_THRESHOLD + 1})
    assert checks.check_text_density(dense, PROFILE, None)[0] == FindingStatus.FAIL


def test_check_audio_present():
    assert checks.check_audio_present(_ak(), PROFILE, None)[0] == FindingStatus.PASS
    no_audio = _ak(**{"asset.metadata.audio_present": False})
    assert checks.check_audio_present(no_audio, PROFILE, None)[0] == FindingStatus.FAIL


def test_check_speech_detected():
    assert checks.check_speech_detected(_ak(), PROFILE, None)[0] == FindingStatus.PASS
    no_speech = _ak(**{"audio.summary.speech_detected": False})
    assert checks.check_speech_detected(no_speech, PROFILE, None)[0] == FindingStatus.FAIL


def test_check_language_without_brief_expectation_passes():
    status, msg, _ = checks.check_language(_ak(), PROFILE, None)
    assert status == FindingStatus.PASS
    assert "no especifica" in msg


def test_check_language_matches_brief_expectation():
    brief = {"expected_language": "es"}
    status, _, _ = checks.check_language(_ak(), PROFILE, brief)
    assert status == FindingStatus.PASS


def test_check_language_mismatches_brief_expectation():
    brief = {"expected_language": "en"}
    status, _, _ = checks.check_language(_ak(), PROFILE, brief)
    assert status == FindingStatus.FAIL


def test_check_narration_present():
    assert checks.check_narration_present(_ak(), PROFILE, None)[0] == FindingStatus.PASS
    silent = _ak(**{"audio.summary.word_count": 0})
    assert checks.check_narration_present(silent, PROFILE, None)[0] == FindingStatus.FAIL


def test_not_evaluated_factory():
    status, message, evidence = checks.not_evaluated("motivo de prueba")
    assert status == FindingStatus.NOT_EVALUATED
    assert "motivo de prueba" in message
    assert evidence is None


def test_check_registry_covers_all_implementable_rule_check_fns(catalog):
    for rule in catalog:
        if rule.implementable:
            assert rule.check_fn in checks.CHECK_REGISTRY, f"{rule.check_fn} no registrado"
