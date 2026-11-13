"""File-backed catalog. PostGIS is used when DATABASE_URL is configured."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from app.core.config import settings


def _path(name: str) -> Path:
    path = settings.data_dir / name
    if path.exists():
        return path
    alt = settings.processed_dir / name
    if alt.exists():
        return alt
    return path


def _load(name: str) -> Any:
    path = _path(name)
    with path.open() as handle:
        return json.load(handle)


def _summary_to_catalog(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": row["id"],
        "official_name": row.get("official_name"),
        "display_name": row.get("name"),
        "lon": row["lon"],
        "lat": row["lat"],
        "county": row.get("county"),
        "elevation_m": row.get("elevation_m"),
        "elevation_source": row.get("elevation_source"),
        "surface_area_km2": row.get("area_km2"),
        "perimeter_km": row.get("perimeter_km"),
        "waterbody_type": row.get("type"),
        "nhd_fcode_desc": row.get("nhd_fcode_desc"),
        "depth_m": row.get("depth_m"),
        "max_depth_m": row.get("max_depth_m"),
        "source": row.get("source") or "Colorado OIT NHD Waterbodies (USGS NHDPlus)",
        "source_identifier": row.get("source_identifier"),
        "gnis_id": row.get("gnis_id"),
        "grid_cell_id": row.get("grid_cell_id"),
        "duplicate_flag": row.get("duplicate_flag"),
        "source_feature_date": row.get("source_feature_date"),
    }


@lru_cache(maxsize=1)
def summaries() -> list[dict[str, Any]]:
    return _load("summaries.json")


@lru_cache(maxsize=1)
def catalog() -> list[dict[str, Any]]:
    path = _path("catalog.json")
    if path.exists():
        return json.loads(path.read_text())
    return [_summary_to_catalog(row) for row in summaries()]


@lru_cache(maxsize=1)
def predictions() -> dict[str, dict[str, Any]]:
    path = _path("predictions.json")
    if path.exists():
        return {row["waterbody_id"]: row for row in json.loads(path.read_text())}
    out = {}
    meta = _load("meta.json")
    for row in summaries():
        out[row["id"]] = {
            "waterbody_id": row["id"],
            "prediction_timestamp": meta.get("generated_at"),
            "as_of_date": row.get("as_of"),
            "estimated_ice_coverage": row.get("coverage_pct"),
            "estimated_ice_thickness_cm": row.get("thickness_cm"),
            "lower_thickness_estimate_cm": row.get("thickness_lo_cm"),
            "upper_thickness_estimate_cm": row.get("thickness_hi_cm"),
            "ice_state": row.get("ice_state"),
            "confidence": row.get("confidence"),
            "model_version": meta.get("model_version"),
            "fdd_c_day": row.get("fdd"),
            "input_data_references": {},
            "methodology": "stefan_snow_v0.1",
        }
    return out


@lru_cache(maxsize=1)
def satellite() -> dict[str, dict[str, Any]]:
    path = _path("satellite.json")
    if not path.exists():
        return {
            row["id"]: {
                "waterbody_id": row["id"],
                "acquisition_timestamp": row.get("sat_at"),
                "classification": row.get("sat_class"),
                "source": "Sentinel-2 L2A (Planetary Computer STAC)",
            }
            for row in summaries()
            if row.get("sat_class")
        }
    return {row["waterbody_id"]: row for row in json.loads(path.read_text())}


@lru_cache(maxsize=1)
def weather_grid() -> dict[str, dict[str, Any]]:
    payload = _load("weather_grid.json")
    if isinstance(payload, dict) and "cells" in payload:
        expanded = {}
        dates = payload.get("dates") or []
        flags = payload.get("is_forecast") or [False] * len(dates)
        for cell_id, cell in (payload.get("cells") or {}).items():
            daily = []
            for i, date in enumerate(dates):
                daily.append(
                    {
                        "date": date,
                        "is_forecast": flags[i] if i < len(flags) else False,
                        "tmin_c": _at(cell.get("tmin_c"), i),
                        "tmax_c": _at(cell.get("tmax_c"), i),
                        "tmean_c": _at(cell.get("tmean_c"), i),
                        "precipitation_mm": _at(cell.get("precipitation_mm"), i),
                        "snowfall_cm": _at(cell.get("snowfall_cm"), i),
                        "wind_speed_kmh": _at(cell.get("wind_speed_kmh"), i),
                        "shortwave_mjm2": _at(cell.get("shortwave_mjm2"), i),
                        "snow_depth_m": _at(cell.get("snow_depth_m"), i),
                    }
                )
            expanded[cell_id] = {
                "grid_cell_id": cell_id,
                "latitude": cell.get("latitude"),
                "longitude": cell.get("longitude"),
                "elevation_m": cell.get("elevation_m"),
                "source": payload.get("source"),
                "retrieved_at": payload.get("retrieved_at"),
                "daily": daily,
            }
        return expanded
    return {row["grid_cell_id"]: row for row in payload}


def _at(column: list[Any] | None, index: int) -> Any:
    if not column or index >= len(column):
        return None
    return column[index]


@lru_cache(maxsize=1)
def counties() -> list[dict[str, Any]]:
    return _load("counties.json")


@lru_cache(maxsize=1)
def cities() -> list[dict[str, Any]]:
    return _load("cities.json")


@lru_cache(maxsize=1)
def provenance() -> dict[str, Any]:
    return _load("provenance.json")


@lru_cache(maxsize=1)
def model_run() -> dict[str, Any]:
    return _load("model_run.json")


@lru_cache(maxsize=1)
def meta() -> dict[str, Any]:
    return _load("meta.json")


def by_id() -> dict[str, dict[str, Any]]:
    return {row["id"]: row for row in catalog()}


def data_paths() -> dict[str, str]:
    return {
        "data_dir": str(settings.data_dir),
        "processed_dir": str(settings.processed_dir),
        "map_geojson": str(Path(settings.data_dir) / "map.geojson"),
    }
