"""Funciones de verificación (una por regla 'implementable: true' del catálogo)
más el factory compartido para las reglas NOT_EVALUATED.

Firma común: check_fn(asset_knowledge: dict, profile: dict, brief: dict | None)
             -> tuple[FindingStatus, str, dict | None]
             (status, message, evidence) — el motor (engine.py) arma el
             Finding completo agregando rule_id/layer/severity.
"""
from __future__ import annotations

import math
from collections.abc import Callable
from typing import Any

from .loaders import get_field
from .models import FindingStatus

CheckResult = tuple[FindingStatus, str, dict[str, Any] | None]
CheckFn = Callable[[dict, dict, dict | None], CheckResult]

# Umbral heurístico de "demasiadas palabras en un solo frame" para el proxy
# de legibilidad basado en conteo de palabras OCR (VISUAL_TEXT_DENSITY).
# No es un análisis real de legibilidad/composición.
TEXT_DENSITY_WARN_THRESHOLD = 40

# Umbral heurístico (distancia Euclidiana RGB, sobre un máximo teórico de
# sqrt(255^2*3) ~= 441.7) para considerar que un color dominante extraído
# coincide con un color de marca del brief. JPEG + extracción a 1fps +
# promediado por centroides de k-means hacen que la reproducción exacta del
# hex de marca sea poco realista; 60 tolera drift de iluminación/compresión
# moderado sin dejar pasar colores de familia de tono claramente distinta.
DOMINANT_COLOR_DISTANCE_THRESHOLD = 60

# Umbral heurístico (segundos) de silencio continuo máximo aceptable dentro
# del audio. Sin fuente de datos por canal/brief -- mismo patrón que
# TEXT_DENSITY_WARN_THRESHOLD, un proxy documentado, no un estándar publicado.
MAX_SILENCE_DURATION_WARN_S = 2.0

# Tolerancia relativa al comparar el aspect ratio real del asset contra los
# aspect ratios soportados por el placement.
ASPECT_RATIO_TOLERANCE = 0.02

# Tolerancia absoluta (fps) al comparar contra una lista de frame rates
# discretos permitidos -- cubre drift típico de NTSC (29.97 vs 30, etc.).
FRAME_RATE_TOLERANCE = 0.1

# ffprobe devuelve nombres técnicos de códec (codec_name) distintos a los
# nombres "de marketing" usados en context/matriz_medios.json / profiles/.
# Mapeo best-effort; códecs no listados se comparan por igualdad de string
# case-insensitive tal cual.
CODEC_ALIASES: dict[str, str] = {
    "h264": "H.264",
    "avc": "H.264",
    "avc1": "H.264",
    "hevc": "H.265",
    "h265": "H.265",
    "vp9": "VP9",
    "vp8": "VP8",
    "av1": "AV1",
    "mpeg4": "MPEG-4",
    "mpeg2video": "MPEG-2",
    "prores": "ProRes",
}


def normalize_codec(codec: str) -> str:
    return CODEC_ALIASES.get(codec.strip().lower(), codec.strip())


def _parse_ratio(ratio_str: str) -> float | None:
    """'9:16' -> 0.5625. Devuelve None si el string no tiene forma W:H."""
    parts = ratio_str.split(":")
    if len(parts) != 2:
        return None
    try:
        w, h = float(parts[0]), float(parts[1])
        return w / h if h else None
    except ValueError:
        return None


def _closest_ratio_match(actual: float, allowed: list[str], tolerance: float) -> str | None:
    for ratio_str in allowed:
        target = _parse_ratio(ratio_str)
        if target is not None and abs(actual - target) <= tolerance * target:
            return ratio_str
    return None


