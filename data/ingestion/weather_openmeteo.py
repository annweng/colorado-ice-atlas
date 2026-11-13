"""Gridded weather from Open-Meteo (ERA5-Land / operational forecast blend).

Lakes are assigned to a regular grid rather than the nearest surface station.
Open-Meteo interpolates public reanalysis and forecast models to the cell
center. This is more appropriate than sparse COOP/ASOS stations in the alpine.

Free-tier note: no API key. Attribution required (Open-Meteo, Copernicus ERA5).
"""

from __future__ import annotations

import math
from datetime import date, datetime, timedelta, timezone
from typing import Any

from data.ingestion.http import json_get

FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"
GRID_STEP_DEG = 0.25
BATCH_LOCATIONS = 12
PAST_DAYS = 92
FORECAST_DAYS = 7

DAILY_VARS = [
    "temperature_2m_max",
    "temperature_2m_min",
    "temperature_2m_mean",
    "precipitation_sum",
    "snowfall_sum",
    "wind_speed_10m_max",
    "shortwave_radiation_sum",
]


def cell_center(lat: float, lon: float, step: float = GRID_STEP_DEG) -> tuple[float, float]:
    lat_c = math.floor(lat / step) * step + step / 2
    lon_c = math.floor(lon / step) * step + step / 2
    return round(lat_c, 4), round(lon_c, 4)


def cell_id(lat: float, lon: float, step: float = GRID_STEP_DEG) -> str:
    lat_c, lon_c = cell_center(lat, lon, step)
    return f"g:{lat_c:.3f}:{lon_c:.3f}"


def unique_cells(latitudes: list[float], longitudes: list[float]) -> list[dict[str, float | str]]:
    cells: dict[str, dict[str, float | str]] = {}
    for lat, lon in zip(latitudes, longitudes):
        cid = cell_id(lat, lon)
        if cid not in cells:
            clat, clon = cell_center(lat, lon)
            cells[cid] = {"grid_cell_id": cid, "latitude": clat, "longitude": clon}
    return list(cells.values())


def _normalize_location(payload: dict[str, Any], lat: float, lon: float, retrieved_at: str) -> dict[str, Any]:
    daily = payload.get("daily") or {}
    times = daily.get("time") or []
    today = date.today().isoformat()
    rows = []
    for i, day in enumerate(times):
        rows.append(
            {
                "date": day,
                "is_forecast": day > today,
                "tmin_c": _at(daily.get("temperature_2m_min"), i),
                "tmax_c": _at(daily.get("temperature_2m_max"), i),
                "tmean_c": _at(daily.get("temperature_2m_mean"), i),
                "precipitation_mm": _at(daily.get("precipitation_sum"), i),
                "snowfall_cm": _at(daily.get("snowfall_sum"), i),
                "wind_speed_kmh": _at(daily.get("wind_speed_10m_max"), i),
                "shortwave_mjm2": _at(daily.get("shortwave_radiation_sum"), i),
                "snow_depth_m": None,
            }
        )
    hourly = payload.get("hourly") or {}
    h_times = hourly.get("time") or []
    h_snow = hourly.get("snow_depth") or []
    by_day: dict[str, list[float]] = {}
    for stamp, depth in zip(h_times, h_snow):
        if depth is None:
            continue
        day = stamp[:10]
        by_day.setdefault(day, []).append(float(depth))
    for row in rows:
        values = by_day.get(row["date"])
        if values:
            row["snow_depth_m"] = sum(values) / len(values)

    return {
        "latitude": payload.get("latitude", lat),
        "longitude": payload.get("longitude", lon),
        "elevation_m": payload.get("elevation"),
        "timezone": payload.get("timezone"),
        "utc_offset_seconds": payload.get("utc_offset_seconds"),
        "retrieved_at": retrieved_at,
        "source": "Open-Meteo Forecast API (past_days + forecast; GFS/ECMWF blend, ERA5 where applicable)",
        "daily": rows,
    }


