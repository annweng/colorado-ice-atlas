"""Sample USGS 3DEP / NED 10 m elevation at lake centroids via OpenTopoData.

OpenTopoData is a convenience API over public USGS NED tiles. Elevations are
measurements of the DEM at the centroid, not surveyed lake-surface elevations.
"""

from __future__ import annotations

import time
from datetime import datetime, timezone

from data.ingestion.http import json_get

NED_URL = "https://api.opentopodata.org/v1/ned10m"
ASTER_FALLBACK_URL = "https://api.opentopodata.org/v1/aster30m"
BATCH = 100


def sample_elevations(lats: list[float], lons: list[float]) -> tuple[list[float | None], dict]:
    if len(lats) != len(lons):
        raise ValueError("lats and lons must align")
    elevations: list[float | None] = [None] * len(lats)
    provenance = {
        "source": "USGS 3DEP NED 10m via OpenTopoData",
        "source_url": NED_URL,
        "fallback_source": "ASTER GDEM 30m via OpenTopoData",
        "retrieval_timestamp": datetime.now(timezone.utc).isoformat(),
        "units": "meters",
        "methodology": (
            "Centroid coordinates were batched to the OpenTopoData ned10m endpoint, "
            "which samples USGS National Elevation Dataset 10 m (3DEP). Points that "
            "failed NED were retried against ASTER GDEM 30 m. Values are DEM samples "
            "at the polygon centroid, not surveyed water-surface elevations."
        ),
        "requested": len(lats),
        "ned_ok": 0,
        "aster_ok": 0,
        "missing": 0,
    }
    failed: list[int] = []
    for start in range(0, len(lats), BATCH):
        chunk = range(start, min(start + BATCH, len(lats)))
        locations = "|".join(f"{lats[i]:.6f},{lons[i]:.6f}" for i in chunk)
        try:
            payload = json_get(NED_URL, params={"locations": locations}, timeout=90)
            results = payload.get("results") or []
            for offset, result in enumerate(results):
                idx = start + offset
                value = result.get("elevation")
                if value is None:
                    failed.append(idx)
                else:
                    elevations[idx] = float(value)
                    provenance["ned_ok"] += 1
            if len(results) != len(list(chunk)):
                for i in chunk:
                    if elevations[i] is None:
                        failed.append(i)
        except Exception:
            failed.extend(list(chunk))
        time.sleep(1.05)

    # Unique failed indexes
    failed = sorted(set(failed))
    for start in range(0, len(failed), BATCH):
        subset = failed[start : start + BATCH]
        locations = "|".join(f"{lats[i]:.6f},{lons[i]:.6f}" for i in subset)
        try:
            payload = json_get(ASTER_FALLBACK_URL, params={"locations": locations}, timeout=90)
            results = payload.get("results") or []
            for offset, result in enumerate(results):
                idx = subset[offset]
                value = result.get("elevation")
                if value is not None and elevations[idx] is None:
                    elevations[idx] = float(value)
                    provenance["aster_ok"] += 1
        except Exception:
            pass
        time.sleep(1.05)

    provenance["missing"] = sum(1 for value in elevations if value is None)
    provenance["processing_timestamp"] = datetime.now(timezone.utc).isoformat()
    return elevations, provenance
