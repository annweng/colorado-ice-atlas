# Architecture

Colorado Ice Atlas is a map-first environmental information system. The map is the product. The API, database, and daily pipeline exist to keep that map honest: every ice value has a timestamp, a model version, and a source.

## Runtime split

| Surface | Role |
| --- | --- |
| Vite + MapLibre frontend | Statewide map, search, filters, lake profiles, charts |
| FastAPI | Query, pagination, OpenAPI, on-demand ice series |
| Snapshot JSON in `frontend/public/data` | $0 static hosting; the published map does not need an always-on API |
| PostgreSQL / PostGIS | Source of truth when `DATABASE_URL` is set |
| GitHub Actions | Daily weather ingest, STAC search, ice estimates |

The frontend talks to snapshot files first. The API is used in Docker and can recompute a lake series from the weather grid. Application code does not import Cloudflare, Supabase, GCP, or AWS SDKs.

## Data flow

1. `scripts/download_inventory.py` pulls NHD waterbodies, counties, and cities from Colorado OIT GIS (USGS NHDPlus).
2. Centroids are sampled against USGS 3DEP NED 10 m.
3. Each lake is assigned to a 0.25° weather cell. Open-Meteo is queried once per cell (not once per lake).
4. Sentinel-2 L2A scenes over Colorado are discovered in the Planetary Computer STAC. Raw imagery is not stored.
5. `stefan_snow_v0.1` walks the daily temperature series and writes coverage, thickness bounds, confidence, and ice state.
6. Snapshots are exported for the map. Historical prediction rows are append-only when PostGIS is enabled.

## Why snapshots plus PostGIS

Seven thousand polygons with simplified geometry are small enough to ship as GeoJSON and render in MapLibre. That matches the free-tier goal: Cloudflare Pages can serve the atlas with no virtual machine. PostGIS remains the spatial database of record for bbox queries, duplicate detection, and future 3DHP-scale inventories.

## Ice states on the map

| Color | State | Meaning |
| --- | --- | --- |
| Red | `open_water` | Modeled coverage under 15% |
| Orange | `partial` | 15–70% |
| Yellow | `extensive` | 70–90%, or frozen coverage with very thin ice / uncertain class |
| Blue | `frozen` | ≥90% coverage and modeled thickness ≥ 4 cm |
| Gray | `unknown` | Missing weather or withheld estimate |

Dashed outlines mark lakes that intersect a recent Sentinel-2 scene. That is imagery metadata, not thickness.

## Portability

- Containers: `docker compose up --build`
- Database: standard PostGIS SQL migrations
- Object storage: filesystem today; S3-compatible (R2, GCS, S3) behind a one-function put/get interface
- Config: environment variables only
