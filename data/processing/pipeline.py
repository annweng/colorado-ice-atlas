"""End-to-end daily pipeline: inventory, weather, satellite, ice estimates."""

from __future__ import annotations

import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from data.ingestion.elevation_ned import sample_elevations
from data.ingestion.satellite_stac import assign_scenes_to_lakes, search_recent_scenes
from data.ingestion.weather_openmeteo import cell_id, fetch_grid_weather, unique_cells
from data.processing.aliases import apply_alias, load_aliases
from data.processing.inventory import (
    attach_counties,
    colorado_outline,
    compute_metrics,
    detect_duplicates,
    load_cities,
    load_counties,
    load_waterbodies,
    to_records,
)
from modeling.ice_models.stefan import MODEL_VERSION, LakeParams, estimate_depth_m, simulate_season

RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"
FRONTEND_DATA = ROOT / "frontend" / "public" / "data"


def _geom_bbox(geom: dict[str, Any] | None) -> list[float] | None:
    if not geom:
        return None
    rings: list[list[float]] = []

    def walk(node: Any) -> None:
        if not isinstance(node, list) or not node:
            return
        if isinstance(node[0], (int, float)) and len(node) >= 2:
            rings.append([float(node[0]), float(node[1])])
            return
        for child in node:
            walk(child)

    walk(geom.get("coordinates"))
    if not rings:
        return None
    xs = [p[0] for p in rings]
    ys = [p[1] for p in rings]
    return [min(xs), min(ys), max(xs), max(ys)]


def jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [jsonable(v) for v in value]
    if isinstance(value, np.bool_):
        return bool(value)
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.floating):
        return None if not np.isfinite(value) else float(value)
    if isinstance(value, float):
        return None if not math.isfinite(value) else value
    try:
        if value is pd.NA or pd.isna(value):
            return None
    except Exception:
        pass
    return value


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(jsonable(payload), allow_nan=False), encoding="utf-8")


def build_inventory(skip_elevation: bool = False) -> dict[str, Any]:
    retrieved_at = datetime.now(timezone.utc).isoformat()
    lakes = load_waterbodies(RAW / "co_nhd_waterbodies.geojson")
    counties = load_counties(RAW / "co_counties.geojson")
    cities = load_cities(RAW / "co_cities.geojson")
    lakes = compute_metrics(lakes)
    lakes = attach_counties(lakes, counties)
    lakes["duplicate_flag"] = detect_duplicates(lakes)

    if skip_elevation:
        lakes["elevation_dem_m"] = pd.NA
        elev_prov = {"skipped": True}
    else:
        elevations, elev_prov = sample_elevations(lakes["lat"].tolist(), lakes["lon"].tolist())
        lakes["elevation_dem_m"] = elevations

    records = to_records(lakes, retrieved_at)
    outline = colorado_outline(counties)
    city_records = [
        {
            "name": row["name"],
            "lon": float(row["lon"]),
            "lat": float(row["lat"]),
        }
        for _, row in cities.iterrows()
        if pd.notna(row.get("name"))
    ]
    county_records = (
        counties.drop(columns="geometry")
        .drop_duplicates(subset=["county_fips"])
        .to_dict(orient="records")
    )
    return {
        "waterbodies": records,
        "counties": county_records,
        "cities": city_records,
        "outline": outline,
        "elevation_provenance": elev_prov,
        "inventory_provenance": {
            "source": "Colorado OIT NHD Waterbodies layer (USGS NHDPlus)",
            "source_url": "https://gis.colorado.gov/public/rest/services/OIT/Colorado_State_Basemap/MapServer/48",
            "counties_source": "Colorado Census Counties (US Census TIGER via Colorado OIT GIS)",
            "cities_source": "Colorado Cities (Colorado OIT GIS)",
            "retrieval_timestamp": retrieved_at,
            "processing_timestamp": datetime.now(timezone.utc).isoformat(),
            "crs": "EPSG:4326",
            "area_crs": "EPSG:5070",
            "feature_count": len(records),
            "named_count": sum(1 for r in records if r["official_name"]),
            "with_depth": sum(1 for r in records if r["depth_m"] is not None),
            "license": "USGS-authored NHD is public domain. Colorado GIS services attribution required.",
        },
    }