def check_aspect_ratio(asset_knowledge: dict, profile: dict, brief: dict | None) -> CheckResult:
    width = get_field(asset_knowledge, "asset.metadata.width")
    height = get_field(asset_knowledge, "asset.metadata.height")
    allowed = get_field(profile, "technical.aspect_ratios")

    actual_ratio = width / height
    match = _closest_ratio_match(actual_ratio, allowed, ASPECT_RATIO_TOLERANCE)
    evidence = {"width": width, "height": height, "actual_ratio": round(actual_ratio, 4), "allowed": allowed}

    if match:
        return FindingStatus.PASS, f"Aspect ratio {width}x{height} coincide con {match}.", evidence
    return (
        FindingStatus.FAIL,
        f"Aspect ratio {width}x{height} (~{actual_ratio:.3f}) no coincide con ninguno de {allowed}.",
        evidence,
    )


def check_resolution_min(asset_knowledge: dict, profile: dict, brief: dict | None) -> CheckResult:
    width = get_field(asset_knowledge, "asset.metadata.width")
    height = get_field(asset_knowledge, "asset.metadata.height")
    min_w, min_h = get_field(profile, "technical.resolution_min")
    evidence = {"width": width, "height": height, "min_w": min_w, "min_h": min_h}

    problems = []
    if min_w is not None and width < min_w:
        problems.append(f"ancho {width}px < mínimo {min_w}px")
    if min_h is not None and height < min_h:
        problems.append(f"alto {height}px < mínimo {min_h}px")

    if problems:
        return FindingStatus.FAIL, "Resolución por debajo del mínimo: " + "; ".join(problems), evidence
    return FindingStatus.PASS, f"Resolución {width}x{height} cumple el mínimo del placement.", evidence


def check_duration_min(asset_knowledge: dict, profile: dict, brief: dict | None) -> CheckResult:
    duration = get_field(asset_knowledge, "asset.metadata.duration")
    min_s = get_field(profile, "technical.duration_min_s")
    evidence = {"duration_s": duration, "duration_min_s": min_s}

    if duration < min_s:
        return FindingStatus.FAIL, f"Duración {duration}s menor al mínimo {min_s}s del placement.", evidence
    return FindingStatus.PASS, f"Duración {duration}s cumple el mínimo {min_s}s.", evidence


def check_duration_max(asset_knowledge: dict, profile: dict, brief: dict | None) -> CheckResult:
    duration = get_field(asset_knowledge, "asset.metadata.duration")
    max_s = get_field(profile, "technical.duration_max_s")
    evidence = {"duration_s": duration, "duration_max_s": max_s}

    if duration > max_s:
        return FindingStatus.FAIL, f"Duración {duration}s excede el máximo {max_s}s del placement.", evidence
    return FindingStatus.PASS, f"Duración {duration}s cumple el máximo {max_s}s.", evidence


def check_orientation(asset_knowledge: dict, profile: dict, brief: dict | None) -> CheckResult:
    orientation = get_field(asset_knowledge, "asset.metadata.orientation")
    width = get_field(asset_knowledge, "asset.metadata.width")
    height = get_field(asset_knowledge, "asset.metadata.height")
    expected = "vertical" if height > width else ("horizontal" if width > height else "square")
    evidence = {"orientation_reportada": orientation, "width": width, "height": height}

    if orientation != expected:
        return (
            FindingStatus.FAIL,
            f"orientation='{orientation}' no es consistente con width/height (se esperaba '{expected}').",
            evidence,
        )
    return FindingStatus.PASS, f"orientation='{orientation}' es consistente con width/height.", evidence


def check_frame_rate(asset_knowledge: dict, profile: dict, brief: dict | None) -> CheckResult:
    fps = get_field(asset_knowledge, "asset.metadata.fps")
    allowed = get_field(profile, "technical.frame_rate")
    evidence = {"fps": fps, "frame_rate_permitido": allowed}

    if isinstance(allowed, list):
        match = any(abs(fps - v) <= FRAME_RATE_TOLERANCE for v in allowed)
        if not match:
            return (
                FindingStatus.FAIL,
                f"fps={fps} no coincide con ninguno de los valores permitidos {allowed}.",
                evidence,
            )
        return FindingStatus.PASS, f"fps={fps} coincide con un valor permitido de {allowed}.", evidence

    # Un único número en el profile se interpreta como mínimo (ej. GDN
    # in-banner: "mín 14fps"), no como valor exacto.
    if fps < allowed:
        return FindingStatus.FAIL, f"fps={fps} por debajo del mínimo requerido ({allowed}fps).", evidence
    return FindingStatus.PASS, f"fps={fps} cumple el mínimo requerido ({allowed}fps).", evidence


