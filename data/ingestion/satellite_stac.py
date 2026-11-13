"""Sentinel-2 scene discovery via the Microsoft Planetary Computer STAC API.

Pixel-level ice classification is optional and expensive. The operational
pipeline records the most recent low-cloud scene intersecting each lake
bounding box. Scene metadata is an observation of imagery availability and
cloud conditions, not ice thickness.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from data.ingestion.http import json_post

STAC_SEARCH = "https://planetarycomputer.microsoft.com/api/stac/v1/search"
COLORADO_BBOX = [-109.06, 36.99, -102.04, 41.01]


def search_recent_scenes(days: int = 14, cloud_lt: float = 40.0, limit: int = 40) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=days)
    payload = {
        "collections": ["sentinel-2-l2a"],
        "bbox": COLORADO_BBOX,
        "datetime": f"{start.date().isoformat()}/{end.date().isoformat()}",
        "limit": limit,
        "query": {"eo:cloud_cover": {"lt": cloud_lt}},
        "sortby": [{"field": "properties.datetime", "direction": "desc"}],
    }
    provenance = {
        "source": "Microsoft Planetary Computer STAC",
        "source_url": STAC_SEARCH,
        "collection": "sentinel-2-l2a",
        "retrieval_timestamp": end.isoformat(),
        "query_window_days": days,
        "cloud_cover_lt": cloud_lt,
        "bbox": COLORADO_BBOX,
        "methodology": (
            "STAC search for Sentinel-2 L2A scenes over Colorado. Results are scene "
            "footprints and cloud metadata. No raw imagery is downloaded. Surface ice "
            "percent is not inferred from scene presence."
        ),
        "error": None,
    }
    try:
        body = json_post(STAC_SEARCH, payload, timeout=60)
    except Exception as exc:
        provenance["error"] = str(exc)
        provenance["processing_timestamp"] = datetime.now(timezone.utc).isoformat()
        return [], provenance

    scenes = []
    for feature in body.get("features") or []:
        props = feature.get("properties") or {}
        geom = feature.get("geometry") or {}
        scenes.append(
            {
                "scene_id": feature.get("id"),
                "acquired_at": props.get("datetime"),
                "cloud_cover": props.get("eo:cloud_cover"),
                "platform": props.get("platform"),
                "mgrs_tile": props.get("s2:mgrs_tile") or props.get("mgrs:utm_zone"),
                "bbox": feature.get("bbox"),
                "geometry": geom,
                "source": "sentinel-2-l2a",
            }
        )
    provenance["scenes"] = len(scenes)
    provenance["processing_timestamp"] = datetime.now(timezone.utc).isoformat()
    return scenes, provenance


def scene_intersects_point(scene: dict[str, Any], lon: float, lat: float) -> bool:
    bbox = scene.get("bbox")
    if not bbox or len(bbox) < 4:
        return False
    minx, miny, maxx, maxy = bbox[:4]
    return minx <= lon <= maxx and miny <= lat <= maxy


def assign_scenes_to_lakes(
    lakes: list[dict[str, Any]],
    scenes: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Attach the newest intersecting scene to each lake. No ice % is invented."""
    observations = []
    for lake in lakes:
        lon = lake["lon"]
        lat = lake["lat"]
        match = next((s for s in scenes if scene_intersects_point(s, lon, lat)), None)
        if not match:
            continue
        observations.append(
            {
                "waterbody_id": lake["id"],
                "acquisition_timestamp": match["acquired_at"],
                "ice_coverage_percentage": None,
                "classification": "scene_available_uncclassified",
                "cloud_coverage": match.get("cloud_cover"),
                "source": "Sentinel-2 L2A (Planetary Computer STAC)",
                "scene_id": match.get("scene_id"),
                "quality_metadata": {
                    "note": (
                        "A Sentinel-2 scene intersects this lake, but surface ice was not "
                        "classified at pixel level in this pipeline run. Scene presence is "
                        "not evidence of ice thickness."
                    ),
                    "bbox": match.get("bbox"),
                },
            }
        )
    return observations