def run_models(inventory: dict[str, Any]) -> dict[str, Any]:
    lakes = inventory["waterbodies"]
    cells = unique_cells([wb["lat"] for wb in lakes], [wb["lon"] for wb in lakes])
    weather, weather_prov = fetch_grid_weather(cells)
    weather_by_cell = {item["grid_cell_id"]: item for item in weather}

    scenes, sat_prov = search_recent_scenes()
    satellite_obs = assign_scenes_to_lakes(lakes, scenes)

    generated_at = datetime.now(timezone.utc).isoformat()
    predictions = []
    timeseries_by_id: dict[str, list[dict[str, Any]]] = {}
    weather_by_id: dict[str, dict[str, Any]] = {}
    stale = False

    for lake in lakes:
        cid = cell_id(lake["lat"], lake["lon"])
        lake["grid_cell_id"] = cid
        cell = weather_by_cell.get(cid)
        depth = lake["depth_m"]
        depth_estimated = depth is None
        params = LakeParams(
            area_km2=lake["surface_area_km2"],
            depth_m=depth if depth is not None else estimate_depth_m(lake["surface_area_km2"]),
            elevation_m=lake["elevation_m"],
            waterbody_type=lake["waterbody_type"],
            fcode_desc=lake["nhd_fcode_desc"],
            depth_is_estimated=depth_estimated,
        )
        if not cell or not cell.get("daily"):
            stale = True
            predictions.append(_unavailable_prediction(lake, generated_at, "No weather grid cell retrieved."))
            continue
        daily = cell["daily"]
        series = simulate_season(
            dates=[d["date"] for d in daily],
            tmean_c=[d["tmean_c"] for d in daily],
            tmin_c=[d["tmin_c"] for d in daily],
            tmax_c=[d["tmax_c"] for d in daily],
            snow_depth_m=[d["snow_depth_m"] for d in daily],
            snowfall_cm=[d["snowfall_cm"] for d in daily],
            wind_speed_kmh=[d["wind_speed_kmh"] for d in daily],
            precipitation_mm=[d["precipitation_mm"] for d in daily],
            shortwave_mjm2=[d["shortwave_mjm2"] for d in daily],
            is_forecast=[d["is_forecast"] for d in daily],
            params=params,
        )
        observed = [row for row in series if not row.is_forecast]
        current = observed[-1] if observed else series[-1]
        sat = next((s for s in satellite_obs if s["waterbody_id"] == lake["id"]), None)
        predictions.append(
            {
                "waterbody_id": lake["id"],
                "prediction_timestamp": generated_at,
                "as_of_date": current.date,
                "estimated_ice_coverage": current.estimated_ice_coverage_pct,
                "estimated_ice_thickness_cm": current.estimated_ice_thickness_cm,
                "lower_thickness_estimate_cm": current.lower_thickness_cm,
                "upper_thickness_estimate_cm": current.upper_thickness_cm,
                "ice_state": current.ice_state,
                "confidence": current.confidence,
                "data_quality": _data_quality(lake, current, cell),
                "model_version": MODEL_VERSION,
                "fdd_c_day": current.fdd_c_day,
                "tdd_c_day": current.tdd_c_day,
                "ice_on": current.ice_on,
                "is_forecast": current.is_forecast,
                "is_stale": False,
                "notes": current.notes,
                "input_data_references": {
                    "weather_source": cell.get("source"),
                    "weather_retrieved_at": cell.get("retrieved_at"),
                    "grid_cell_id": cid,
                    "elevation_source": lake.get("elevation_source"),
                    "depth_source": "NHDPlus MeanDepth" if not depth_estimated else "area-depth heuristic",
                    "satellite_scene_id": None if sat is None else sat.get("scene_id"),
                    "satellite_classification": None if sat is None else sat.get("classification"),
                },
                "methodology": (
                    "Accumulated freezing degree days from daily mean air temperature, "
                    "Stefan-type thickness after a morphometry-dependent freeze-over "
                    "threshold, with snow-depth insulation. Model estimate, not a measurement."
                ),
            }
        )
        timeseries_by_id[lake["id"]] = [
            {
                "date": row.date,
                "is_forecast": row.is_forecast,
                "tmin_c": row.tmin_c,
                "tmax_c": row.tmax_c,
                "tmean_c": row.tmean_c,
                "snow_depth_m": row.snow_depth_m,
                "snowfall_cm": row.snowfall_cm,
                "wind_speed_kmh": row.wind_speed_kmh,
                "precipitation_mm": row.precipitation_mm,
                "shortwave_mjm2": row.shortwave_mjm2,
                "fdd_c_day": row.fdd_c_day,
                "tdd_c_day": row.tdd_c_day,
                "estimated_ice_coverage": row.estimated_ice_coverage_pct,
                "estimated_ice_thickness_cm": row.estimated_ice_thickness_cm,
                "lower_thickness_cm": row.lower_thickness_cm,
                "upper_thickness_cm": row.upper_thickness_cm,
                "ice_state": row.ice_state,
                "confidence": row.confidence,
            }
            for row in series
        ]
        weather_by_id[lake["id"]] = {
            "grid_cell_id": cid,
            "source": cell.get("source"),
            "retrieved_at": cell.get("retrieved_at"),
            "grid_latitude": cell.get("latitude"),
            "grid_longitude": cell.get("longitude"),
            "grid_elevation_m": cell.get("elevation_m"),
        }

    model_run = {
        "id": f"run-{generated_at}",
        "model_version": MODEL_VERSION,
        "execution_timestamp": generated_at,
        "ingestion_status": "partial" if weather_prov.get("errors") else "ok",
        "processing_status": "ok",
        "waterbodies": len(lakes),
        "predictions": len(predictions),
        "weather_cells": weather_prov.get("cells_ok"),
        "satellite_scenes": sat_prov.get("scenes"),
        "satellite_assignments": len(satellite_obs),
        "error_details": weather_prov.get("errors") or sat_prov.get("error"),
        "stale": stale,
    }
    return {
        "predictions": predictions,
        "timeseries_by_id": timeseries_by_id,
        "weather_by_id": weather_by_id,
        "weather_grid": weather,
        "satellite_observations": satellite_obs,
        "weather_provenance": weather_prov,
        "satellite_provenance": sat_prov,
        "model_run": model_run,
    }


