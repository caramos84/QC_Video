"""Funciones de verificación (una por regla 'implementable: true' del catálogo)
más el factory compartido para las reglas NOT_EVALUATED.

Firma común: check_fn(asset_knowledge: dict, profile: dict, brief: dict | None)
             -> tuple[FindingStatus, str, dict | None]
             (status, message, evidence) — el motor (engine.py) arma el
             Finding completo agregando rule_id/layer/severity.
"""
from __future__ import annotations

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

# Tolerancia relativa al comparar el aspect ratio real del asset contra los
# aspect ratios soportados por el placement.
ASPECT_RATIO_TOLERANCE = 0.02


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


def not_evaluated(reason: str) -> CheckResult:
    """Factory compartido por todas las reglas con implementable: false."""
    return FindingStatus.NOT_EVALUATED, f"No evaluado: {reason}", None


CHECK_REGISTRY: dict[str, CheckFn] = {
    "check_aspect_ratio": check_aspect_ratio,
    "check_resolution_min": check_resolution_min,
    "check_duration_min": check_duration_min,
    "check_duration_max": check_duration_max,
    "check_orientation": check_orientation,
    "check_text_presence": check_text_presence,
    "check_text_density": check_text_density,
    "check_audio_present": check_audio_present,
    "check_speech_detected": check_speech_detected,
    "check_language": check_language,
    "check_narration_present": check_narration_present,
}
