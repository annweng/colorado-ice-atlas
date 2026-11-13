"""Attach documented local names when NHDPlus has no GNIS_NAME."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ALIAS_PATH = Path(__file__).with_name("aliases.json")


def load_aliases() -> dict[str, dict[str, Any]]:
    if not ALIAS_PATH.exists():
        return {}
    rows = json.loads(ALIAS_PATH.read_text())
    return {row["waterbody_id"]: row for row in rows}


def apply_alias(record: dict[str, Any], aliases: dict[str, dict[str, Any]] | None = None) -> dict[str, Any]:
    aliases = aliases if aliases is not None else load_aliases()
    alias = aliases.get(record.get("id") or record.get("waterbody_id") or "")
    if not alias:
        return record
    names = list(record.get("alternative_names") or [])
    for name in alias.get("alternative_names") or []:
        if name not in names:
            names.append(name)
    record["alternative_names"] = names
    record["display_name"] = alias["display_name"]
    if "name" in record:
        record["name"] = alias["display_name"]
    record["name_source"] = alias.get("name_source")
    if not record.get("official_name"):
        record["named"] = True
    return record
