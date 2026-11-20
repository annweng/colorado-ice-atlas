from pathlib import Path

import pandas as pd

from data.processing.pipeline import load_cached_dem_elevations


def test_cached_dem_reuses_snapshot_heights(tmp_path: Path) -> None:
    summaries = tmp_path / "summaries.json"
    summaries.write_text(
        '[{"id":"nhd-1","elevation_m":3120},{"id":"nhd-2","elevation_m":null}]',
        encoding="utf-8",
    )
    lakes = pd.DataFrame({"COMID": [1, 2, 3], "OBJECTID": [10, 20, 30]})
    elevations, provenance = load_cached_dem_elevations(lakes, summaries)
    assert elevations == [3120.0, None, None]
    assert provenance["skipped"] is True
    assert provenance["cache_hits"] == 1
    assert provenance["missing"] == 2


def test_cached_dem_missing_file(tmp_path: Path) -> None:
    lakes = pd.DataFrame({"COMID": [99], "OBJECTID": [1]})
    elevations, provenance = load_cached_dem_elevations(lakes, tmp_path / "missing.json")
    assert elevations == [None]
    assert provenance["cache_hits"] == 0
    assert provenance["missing"] == 1