def check_file_size(asset_knowledge: dict, profile: dict, brief: dict | None) -> CheckResult:
    size_bytes = get_field(asset_knowledge, "asset.metadata.file_size_bytes")
    max_mb = get_field(profile, "technical.max_file_size_mb")
    size_mb = size_bytes / (1024 * 1024)
    evidence = {"file_size_mb": round(size_mb, 2), "max_file_size_mb": max_mb}

    if size_mb > max_mb:
        return FindingStatus.FAIL, f"Peso {size_mb:.2f}MB excede el máximo {max_mb}MB del placement.", evidence
    return FindingStatus.PASS, f"Peso {size_mb:.2f}MB cumple el máximo {max_mb}MB.", evidence


def check_codec(asset_knowledge: dict, profile: dict, brief: dict | None) -> CheckResult:
    codec = get_field(asset_knowledge, "asset.metadata.codec")
    allowed = get_field(profile, "technical.codecs") or []
    allowed_optional = get_field(profile, "technical.codecs_optional") or []
    normalized = normalize_codec(codec)
    accepted = {c.upper() for c in [*allowed, *allowed_optional]}
    evidence = {"codec": codec, "codec_normalizado": normalized, "codecs_permitidos": allowed, "codecs_opcionales": allowed_optional}

    if normalized.upper() not in accepted:
        return (
            FindingStatus.FAIL,
            f"Códec '{codec}' (normalizado: '{normalized}') no está entre los permitidos {allowed + allowed_optional}.",
            evidence,
        )
    return FindingStatus.PASS, f"Códec '{codec}' (normalizado: '{normalized}') es válido para el placement.", evidence


def check_text_presence(asset_knowledge: dict, profile: dict, brief: dict | None) -> CheckResult:
    frames_with_text = get_field(asset_knowledge, "visual.summary.frames_with_text")
    frames_processed = get_field(asset_knowledge, "visual.summary.frames_processed")
    evidence = {"frames_with_text": frames_with_text, "frames_processed": frames_processed}

    if frames_with_text == 0:
        return FindingStatus.FAIL, "Ningún frame tiene texto detectado por OCR.", evidence
    return FindingStatus.PASS, f"{frames_with_text}/{frames_processed} frames con texto detectado.", evidence


def check_text_density(asset_knowledge: dict, profile: dict, brief: dict | None) -> CheckResult:
    max_words = get_field(asset_knowledge, "visual.summary.max_words_in_frame")
    evidence = {"max_words_in_frame": max_words, "umbral": TEXT_DENSITY_WARN_THRESHOLD}

    if max_words > TEXT_DENSITY_WARN_THRESHOLD:
        message = (
            f"Un frame tiene {max_words} palabras (> {TEXT_DENSITY_WARN_THRESHOLD}); "
            f"proxy de posible sobrecarga de texto, no un análisis real de legibilidad."
        )
        return FindingStatus.FAIL, message, evidence
    return FindingStatus.PASS, f"Máximo {max_words} palabras en un frame, dentro del proxy aceptable.", evidence


def _hex_to_rgb(hex_str: str) -> tuple[int, int, int]:
    h = hex_str.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def _rgb_distance(hex_a: str, hex_b: str) -> float:
    r1, g1, b1 = _hex_to_rgb(hex_a)
    r2, g2, b2 = _hex_to_rgb(hex_b)
    return math.sqrt((r1 - r2) ** 2 + (g1 - g2) ** 2 + (b1 - b2) ** 2)