def _at(column: list[Any] | None, index: int) -> float | None:
    if not column or index >= len(column):
        return None
    value = column[index]
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def fetch_forecast_batch(locations: list[tuple[float, float]]) -> list[dict[str, Any]]:
    if not locations:
        return []
    lats = ",".join(f"{lat:.4f}" for lat, _ in locations)
    lons = ",".join(f"{lon:.4f}" for _, lon in locations)
    params = {
        "latitude": lats,
        "longitude": lons,
        "daily": ",".join(DAILY_VARS),
        "hourly": "snow_depth",
        "past_days": PAST_DAYS,
        "forecast_days": FORECAST_DAYS,
        "timezone": "America/Denver",
        "wind_speed_unit": "kmh",
        "precipitation_unit": "mm",
    }
    retrieved_at = datetime.now(timezone.utc).isoformat()
    payload = json_get(FORECAST_URL, params=params, timeout=90)
    if isinstance(payload, dict) and "daily" in payload:
        lat, lon = locations[0]
        return [_normalize_location(payload, lat, lon, retrieved_at)]
    out = []
    for item, (lat, lon) in zip(payload, locations):
        if isinstance(item, dict) and item.get("error"):
            continue
        out.append(_normalize_location(item, lat, lon, retrieved_at))
    return out


def fetch_grid_weather(cells: list[dict[str, float | str]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    weather: list[dict[str, Any]] = []
    errors: list[str] = []
    for start in range(0, len(cells), BATCH_LOCATIONS):
        chunk = cells[start : start + BATCH_LOCATIONS]
        locs = [(float(c["latitude"]), float(c["longitude"])) for c in chunk]
        try:
            results = fetch_forecast_batch(locs)
            for cell, result in zip(chunk, results):
                result["grid_cell_id"] = cell["grid_cell_id"]
                weather.append(result)
            if len(results) < len(chunk):
                errors.append(f"partial batch starting {chunk[0]['grid_cell_id']}")
        except Exception as exc:
            errors.append(f"{chunk[0]['grid_cell_id']}: {exc}")
    provenance = {
        "source": "Open-Meteo",
        "source_url": FORECAST_URL,
        "retrieval_timestamp": datetime.now(timezone.utc).isoformat(),
        "past_days": PAST_DAYS,
        "forecast_days": FORECAST_DAYS,
        "grid_step_deg": GRID_STEP_DEG,
        "cells_requested": len(cells),
        "cells_ok": len(weather),
        "errors": errors,
        "units": {
            "temperature": "°C",
            "precipitation": "mm",
            "snowfall": "cm",
            "snow_depth": "m",
            "wind_speed": "km/h",
            "shortwave_radiation": "MJ/m²",
        },
        "methodology": (
            "Each waterbody is assigned to the 0.25° grid cell containing its centroid. "
            "Weather is retrieved once per cell from Open-Meteo, which downscales public "
            "forecast/reanalysis models. This is gridded meteorology, not a station observation."
        ),
        "attribution": "Weather data by Open-Meteo.com. Contains modified Copernicus Climate Change Service information where ERA5 is used.",
    }
    return weather, provenance


def fetch_archive_range(lat: float, lon: float, start: date, end: date) -> dict[str, Any]:
    params = {
        "latitude": f"{lat:.4f}",
        "longitude": f"{lon:.4f}",
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
        "daily": ",".join(DAILY_VARS),
        "timezone": "America/Denver",
        "wind_speed_unit": "kmh",
    }
    retrieved_at = datetime.now(timezone.utc).isoformat()
    payload = json_get(ARCHIVE_URL, params=params, timeout=90)
    return _normalize_location(payload, lat, lon, retrieved_at)


def previous_winter_window(today: date | None = None) -> tuple[date, date]:
    today = today or date.today()
    year = today.year if today.month >= 8 else today.year - 1
    return date(year - 1, 10, 1), date(year, 5, 31)


def default_season_start(today: date | None = None) -> date:
    today = today or date.today()
    return today - timedelta(days=PAST_DAYS)
