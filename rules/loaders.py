"""Carga y validación de los inputs del Motor de QC:
asset_knowledge.json, profile, brief y el catálogo de reglas."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import jsonschema
import yaml

from .models import Rule, Severity

PACKAGE_DIR = Path(__file__).resolve().parent
SCHEMA_DIR = PACKAGE_DIR / "schema"
CATALOG_PATH = PACKAGE_DIR / "catalog.yaml"
SCORING_CONFIG_PATH = PACKAGE_DIR / "scoring_config.yaml"

PathLike = str | Path


def _load_schema(name: str) -> dict:
    return json.loads((SCHEMA_DIR / name).read_text(encoding="utf-8"))


def load_asset_knowledge(path: PathLike) -> dict:
    """asset_knowledge.json no tiene JSON Schema propio (es la salida libre
    de Notebook 04 actual, consolidando metadata/visual/audio) — el motor
    tolera estructura parcial y usa get_field() para navegarlo con seguridad."""
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load_profile(path: PathLike) -> dict:
    doc = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    jsonschema.validate(doc, _load_schema("profile.schema.json"))
    return doc


def load_brief(path: PathLike | None) -> dict | None:
    if path is None:
        return None
    doc = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    jsonschema.validate(doc, _load_schema("brief.schema.json"))
    return doc


def load_catalog(path: PathLike = CATALOG_PATH) -> list[Rule]:
    doc = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    rules = []
    for r in doc["rules"]:
        rules.append(
            Rule(
                rule_id=r["rule_id"],
                layer=r["layer"],
                default_severity=Severity(r["default_severity"]),
                implementable=r["implementable"],
                description=r["description"],
                requires_fields=r.get("requires_fields", []),
                requires_profile_fields=r.get("requires_profile_fields", []),
                check_fn=r.get("check_fn"),
                not_evaluated_reason=r.get("not_evaluated_reason"),
            )
        )
    return rules


def load_scoring_config(path: PathLike = SCORING_CONFIG_PATH) -> dict:
    return yaml.safe_load(Path(path).read_text(encoding="utf-8"))


def get_field(data: dict, dotted_path: str) -> Any:
    """Navega un path tipo 'asset.metadata.width' dentro de un dict anidado.
    Devuelve None si cualquier tramo falta o es None; nunca lanza KeyError.
    Un valor None explícito en el JSON/YAML de origen se trata igual que
    'campo ausente' -- ambos casos deben producir NOT_EVALUATED."""
    node: Any = data
    for part in dotted_path.split("."):
        if not isinstance(node, dict) or part not in node:
            return None
        node = node[part]
    return node


def has_field(data: dict, dotted_path: str) -> bool:
    return get_field(data, dotted_path) is not None


def missing_fields(data: dict, dotted_paths: list[str]) -> list[str]:
    return [p for p in dotted_paths if not has_field(data, p)]
