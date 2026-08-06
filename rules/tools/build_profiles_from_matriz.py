"""Genera profiles/*.yaml a partir de context/matriz_medios.json.

Los profiles NO se editan a mano: son un espejo del specs de plataforma.
Este script es también el que corre en CI (sync-check) para detectar si
profiles/ quedó desactualizado respecto a la matriz de medios.

Uso:
    python -m rules.tools.build_profiles_from_matriz [--check]

--check: no escribe archivos, solo compara contra lo ya generado y sale con
código != 0 si hay diferencias (usado por el pipeline de Harness).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
MATRIZ_PATH = REPO_ROOT / "context" / "matriz_medios.json"
PROFILES_DIR = REPO_ROOT / "profiles"

TECHNICAL_FIELDS = (
    "aspect_ratios",
    "aspect_ratio_recommended",
    "aspect_ratio_tolerance",
    "aspect_ratio_range",
    "resolution_min",
    "resolution_recommended",
    "resolution_max",
    "duration_min_s",
    "duration_max_s",
    "duration_allowed_s",
    "duration_allowed_s_3p",
    "max_file_size_mb",
    "min_file_size_mb",
    "codecs",
    "codecs_optional",
    "containers",
    "frame_rate",
    "frame_rate_recommended",
    "bitrate_kbps",
    "vast_versions_supported",
    "captions_required",
    "safe_zone_notes",
    "safe_zone_margins_pct",
    "audio",
    "loudness_targets_lufs",
)


def slugify(*parts: str) -> str:
    seen = []
    for p in parts:
        if not p:
            continue
        ascii_p = unicodedata.normalize("NFKD", p).encode("ascii", "ignore").decode("ascii")
        norm = re.sub(r"[^a-z0-9]+", "_", ascii_p.lower()).strip("_")
        if norm and norm not in seen:
            seen.append(norm)
    slug = "_".join(seen)
    slug = re.sub(r"_+", "_", slug).strip("_")
    return slug


def build_profile(entry: dict) -> dict:
    profile_id = slugify(entry["platform"], entry.get("channel", ""), entry["placement"])
    technical = {field: entry.get(field) for field in TECHNICAL_FIELDS if field in entry}
    profile = {
        "schema_version": 1,
        "profile_id": profile_id,
        "platform": entry["platform"],
        "channel": entry.get("channel", entry["platform"]),
        "placement": entry["placement"],
        "technical": technical,
    }
    if entry.get("source_url"):
        profile["source_url"] = entry["source_url"]
    if entry.get("notes"):
        profile["notes"] = entry["notes"]
    return profile


def render_yaml(profile: dict) -> str:
    header = (
        "# AUTOGENERADO por rules/tools/build_profiles_from_matriz.py"
        " desde context/matriz_medios.json - NO editar a mano.\n"
    )
    body = yaml.safe_dump(profile, sort_keys=False, allow_unicode=True, width=100)
    return header + body


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="no escribir, solo verificar sync")
    args = parser.parse_args()

    matriz = json.loads(MATRIZ_PATH.read_text(encoding="utf-8"))
    placements = matriz["placements"]

    generated = {}
    seen_ids = set()
    for entry in placements:
        profile = build_profile(entry)
        pid = profile["profile_id"]
        if pid in seen_ids:
            raise SystemExit(f"profile_id duplicado: {pid} (colisión de slug, revisar matriz_medios.json)")
        seen_ids.add(pid)
        generated[pid] = render_yaml(profile)

    if args.check:
        drift = []
        for pid, content in generated.items():
            path = PROFILES_DIR / f"{pid}.yaml"
            if not path.exists() or path.read_text(encoding="utf-8") != content:
                drift.append(pid)
        existing_ids = {p.stem for p in PROFILES_DIR.glob("*.yaml")}
        stale = existing_ids - set(generated.keys())
        if drift or stale:
            if drift:
                print(f"Perfiles desactualizados respecto a matriz_medios.json: {sorted(drift)}")
            if stale:
                print(f"Perfiles obsoletos (ya no están en matriz_medios.json): {sorted(stale)}")
            print("Correr: python -m rules.tools.build_profiles_from_matriz")
            return 1
        print(f"{len(generated)} profiles sincronizados con matriz_medios.json.")
        return 0

    PROFILES_DIR.mkdir(exist_ok=True)
    for pid, content in generated.items():
        (PROFILES_DIR / f"{pid}.yaml").write_text(content, encoding="utf-8")
    print(f"{len(generated)} profiles generados en {PROFILES_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
