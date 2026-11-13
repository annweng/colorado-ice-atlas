#!/usr/bin/env python3
"""Download Colorado NHD waterbodies, counties, and cities from public GIS services."""

from __future__ import annotations

import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

RAW = Path(__file__).resolve().parents[1] / "data" / "raw"
RAW.mkdir(parents=True, exist_ok=True)

LAYERS = [
    {
        "name": "co_nhd_waterbodies.geojson",
        "url": "https://gis.colorado.gov/public/rest/services/OIT/Colorado_State_Basemap/MapServer/48/query",
        "where": "FTYPE IN ('Lake/Pond','Reservoir','Playa')",
        "fields": "OBJECTID,COMID,GNIS_ID,GNIS_NAME,AREASQKM,ELEVATION,REACHCODE,FTYPE,FCODE,FCODEDesc,MeanDepth,LakeVolume,MaxDepth,LakeArea,FDATE",
    },
    {
        "name": "co_counties.geojson",
        "url": "https://gis.colorado.gov/public/rest/services/OIT/Colorado_State_Basemap/MapServer/52/query",
        "where": "1=1",
        "fields": "*",
    },
    {
        "name": "co_cities.geojson",
        "url": "https://gis.colorado.gov/public/rest/services/OIT/Colorado_State_Basemap/MapServer/73/query",
        "where": "1=1",
        "fields": "*",
    },
]


def fetch_layer(spec: dict) -> dict:
    features = []
    offset = 0
    page = 2000
    while True:
        params = {
            "where": spec["where"],
            "outFields": spec["fields"],
            "returnGeometry": "true",
            "outSR": "4326",
            "geometryPrecision": "5",
            "resultOffset": str(offset),
            "resultRecordCount": str(page),
            "f": "geojson",
        }
        url = spec["url"] + "?" + urllib.parse.urlencode(params)
        print(f"{spec['name']} offset={offset}", flush=True)
        with urllib.request.urlopen(url, timeout=180) as response:
            payload = json.load(response)
        batch = payload.get("features") or []
        features.extend(batch)
        if not batch or (not payload.get("exceededTransferLimit") and len(batch) < page):
            break
        offset += len(batch)
        time.sleep(0.25)
    return {"type": "FeatureCollection", "features": features}


def main() -> None:
    for spec in LAYERS:
        dest = RAW / spec["name"]
        if dest.exists() and dest.stat().st_size > 1000:
            print(f"keep {dest}")
            continue
        data = fetch_layer(spec)
        dest.write_text(json.dumps(data))
        print(f"wrote {dest} n={len(data['features'])}")


if __name__ == "__main__":
    main()