def check_cta_detection(asset_knowledge: dict, profile: dict, brief: dict | None) -> CheckResult:
    accepted_texts = ((brief or {}).get("cta") or {}).get("accepted_texts") or []
    frames = get_field(asset_knowledge, "visual.frames") or []
    evidence = {"frames_scanned": len(frames), "accepted_texts": accepted_texts}

    if not accepted_texts:
        return (
            FindingStatus.PASS,
            "CTA no evaluado: el brief no especifica cta.accepted_texts.",
            evidence,
        )

    matches = []
    for frame in frames:
        for text in frame.get("text") or []:
            for accepted in accepted_texts:
                if accepted.lower() in text.lower():
                    matches.append(
                        {
                            "frame": frame.get("frame"),
                            "time": frame.get("time"),
                            "ocr_text": text,
                            "matched_cta": accepted,
                        }
                    )
    evidence["matches"] = matches

    if matches:
        m = matches[0]
        return (
            FindingStatus.PASS,
            f"CTA '{m['matched_cta']}' detectado en frame {m['frame']} (t={m['time']}s) vía OCR.",
            evidence,
        )
    return (
        FindingStatus.FAIL,
        f"Ningún frame contiene alguno de los CTA esperados {accepted_texts} (OCR de {len(frames)} frames).",
        evidence,
    )


def check_dominant_color(asset_knowledge: dict, profile: dict, brief: dict | None) -> CheckResult:
    brand_colors = ((brief or {}).get("brand") or {}).get("brand_colors_hex") or []
    dominant_colors = get_field(asset_knowledge, "visual.summary.dominant_colors") or []
    evidence = {
        "dominant_colors": dominant_colors,
        "brand_colors_hex": brand_colors,
        "threshold": DOMINANT_COLOR_DISTANCE_THRESHOLD,
    }

    if not brand_colors:
        return (
            FindingStatus.PASS,
            "Color dominante no evaluado: el brief no especifica brand.brand_colors_hex.",
            evidence,
        )
    if not dominant_colors:
        return FindingStatus.FAIL, "No hay colores dominantes extraídos para comparar.", evidence

    best_distance, best_dom, best_brand = min(
        ((_rgb_distance(d, b), d, b) for d in dominant_colors for b in brand_colors),
        key=lambda t: t[0],
    )
    evidence["closest_match"] = {"dominant": best_dom, "brand": best_brand, "distance": round(best_distance, 1)}

    if best_distance <= DOMINANT_COLOR_DISTANCE_THRESHOLD:
        pass_message = (
            f"Color dominante {best_dom} cerca del color de marca {best_brand} "
            f"(distancia {best_distance:.1f} <= {DOMINANT_COLOR_DISTANCE_THRESHOLD})."
        )
        return FindingStatus.PASS, pass_message, evidence

    fail_message = (
        f"Ningún color dominante está cerca de la paleta de marca "
        f"(distancia mínima {best_distance:.1f} > {DOMINANT_COLOR_DISTANCE_THRESHOLD}, "
        f"entre {best_dom} y {best_brand})."
    )
    return FindingStatus.FAIL, fail_message, evidence


def check_logo_presence(asset_knowledge: dict, profile: dict, brief: dict | None) -> CheckResult:
    required = ((brief or {}).get("brand") or {}).get("required_logo_present")
    logo_detection = get_field(asset_knowledge, "visual.summary.logo_detection")
    frames_with_logo = logo_detection.get("frames_with_logo", 0)
    frames_analyzed = logo_detection.get("frames_analyzed", 0)
    evidence = {
        "frames_with_logo": frames_with_logo,
        "frames_analyzed": frames_analyzed,
        "reference_image": logo_detection.get("reference_image"),
    }

    if not required:
        return (
            FindingStatus.PASS,
            "Presencia de logo no evaluada: el brief no marca brand.required_logo_present.",
            evidence,
        )
    if frames_with_logo > 0:
        return (
            FindingStatus.PASS,
            f"Logo detectado en {frames_with_logo}/{frames_analyzed} frames analizados.",
            evidence,
        )
    return (
        FindingStatus.FAIL,
        f"Logo no detectado en ninguno de los {frames_analyzed} frames analizados.",
        evidence,
    )


