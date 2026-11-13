"""Patch current snapshots with documented local names and geometry bboxes."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from data.processing.aliases import apply_alias, load_aliases
from data.processing.pipeline import FRONTEND_DATA, PROCESSED, _geom_bbox, jsonable


def _write(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(jsonable(payload), allow_nan=False), encoding="utf-8")


def main() -> None:
    aliases = load_aliases()
    map_path = FRONTEND_DATA / "map.geojson"
    map_fc = json.loads(map_path.read_text())
    bbox_by_id: dict[str, list[float] | None] = {}
    for feature in map_fc["features"]:
        props = apply_alias(feature["properties"], aliases)
        bbox = _geom_bbox(feature.get("geometry"))
        props["bbox"] = bbox
        feature["properties"] = props
        bbox_by_id[props["id"]] = bbox

    summaries_path = FRONTEND_DATA / "summaries.json"
    summaries = json.loads(summaries_path.read_text())
    for row in summaries:
        apply_alias(row, aliases)
        row["bbox"] = bbox_by_id.get(row["id"]) or row.get("bbox")

    _write(map_path, map_fc)
    _write(PROCESSED / "map.geojson", map_fc)
    _write(summaries_path, summaries)
    _write(PROCESSED / "summaries.json", summaries)
    print(f"patched {len(summaries)} summaries and {len(map_fc['features'])} map features")


if __name__ == "__main__":
    main()
