from rules import checks
from rules.models import FindingStatus


def _ak(**overrides):
    """Construye un asset_knowledge mínimo, sobreescribible por test."""
    base = {
        "asset": {"metadata": {
            "width": 1080, "height": 1920, "duration": 15.0,
            "orientation": "vertical", "audio_present": True,
            "fps": 24, "file_size_bytes": 10_000_000, "codec": "h264",
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
        "frame_rate": [24, 25, 30],
        "max_file_size_mb": 50,
        "codecs": ["H.264"],
        "codecs_optional": ["H.265"],
    }
}

PROFILE_FRAME_RATE_MIN = {
    "technical": {
        "frame_rate": 14,  # número único == mínimo, ej. GDN in-banner
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


def test_check_frame_rate_list_pass_and_fail():
    # PROFILE.frame_rate = [24, 25, 30]; fixture base fps=24 -> match exacto.
    assert checks.check_frame_rate(_ak(), PROFILE, None)[0] == FindingStatus.PASS

    within_tolerance = _ak(**{"asset.metadata.fps": 29.97})
    assert checks.check_frame_rate(within_tolerance, PROFILE, None)[0] == FindingStatus.PASS

    off_list = _ak(**{"asset.metadata.fps": 50})
    assert checks.check_frame_rate(off_list, PROFILE, None)[0] == FindingStatus.FAIL


def test_check_frame_rate_single_number_is_treated_as_minimum():
    # PROFILE_FRAME_RATE_MIN.frame_rate = 14 (num. único == mínimo, no valor exacto).
    above_min = _ak(**{"asset.metadata.fps": 30})
    assert checks.check_frame_rate(above_min, PROFILE_FRAME_RATE_MIN, None)[0] == FindingStatus.PASS

    below_min = _ak(**{"asset.metadata.fps": 10})
    assert checks.check_frame_rate(below_min, PROFILE_FRAME_RATE_MIN, None)[0] == FindingStatus.FAIL


def test_check_file_size_pass_and_fail():
    # PROFILE.max_file_size_mb = 50; fixture base file_size_bytes=10MB.
    assert checks.check_file_size(_ak(), PROFILE, None)[0] == FindingStatus.PASS

    too_big = _ak(**{"asset.metadata.file_size_bytes": 100 * 1024 * 1024})
    assert checks.check_file_size(too_big, PROFILE, None)[0] == FindingStatus.FAIL


def test_check_codec_pass_primary_and_optional_and_fail():
    # PROFILE.codecs = ["H.264"], codecs_optional = ["H.265"]; fixture base codec="h264".
    assert checks.check_codec(_ak(), PROFILE, None)[0] == FindingStatus.PASS

    optional_codec = _ak(**{"asset.metadata.codec": "hevc"})
    assert checks.check_codec(optional_codec, PROFILE, None)[0] == FindingStatus.PASS

    unsupported = _ak(**{"asset.metadata.codec": "vp9"})
    assert checks.check_codec(unsupported, PROFILE, None)[0] == FindingStatus.FAIL


def test_normalize_codec_known_and_unknown():
    assert checks.normalize_codec("h264") == "H.264"
    assert checks.normalize_codec("HEVC") == "H.265"
    assert checks.normalize_codec("some_weird_codec") == "some_weird_codec"


def test_check_text_presence():
    assert checks.check_text_presence(_ak(), PROFILE, None)[0] == FindingStatus.PASS
    no_text = _ak(**{"visual.summary.frames_with_text": 0})
    assert checks.check_text_presence(no_text, PROFILE, None)[0] == FindingStatus.FAIL


def test_check_text_density_threshold():
    assert checks.check_text_density(_ak(), PROFILE, None)[0] == FindingStatus.PASS
    dense = _ak(**{"visual.summary.max_words_in_frame": checks.TEXT_DENSITY_WARN_THRESHOLD + 1})
    assert checks.check_text_density(dense, PROFILE, None)[0] == FindingStatus.FAIL


def _ak_with_frames(frames):
    return {"visual": {"frames": frames}}


def test_check_cta_detection_no_brief_is_informational_pass():
    status, message, _ = checks.check_cta_detection(_ak_with_frames([]), {}, None)
    assert status == FindingStatus.PASS
    assert "no especifica" in message


def test_check_cta_detection_brief_without_accepted_texts_is_informational_pass():
    ak = _ak_with_frames([{"frame": "f0", "time": 0, "text": ["algo"]}])
    brief = {"cta": {"required": True, "accepted_texts": []}}
    status, _, _ = checks.check_cta_detection(ak, {}, brief)
    assert status == FindingStatus.PASS


def test_check_cta_detection_exact_match():
    ak = _ak_with_frames([{"frame": "f0", "time": 0, "text": ["Compra ahora"]}])
    brief = {"cta": {"accepted_texts": ["Compra ahora"]}}
    status, _, evidence = checks.check_cta_detection(ak, {}, brief)
    assert status == FindingStatus.PASS
    assert evidence["matches"]


def test_check_cta_detection_case_insensitive_substring_match():
    ak = _ak_with_frames([{"frame": "f0", "time": 0, "text": ["COMPRA AHORA YA MISMO"]}])
    brief = {"cta": {"accepted_texts": ["compra ahora"]}}
    status, _, _ = checks.check_cta_detection(ak, {}, brief)
    assert status == FindingStatus.PASS


def test_check_cta_detection_match_in_later_frame():
    ak = _ak_with_frames(
        [
            {"frame": "f0", "time": 0, "text": ["nada relevante"]},
            {"frame": "f1", "time": 1, "text": ["Compra ahora"]},
        ]
    )
    brief = {"cta": {"accepted_texts": ["Compra ahora"]}}
    status, _, evidence = checks.check_cta_detection(ak, {}, brief)
    assert status == FindingStatus.PASS
    assert evidence["matches"][0]["frame"] == "f1"


def test_check_cta_detection_no_match_fails():
    ak = _ak_with_frames([{"frame": "f0", "time": 0, "text": ["otra cosa"]}])
    brief = {"cta": {"accepted_texts": ["Compra ahora"]}}
    status, _, _ = checks.check_cta_detection(ak, {}, brief)
    assert status == FindingStatus.FAIL


def test_check_cta_detection_empty_frames_with_requirement_fails():
    brief = {"cta": {"accepted_texts": ["Compra ahora"]}}
    status, _, _ = checks.check_cta_detection(_ak_with_frames([]), {}, brief)
    assert status == FindingStatus.FAIL


def _ak_with_colors(colors):
    return {"visual": {"summary": {"dominant_colors": colors}}}


def test_check_dominant_color_no_brief_is_informational_pass():
    status, message, _ = checks.check_dominant_color(_ak_with_colors(["#000000"]), {}, None)
    assert status == FindingStatus.PASS
    assert "no especifica" in message


def test_check_dominant_color_brief_without_brand_colors_is_informational_pass():
    brief = {"brand": {"brand_colors_hex": []}}
    status, _, _ = checks.check_dominant_color(_ak_with_colors(["#000000"]), {}, brief)
    assert status == FindingStatus.PASS


def test_check_dominant_color_exact_match():
    brief = {"brand": {"brand_colors_hex": ["#E2001A"]}}
    status, _, evidence = checks.check_dominant_color(_ak_with_colors(["#E2001A"]), {}, brief)
    assert status == FindingStatus.PASS
    assert evidence["closest_match"]["distance"] == 0.0


def test_check_dominant_color_within_threshold_passes():
    # #E2001A=(226,0,26) vs #C81428=(200,20,40) -> distancia ~35.7 (< 60)
    brief = {"brand": {"brand_colors_hex": ["#E2001A"]}}
    status, _, _ = checks.check_dominant_color(_ak_with_colors(["#C81428"]), {}, brief)
    assert status == FindingStatus.PASS


def test_check_dominant_color_at_exact_threshold_boundary_passes():
    # #3C0000=(60,0,0) vs #000000=(0,0,0) -> distancia EXACTA 60 (<=, no <)
    brief = {"brand": {"brand_colors_hex": ["#3C0000"]}}
    status, _, evidence = checks.check_dominant_color(_ak_with_colors(["#000000"]), {}, brief)
    assert evidence["closest_match"]["distance"] == checks.DOMINANT_COLOR_DISTANCE_THRESHOLD
    assert status == FindingStatus.PASS


def test_check_dominant_color_beyond_threshold_fails():
    brief = {"brand": {"brand_colors_hex": ["#E2001A"]}}
    status, _, _ = checks.check_dominant_color(_ak_with_colors(["#FFFFFF"]), {}, brief)
    assert status == FindingStatus.FAIL


def test_check_dominant_color_matches_non_first_dominant_color():
    brief = {"brand": {"brand_colors_hex": ["#E2001A"]}}
    ak = _ak_with_colors(["#FFFFFF", "#000000", "#E2001A"])
    status, _, _ = checks.check_dominant_color(ak, {}, brief)
    assert status == FindingStatus.PASS


def test_check_dominant_color_matches_non_first_brand_color():
    brief = {"brand": {"brand_colors_hex": ["#000000", "#E2001A"]}}
    status, _, _ = checks.check_dominant_color(_ak_with_colors(["#E2001A"]), {}, brief)
    assert status == FindingStatus.PASS


def test_check_dominant_color_order_independence():
    brief = {"brand": {"brand_colors_hex": ["#E2001A"]}}
    status_a, _, _ = checks.check_dominant_color(_ak_with_colors(["#FFFFFF", "#E2001A"]), {}, brief)
    status_b, _, _ = checks.check_dominant_color(_ak_with_colors(["#E2001A", "#FFFFFF"]), {}, brief)
    assert status_a == status_b == FindingStatus.PASS


def _ak_with_logo(frames_analyzed, frames_with_logo, detections):
    return {
        "visual": {
            "summary": {
                "logo_detection": {
                    "reference_image": "logo.png",
                    "frames_analyzed": frames_analyzed,
                    "frames_with_logo": frames_with_logo,
                    "detections": detections,
                }
            }
        }
    }


_SAFE_MARGINS = {"technical": {"safe_zone_margins_pct": {"top": 14, "bottom": 35, "left": 6, "right": 6}}}


def test_check_logo_presence_no_brief_is_informational_pass():
    ak = _ak_with_logo(3, 0, [])
    status, message, _ = checks.check_logo_presence(ak, {}, None)
    assert status == FindingStatus.PASS
    assert "no marca" in message


def test_check_logo_presence_brief_without_requirement_is_informational_pass():
    ak = _ak_with_logo(3, 0, [])
    brief = {"brand": {"required_logo_present": False}}
    status, _, _ = checks.check_logo_presence(ak, {}, brief)
    assert status == FindingStatus.PASS


def test_check_logo_presence_required_and_found_passes():
    ak = _ak_with_logo(3, 1, [])
    brief = {"brand": {"required_logo_present": True}}
    status, _, _ = checks.check_logo_presence(ak, {}, brief)
    assert status == FindingStatus.PASS


def test_check_logo_presence_required_and_not_found_fails():
    ak = _ak_with_logo(3, 0, [])
    brief = {"brand": {"required_logo_present": True}}
    status, _, _ = checks.check_logo_presence(ak, {}, brief)
    assert status == FindingStatus.FAIL


def test_check_logo_safe_zone_no_brief_is_informational_pass():
    ak = _ak_with_logo(1, 1, [{"detected": True, "bbox_pct": {"x_min": 0, "y_min": 0, "x_max": 1, "y_max": 1}}])
    status, message, _ = checks.check_logo_safe_zone(ak, _SAFE_MARGINS, None)
    assert status == FindingStatus.PASS
    assert "no marca" in message


def test_check_logo_safe_zone_not_required_is_informational_pass():
    ak = _ak_with_logo(1, 1, [{"detected": True, "bbox_pct": {"x_min": 0, "y_min": 0, "x_max": 1, "y_max": 1}}])
    brief = {"brand": {"logo_safe_zone_required": False}}
    status, _, _ = checks.check_logo_safe_zone(ak, _SAFE_MARGINS, brief)
    assert status == FindingStatus.PASS


def test_check_logo_safe_zone_no_detection_is_informational_pass():
    ak = _ak_with_logo(3, 0, [])
    brief = {"brand": {"logo_safe_zone_required": True}}
    status, message, _ = checks.check_logo_safe_zone(ak, _SAFE_MARGINS, brief)
    assert status == FindingStatus.PASS
    assert "no hay posición" in message.lower()


def test_check_logo_safe_zone_within_margins_passes():
    # margins: top=14,bottom=35,left=6,right=6 -> área segura x[0.06,0.94] y[0.14,0.65]
    detections = [{"detected": True, "bbox_pct": {"x_min": 0.30, "y_min": 0.30, "x_max": 0.50, "y_max": 0.50}}]
    ak = _ak_with_logo(1, 1, detections)
    brief = {"brand": {"logo_safe_zone_required": True}}
    status, _, _ = checks.check_logo_safe_zone(ak, _SAFE_MARGINS, brief)
    assert status == FindingStatus.PASS


def test_check_logo_safe_zone_single_edge_violation_fails():
    # y_min=0.05 < top margin 0.14 -> invade el margen superior
    detections = [{"detected": True, "bbox_pct": {"x_min": 0.30, "y_min": 0.05, "x_max": 0.50, "y_max": 0.30}}]
    ak = _ak_with_logo(1, 1, detections)
    brief = {"brand": {"logo_safe_zone_required": True}}
    status, _, evidence = checks.check_logo_safe_zone(ak, _SAFE_MARGINS, brief)
    assert status == FindingStatus.FAIL
    assert len(evidence["violations"]) == 1


def test_check_logo_safe_zone_multiple_edge_violations_fails():
    # Ejemplo real de Instagram Stories: x_min=0.70,y_min=0.05,x_max=0.95,y_max=0.18
    # viola top (0.05 < 0.14) Y right (0.95 > 0.94) simultáneamente.
    detections = [{"detected": True, "bbox_pct": {"x_min": 0.70, "y_min": 0.05, "x_max": 0.95, "y_max": 0.18}}]
    ak = _ak_with_logo(1, 1, detections)
    brief = {"brand": {"logo_safe_zone_required": True}}
    status, _, evidence = checks.check_logo_safe_zone(ak, _SAFE_MARGINS, brief)
    assert status == FindingStatus.FAIL
    violated_edges = {v["edge"] for v in evidence["violations"]}
    assert violated_edges == {"top", "right"}


def test_check_logo_safe_zone_null_margin_is_skipped_not_failed():
    # bottom=None -> aunque y_max=0.99 "violaría" el margen inferior si se
    # evaluara, al no estar publicado se omite y no debe fallar por eso.
    margins = {"technical": {"safe_zone_margins_pct": {"top": 14, "bottom": None, "left": None, "right": None}}}
    detections = [{"detected": True, "bbox_pct": {"x_min": 0.30, "y_min": 0.30, "x_max": 0.50, "y_max": 0.99}}]
    ak = _ak_with_logo(1, 1, detections)
    brief = {"brand": {"logo_safe_zone_required": True}}
    status, _, _ = checks.check_logo_safe_zone(ak, margins, brief)
    assert status == FindingStatus.PASS


def test_check_logo_safe_zone_boundary_exactly_at_margin_passes():
    # x_min exactamente en left/100 = 0.06 -> no debe contar como violación (no es '<').
    detections = [{"detected": True, "bbox_pct": {"x_min": 0.06, "y_min": 0.30, "x_max": 0.50, "y_max": 0.50}}]
    ak = _ak_with_logo(1, 1, detections)
    brief = {"brand": {"logo_safe_zone_required": True}}
    status, _, _ = checks.check_logo_safe_zone(ak, _SAFE_MARGINS, brief)
    assert status == FindingStatus.PASS


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