def check_logo_safe_zone(asset_knowledge: dict, profile: dict, brief: dict | None) -> CheckResult:
    safe_zone_required = ((brief or {}).get("brand") or {}).get("logo_safe_zone_required")
    logo_detection = get_field(asset_knowledge, "visual.summary.logo_detection")
    margins = get_field(profile, "technical.safe_zone_margins_pct")
    frames_with_logo = logo_detection.get("frames_with_logo", 0)
    detections = logo_detection.get("detections", [])
    evidence = {"margins_pct": margins, "frames_with_logo": frames_with_logo}

    if not safe_zone_required:
        return (
            FindingStatus.PASS,
            "Zona segura de logo no evaluada: el brief no marca brand.logo_safe_zone_required.",
            evidence,
        )
    if frames_with_logo == 0:
        return (
            FindingStatus.PASS,
            "Logo no detectado en ningún frame; no hay posición que evaluar.",
            evidence,
        )

    violations = []
    for d in detections:
        if not d.get("detected"):
            continue
        bbox = d.get("bbox_pct") or {}
        edges = [
            ("left", margins.get("left"), bbox.get("x_min"), lambda v, m: v < m / 100),
            ("right", margins.get("right"), bbox.get("x_max"), lambda v, m: v > 1 - m / 100),
            ("top", margins.get("top"), bbox.get("y_min"), lambda v, m: v < m / 100),
            ("bottom", margins.get("bottom"), bbox.get("y_max"), lambda v, m: v > 1 - m / 100),
        ]
        for edge, margin, value, violates in edges:
            if margin is None:
                continue  # borde sin dato publicado -> no se puede validar, se omite
            if violates(value, margin):
                violations.append({"frame": d.get("frame"), "time": d.get("time"), "edge": edge, "bbox_pct": bbox})

    evidence["violations"] = violations
    if violations:
        return FindingStatus.FAIL, f"{len(violations)} detección(es) del logo invaden la zona segura.", evidence
    return (
        FindingStatus.PASS,
        f"Las {frames_with_logo} detección(es) del logo respetan la zona segura configurada.",
        evidence,
    )


def check_audio_present(asset_knowledge: dict, profile: dict, brief: dict | None) -> CheckResult:
    audio_present = get_field(asset_knowledge, "asset.metadata.audio_present")
    evidence = {"audio_present": audio_present}

    if not audio_present:
        return FindingStatus.FAIL, "El asset no tiene pista de audio.", evidence
    return FindingStatus.PASS, "El asset tiene pista de audio.", evidence


def check_speech_detected(asset_knowledge: dict, profile: dict, brief: dict | None) -> CheckResult:
    speech_detected = get_field(asset_knowledge, "audio.summary.speech_detected")
    evidence = {"speech_detected": speech_detected}

    if not speech_detected:
        return FindingStatus.FAIL, "No se detectó voz/habla en la pista de audio.", evidence
    return FindingStatus.PASS, "Se detectó voz/habla en la pista de audio.", evidence


def check_language(asset_knowledge: dict, profile: dict, brief: dict | None) -> CheckResult:
    detected = get_field(asset_knowledge, "audio.summary.language")
    expected = (brief or {}).get("expected_language")
    evidence = {"detected_language": detected, "expected_language": expected}

    if expected is None:
        return FindingStatus.PASS, f"Idioma detectado: '{detected}' (brief no especifica idioma esperado).", evidence
    if detected != expected:
        return FindingStatus.FAIL, f"Idioma detectado '{detected}' no coincide con el esperado '{expected}'.", evidence
    return FindingStatus.PASS, f"Idioma detectado '{detected}' coincide con el esperado.", evidence


