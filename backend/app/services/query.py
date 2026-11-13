from __future__ import annotations

import math
import re
from typing import Any

from app.services import store

COORD_RE = re.compile(r"^\s*(-?\d+(?:\.\d+)?)\s*[, ]\s*(-?\d+(?:\.\d+)?)\s*$")


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def parse_coordinates(query: str) -> tuple[float, float] | None:
    match = COORD_RE.match(query.strip())
    if not match:
        return None
    a, b = float(match.group(1)), float(match.group(2))
    # lon, lat (Colorado longitudes are west of -90)
    if -180 <= a <= -90 and 31 <= b <= 50:
        return b, a
    # lat, lon
    if 31 <= a <= 50 and -180 <= b <= -90:
        return a, b
    if -90 <= a <= 90 and -180 <= b <= 180:
        return a, b
    return None


def search(query: str, limit: int = 20) -> list[dict[str, Any]]:
    q = query.strip()
    if not q:
        return []
    coords = parse_coordinates(q)
    summaries = store.summaries()
    if coords:
        lat, lon = coords
        ranked = sorted(summaries, key=lambda row: _haversine_km(lat, lon, row["lat"], row["lon"]))
        out = []
        for row in ranked[:limit]:
            item = dict(row)
            item["distance_km"] = round(_haversine_km(lat, lon, row["lat"], row["lon"]), 2)
            out.append(item)
        return out

    needle = q.lower()
    city_hit = next((c for c in store.cities() if needle in str(c["name"]).lower()), None)
    scored: list[tuple[float, dict[str, Any]]] = []
    for row in summaries:
        name = (row.get("name") or "").lower()
        official = (row.get("official_name") or "").lower()
        county = (row.get("county") or "").lower()
        tokens = set(official.replace("/", " ").replace("-", " ").split()) | set(name.replace("/", " ").split())
        score = 0.0
        if needle == official or needle == name:
            score = 100
        elif needle in tokens:
            score = 88
        elif official.startswith(needle) or name.startswith(needle):
            score = 70
        elif needle in official or needle in name:
            score = 55
        elif needle in county:
            score = 40
        elif row.get("id", "").lower() == needle:
            score = 90
        if score:
            score += min(25.0, (row.get("area_km2") or 0) * 2)
            scored.append((score, row))
    scored.sort(key=lambda item: (-item[0], -(item[1].get("area_km2") or 0)))
    results = [row for _, row in scored[:limit]]
    if city_hit and len(results) < limit:
        nearby = sorted(
            summaries,
            key=lambda row: _haversine_km(city_hit["lat"], city_hit["lon"], row["lat"], row["lon"]),
        )
        seen = {r["id"] for r in results}
        for row in nearby:
            if row["id"] in seen:
                continue
            item = dict(row)
            item["distance_km"] = round(_haversine_km(city_hit["lat"], city_hit["lon"], row["lat"], row["lon"]), 2)
            item["near"] = city_hit["name"]
            results.append(item)
            if len(results) >= limit:
                break
    return results


def apply_filters(
    rows: list[dict[str, Any]],
    *,
    q: str | None = None,
    county: str | None = None,
    waterbody_type: str | None = None,
    ice_state: str | None = None,
    confidence: str | None = None,
    named_only: bool = False,
    min_elevation: float | None = None,
    max_elevation: float | None = None,
    min_area: float | None = None,
    max_area: float | None = None,
    min_coverage: float | None = None,
    max_coverage: float | None = None,
    min_thickness: float | None = None,
    max_thickness: float | None = None,
    bbox: tuple[float, float, float, float] | None = None,
    has_satellite: bool | None = None,
) -> list[dict[str, Any]]:
    out = rows
    if q:
        ids = {item["id"] for item in search(q, limit=500)}
        out = [row for row in out if row["id"] in ids]
    if county:
        counties = {part.strip().lower() for part in county.split(",") if part.strip()}
        out = [row for row in out if (row.get("county") or "").lower() in counties]
    if waterbody_type:
        types = {part.strip() for part in waterbody_type.split(",") if part.strip()}
        out = [row for row in out if row.get("type") in types]
    if ice_state:
        states = {part.strip() for part in ice_state.split(",") if part.strip()}
        out = [row for row in out if row.get("ice_state") in states]
    if confidence:
        confs = {part.strip() for part in confidence.split(",") if part.strip()}
        out = [row for row in out if row.get("confidence") in confs]
    if named_only:
        out = [row for row in out if row.get("named") or row.get("official_name")]
    if min_elevation is not None:
        out = [row for row in out if row.get("elevation_m") is not None and row["elevation_m"] >= min_elevation]
    if max_elevation is not None:
        out = [row for row in out if row.get("elevation_m") is not None and row["elevation_m"] <= max_elevation]
    if min_area is not None:
        out = [row for row in out if (row.get("area_km2") or 0) >= min_area]
    if max_area is not None:
        out = [row for row in out if (row.get("area_km2") or 0) <= max_area]
    if min_coverage is not None:
        out = [row for row in out if row.get("coverage_pct") is not None and row["coverage_pct"] >= min_coverage]
    if max_coverage is not None:
        out = [row for row in out if row.get("coverage_pct") is not None and row["coverage_pct"] <= max_coverage]
    if min_thickness is not None:
        out = [row for row in out if row.get("thickness_cm") is not None and row["thickness_cm"] >= min_thickness]
    if max_thickness is not None:
        out = [row for row in out if row.get("thickness_cm") is not None and row["thickness_cm"] <= max_thickness]
    if bbox:
        minx, miny, maxx, maxy = bbox
        out = [row for row in out if minx <= row["lon"] <= maxx and miny <= row["lat"] <= maxy]
    if has_satellite is True:
        sat = store.satellite()
        out = [row for row in out if row["id"] in sat]
    if has_satellite is False:
        sat = store.satellite()
        out = [row for row in out if row["id"] not in sat]
    return out


def paginate(rows: list[dict[str, Any]], limit: int, offset: int) -> dict[str, Any]:
    limit = max(1, min(limit, 500))
    offset = max(0, offset)
    return {
        "total": len(rows),
        "limit": limit,
        "offset": offset,
        "items": rows[offset : offset + limit],
    }