def _unavailable_prediction(lake: dict[str, Any], generated_at: str, reason: str) -> dict[str, Any]:
    return {
        "waterbody_id": lake["id"],
        "prediction_timestamp": generated_at,
        "as_of_date": None,
        "estimated_ice_coverage": None,
        "estimated_ice_thickness_cm": None,
        "lower_thickness_estimate_cm": None,
        "upper_thickness_estimate_cm": None,
        "ice_state": "unknown",
        "confidence": "unavailable",
        "data_quality": "weather_missing",
        "model_version": MODEL_VERSION,
        "fdd_c_day": None,
        "tdd_c_day": None,
        "ice_on": False,
        "is_forecast": False,
        "is_stale": True,
        "notes": [reason],
        "input_data_references": {},
        "methodology": "Estimate withheld because required weather inputs were missing.",
    }


def _data_quality(lake: dict[str, Any], current: Any, cell: dict[str, Any]) -> str:
    bits = []
    if lake["depth_m"] is None:
        bits.append("depth_estimated")
    if lake["elevation_m"] is None:
        bits.append("elevation_missing")
    if not lake["official_name"]:
        bits.append("unnamed")
    missing_weather = sum(1 for d in cell.get("daily") or [] if d.get("tmean_c") is None)
    if missing_weather:
        bits.append("incomplete_weather")
    if current.confidence == "unavailable":
        bits.append("insufficient")
    return ",".join(bits) or "ok"