def check_narration_present(asset_knowledge: dict, profile: dict, brief: dict | None) -> CheckResult:
    word_count = get_field(asset_knowledge, "audio.summary.word_count")
    evidence = {"word_count": word_count}

    if word_count == 0:
        return (
            FindingStatus.FAIL,
            "0 palabras transcritas (proxy de narración ausente; no reemplaza detección real de silencios).",
            evidence,
        )
    return FindingStatus.PASS, f"{word_count} palabras transcritas.", evidence


def check_silence_detection(asset_knowledge: dict, profile: dict, brief: dict | None) -> CheckResult:
    silence_analysis = get_field(asset_knowledge, "audio.summary.silence_analysis")
    max_silence = silence_analysis.get("max_silence_s", 0)
    evidence = {
        "max_silence_s": max_silence,
        "threshold_s": MAX_SILENCE_DURATION_WARN_S,
        "silent_segments": silence_analysis.get("silent_segments"),
    }

    if max_silence > MAX_SILENCE_DURATION_WARN_S:
        return (
            FindingStatus.FAIL,
            f"Silencio de {max_silence}s excede el máximo aceptable de {MAX_SILENCE_DURATION_WARN_S}s.",
            evidence,
        )
    return (
        FindingStatus.PASS,
        f"Silencio máximo {max_silence}s dentro de lo aceptable.",
        evidence,
    )


def check_volume_loudness(asset_knowledge: dict, profile: dict, brief: dict | None) -> CheckResult:
    loudness_analysis = get_field(asset_knowledge, "audio.summary.loudness_analysis")
    measured = loudness_analysis.get("integrated_lufs")
    targets = get_field(profile, "technical.loudness_targets_lufs")
    evidence = {"measured_lufs": measured, "targets": targets}

    if measured is None:
        return (
            FindingStatus.FAIL,
            "No se pudo medir el loudness del audio (clip muy corto o silencioso).",
            evidence,
        )

    scored = [{**t, "distance": round(abs(measured - t["target_lufs"]), 2)} for t in targets]
    matches = [t for t in scored if t["distance"] <= t["tolerance_lu"]]
    evidence["scored_targets"] = scored

    if matches:
        best = min(matches, key=lambda t: t["distance"])
        evidence["closest_match"] = best
        pass_message = (
            f"Loudness medido {measured} LUFS dentro de tolerancia del target {best['region']} "
            f"({best['target_lufs']}±{best['tolerance_lu']} LUFS, distancia {best['distance']})."
        )
        return FindingStatus.PASS, pass_message, evidence

    closest_miss = min(scored, key=lambda t: t["distance"])
    evidence["closest_match"] = closest_miss
    fail_message = (
        f"Loudness medido {measured} LUFS fuera de tolerancia de todos los targets publicados "
        f"(más cercano: {closest_miss['region']} {closest_miss['target_lufs']}±{closest_miss['tolerance_lu']} LUFS, "
        f"distancia {closest_miss['distance']})."
    )
    return FindingStatus.FAIL, fail_message, evidence


def not_evaluated(reason: str) -> CheckResult:
    """Factory compartido por todas las reglas con implementable: false."""
    return FindingStatus.NOT_EVALUATED, f"No evaluado: {reason}", None


CHECK_REGISTRY: dict[str, CheckFn] = {
    "check_aspect_ratio": check_aspect_ratio,
    "check_resolution_min": check_resolution_min,
    "check_duration_min": check_duration_min,
    "check_duration_max": check_duration_max,
    "check_orientation": check_orientation,
    "check_frame_rate": check_frame_rate,
    "check_file_size": check_file_size,
    "check_codec": check_codec,
    "check_text_presence": check_text_presence,
    "check_text_density": check_text_density,
    "check_cta_detection": check_cta_detection,
    "check_dominant_color": check_dominant_color,
    "check_logo_presence": check_logo_presence,
    "check_logo_safe_zone": check_logo_safe_zone,
    "check_audio_present": check_audio_present,
    "check_speech_detected": check_speech_detected,
    "check_language": check_language,
    "check_narration_present": check_narration_present,
    "check_silence_detection": check_silence_detection,
    "check_volume_loudness": check_volume_loudness,
}
