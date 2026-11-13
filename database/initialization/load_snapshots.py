"""Load processed snapshots into PostGIS when DATABASE_URL is set."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "backend"))


def main() -> int:
    url = os.environ.get("DATABASE_URL")
    if not url:
        print("DATABASE_URL unset; skipping PostGIS load. File snapshots remain the runtime store.")
        return 0
    try:
        import psycopg
    except ImportError:
        print("psycopg is not installed")
        return 1

    data_dir = ROOT / "frontend" / "public" / "data"
    catalog = json.loads((data_dir / "catalog.json").read_text())
    predictions = json.loads((data_dir / "predictions.json").read_text())
    schema = (ROOT / "database" / "migrations" / "001_init.sql").read_text()
    with psycopg.connect(url) as conn:
        conn.execute(schema)
        with conn.cursor() as cur:
            for row in catalog:
                cur.execute(
                    """
                    INSERT INTO weather_grid_cells (id, latitude, longitude, geom, elevation_m)
                    VALUES (%s, %s, %s, ST_SetSRID(ST_MakePoint(%s, %s), 4326), %s)
                    ON CONFLICT (id) DO NOTHING
                    """,
                    (
                        row.get("grid_cell_id"),
                        row.get("lat"),
                        row.get("lon"),
                        row.get("lon"),
                        row.get("lat"),
                        row.get("elevation_m"),
                    ),
                )
                cur.execute(
                    """
                    INSERT INTO waterbodies (
                        id, official_name, display_name, geometry, centroid, county,
                        elevation_m, elevation_source, surface_area_km2, perimeter_km,
                        waterbody_type, depth_m, max_depth_m, source, source_identifier,
                        gnis_id, duplicate_flag, grid_cell_id, updated_at
                    ) VALUES (
                        %(id)s, %(official_name)s, %(display_name)s,
                        ST_SetSRID(ST_MakePoint(%(lon)s, %(lat)s), 4326),
                        ST_SetSRID(ST_MakePoint(%(lon)s, %(lat)s), 4326),
                        %(county)s, %(elevation_m)s, %(elevation_source)s, %(surface_area_km2)s,
                        %(perimeter_km)s, %(waterbody_type)s, %(depth_m)s, %(max_depth_m)s,
                        %(source)s, %(source_identifier)s, %(gnis_id)s, %(duplicate_flag)s,
                        %(grid_cell_id)s, now()
                    )
                    ON CONFLICT (id) DO UPDATE SET
                        display_name = EXCLUDED.display_name,
                        elevation_m = EXCLUDED.elevation_m,
                        updated_at = now()
                    """,
                    row,
                )
            for pred in predictions:
                cur.execute(
                    """
                    INSERT INTO ice_predictions (
                        waterbody_id, prediction_timestamp, as_of_date, estimated_ice_coverage,
                        estimated_ice_thickness, lower_thickness_estimate, upper_thickness_estimate,
                        ice_state, confidence, data_quality, model_version, input_data_references,
                        fdd_c_day, is_stale
                    ) VALUES (
                        %(waterbody_id)s, %(prediction_timestamp)s, %(as_of_date)s,
                        %(estimated_ice_coverage)s, %(estimated_ice_thickness_cm)s,
                        %(lower_thickness_estimate_cm)s, %(upper_thickness_estimate_cm)s,
                        %(ice_state)s, %(confidence)s, %(data_quality)s, %(model_version)s,
                        %(input_data_references)s, %(fdd_c_day)s, %(is_stale)s
                    )
                    """,
                    {**pred, "input_data_references": json.dumps(pred.get("input_data_references") or {})},
                )
        conn.commit()
    print(f"Loaded {len(catalog)} waterbodies and {len(predictions)} predictions")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