def export_snapshots(inventory: dict[str, Any], modeled: dict[str, Any]) -> None:
    PROCESSED.mkdir(parents=True, exist_ok=True)
    FRONTEND_DATA.mkdir(parents=True, exist_ok=True)
    pred_by_id = {p["waterbody_id"]: p for p in modeled["predictions"]}
    sat_by_id = {s["waterbody_id"]: s for s in modeled["satellite_observations"]}

    aliases = load_aliases()
    map_features = []
    summaries = []
    for lake in inventory["waterbodies"]:
        lake = apply_alias(dict(lake), aliases)
        pred = pred_by_id.get(lake["id"], {})
        sat = sat_by_id.get(lake["id"])
        geom = lake.get("geometry_simplified") or lake.get("geometry")
        bbox = _geom_bbox(geom)
        props = {
            "id": lake["id"],
            "name": lake["display_name"],
            "official_name": lake["official_name"],
            "county": lake["county"],
            "lat": round(lake["lat"], 5),
            "lon": round(lake["lon"], 5),
            "elevation_m": None if lake["elevation_m"] is None else round(lake["elevation_m"]),
            "area_km2": lake["surface_area_km2"],
            "perimeter_km": lake["perimeter_km"],
            "type": lake["waterbody_type"],
            "depth_m": lake["depth_m"],
            "ice_state": pred.get("ice_state", "unknown"),
            "coverage_pct": pred.get("estimated_ice_coverage"),
            "thickness_cm": pred.get("estimated_ice_thickness_cm"),
            "thickness_lo_cm": pred.get("lower_thickness_estimate_cm"),
            "thickness_hi_cm": pred.get("upper_thickness_estimate_cm"),
            "confidence": pred.get("confidence", "unavailable"),
            "fdd": pred.get("fdd_c_day"),
            "as_of": pred.get("as_of_date"),
            "sat_class": None if sat is None else sat.get("classification"),
            "sat_at": None if sat is None else (sat.get("acquisition_timestamp") or "")[:10],
            "named": bool(lake["official_name"]) or bool(lake.get("display_name") and lake.get("name_source")),
            "alternative_names": lake.get("alternative_names") or [],
            "name_source": lake.get("name_source"),
            "bbox": bbox,
            "grid_cell_id": lake.get("grid_cell_id"),
            "nhd_fcode_desc": lake.get("nhd_fcode_desc"),
            "source": lake.get("source"),
            "elevation_source": lake.get("elevation_source"),
            "max_depth_m": lake.get("max_depth_m"),
        }
        map_features.append({"type": "Feature", "id": lake["id"], "geometry": lake["geometry_simplified"], "properties": props})
        summaries.append({**props, "gnis_id": lake["gnis_id"], "source_identifier": lake["source_identifier"]})

    map_fc = {
        "type": "FeatureCollection",
        "name": "colorado_ice_atlas_waterbodies",
        "features": map_features,
    }
    _write_json(PROCESSED / "map.geojson", map_fc)
    _write_json(FRONTEND_DATA / "map.geojson", map_fc)
    _write_json(FRONTEND_DATA / "outline.geojson", {"type": "FeatureCollection", "features": [{"type": "Feature", "properties": {"name": "Colorado"}, "geometry": inventory["outline"]}]})
    _write_json(FRONTEND_DATA / "cities.json", inventory["cities"])
    _write_json(FRONTEND_DATA / "counties.json", inventory["counties"])
    _write_json(FRONTEND_DATA / "predictions.json", modeled["predictions"])
    _write_json(PROCESSED / "predictions.json", modeled["predictions"])
    _write_json(FRONTEND_DATA / "summaries.json", summaries)
    _write_json(FRONTEND_DATA / "satellite.json", modeled["satellite_observations"])
    _write_json(FRONTEND_DATA / "model_run.json", modeled["model_run"])

    weather_grid = []
    compact_cells = {}
    dates = []
    forecast_flags = []
    source = None
    retrieved_at = None
    for cell in modeled["weather_grid"]:
        daily = cell.get("daily") or []
        if not dates and daily:
            dates = [d["date"] for d in daily]
            forecast_flags = [bool(d.get("is_forecast")) for d in daily]
        source = source or cell.get("source")
        retrieved_at = retrieved_at or cell.get("retrieved_at")
        weather_grid.append(
            {
                "grid_cell_id": cell["grid_cell_id"],
                "latitude": cell.get("latitude"),
                "longitude": cell.get("longitude"),
                "elevation_m": cell.get("elevation_m"),
                "source": cell.get("source"),
                "retrieved_at": cell.get("retrieved_at"),
                "daily": daily,
            }
        )
        compact_cells[cell["grid_cell_id"]] = {
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
    compact = {
        "source": source,
        "retrieved_at": retrieved_at,
        "dates": dates,
        "is_forecast": forecast_flags,
        "cells": compact_cells,
    }
    _write_json(PROCESSED / "weather_grid.json", weather_grid)
    _write_json(FRONTEND_DATA / "weather_grid.json", compact)

    catalog = []
    for lake in inventory["waterbodies"]:
        catalog.append({k: v for k, v in lake.items() if k not in {"geometry", "geometry_simplified"}})
    pd.DataFrame(catalog).to_parquet(PROCESSED / "waterbodies.parquet", index=False)
    pd.DataFrame(modeled["predictions"]).to_parquet(PROCESSED / "predictions.parquet", index=False)
    _write_json(PROCESSED / "catalog.json", catalog)
    _write_json(FRONTEND_DATA / "catalog.json", catalog)

    provenance = {
        "inventory": inventory["inventory_provenance"],
        "elevation": inventory["elevation_provenance"],
        "weather": modeled["weather_provenance"],
        "satellite": modeled["satellite_provenance"],
        "model_run": modeled["model_run"],
        "exported_at": datetime.now(timezone.utc).isoformat(),
    }
    _write_json(PROCESSED / "provenance.json", provenance)
    _write_json(FRONTEND_DATA / "provenance.json", provenance)
    _write_json(
        FRONTEND_DATA / "meta.json",
        {
            "title": "Colorado Ice Atlas",
            "tagline": "Explore. Observe. Forecast.",
            "waterbodies": len(inventory["waterbodies"]),
            "named": inventory["inventory_provenance"]["named_count"],
            "model_version": MODEL_VERSION,
            "generated_at": modeled["model_run"]["execution_timestamp"],
            "as_of": next((p.get("as_of_date") for p in modeled["predictions"] if p.get("as_of_date")), None),
        },
    )


def run(skip_elevation: bool = False) -> dict[str, Any]:
    inventory = build_inventory(skip_elevation=skip_elevation)
    modeled = run_models(inventory)
    export_snapshots(inventory, modeled)
    return modeled["model_run"]


if __name__ == "__main__":
    result = run(skip_elevation="--skip-elevation" in sys.argv)
    print(json.dumps(result, indent=2))
