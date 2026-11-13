#!/usr/bin/env python3
"""Rebuild compact frontend snapshots from the last pipeline outputs without refetching."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from data.processing.pipeline import FRONTEND_DATA, PROCESSED, jsonable


def main() -> None:
    catalog = json.loads((PROCESSED / "catalog.json").read_text())
    catalog_by_id = {row["id"]: row for row in catalog}
    summaries = json.loads((FRONTEND_DATA / "summaries.json").read_text())
    for row in summaries:
        lake = catalog_by_id.get(row["id"], {})
        row["grid_cell_id"] = lake.get("grid_cell_id")
        row["nhd_fcode_desc"] = lake.get("nhd_fcode_desc")
        row["source"] = lake.get("source")
        row["elevation_source"] = lake.get("elevation_source")
        row["max_depth_m"] = lake.get("max_depth_m")
    (FRONTEND_DATA / "summaries.json").write_text(json.dumps(jsonable(summaries)))

    map_fc = json.loads((FRONTEND_DATA / "map.geojson").read_text())
    for feat in map_fc["features"]:
        lake = catalog_by_id.get(feat["properties"]["id"], {})
        feat["properties"]["grid_cell_id"] = lake.get("grid_cell_id")
    (FRONTEND_DATA / "map.geojson").write_text(json.dumps(jsonable(map_fc)))
    (PROCESSED / "map.geojson").write_text(json.dumps(jsonable(map_fc)))

    raw_weather = json.loads((PROCESSED / "weather_grid.json").read_text())
    if isinstance(raw_weather, dict) and "cells" in raw_weather:
        compact = raw_weather
    else:
        dates = raw_weather[0]["daily"]
        compact = {
            "source": raw_weather[0].get("source"),
            "retrieved_at": raw_weather[0].get("retrieved_at"),
            "dates": [d["date"] for d in dates],
            "is_forecast": [bool(d.get("is_forecast")) for d in dates],
            "cells": {},
        }
        for cell in raw_weather:
            daily = cell.get("daily") or []
            compact["cells"][cell["grid_cell_id"]] = {
                "latitude": cell.get("latitude"),
                "longitude": cell.get("longitude"),
                "elevation_m": cell.get("elevation_m"),
                "tmin_c": [d.get("tmin_c") for d in daily],
                "tmax_c": [d.get("tmax_c") for d in daily],
                "tmean_c": [d.get("tmean_c") for d in daily],
                "precipitation_mm": [d.get("precipitation_mm") for d in daily],
                "snowfall_cm": [d.get("snowfall_cm") for d in daily],
                "wind_speed_kmh": [d.get("wind_speed_kmh") for d in daily],
                "shortwave_mjm2": [d.get("shortwave_mjm2") for d in daily],
                "snow_depth_m": [d.get("snow_depth_m") for d in daily],
            }
    (FRONTEND_DATA / "weather_grid.json").write_text(json.dumps(jsonable(compact)))
    print("summaries", Path(FRONTEND_DATA / "summaries.json").stat().st_size)
    print("weather", Path(FRONTEND_DATA / "weather_grid.json").stat().st_size)
    print("map", Path(FRONTEND_DATA / "map.geojson").stat().st_size)


if __name__ == "__main__":
    main()
