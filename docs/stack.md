# What this project uses

Colorado Ice Atlas is a static statewide map plus a daily Python job that rebuilds ice estimates. The public site does not need a database, an API, or cloud credentials.

Live map: [https://annweng.github.io/colorado-ice-atlas/](https://annweng.github.io/colorado-ice-atlas/)

## At a glance

| Layer | What it is | Used for |
| --- | --- | --- |
| React 19 + TypeScript | Frontend | Map, search, filters, lake profiles |
| Vite 8 | Bundler and local server | Dev at port 3847; production `dist/` |
| MapLibre GL JS | Open-source map engine | Lake polygons, ice colors, zoom |
| Tailwind CSS 4 | Styling | Layout and components |
| Recharts | Charts | Thickness and coverage time series |
| Python 3.12 | Pipeline and optional API | Ingest, ice model, FastAPI |
| GeoPandas / Shapely | Spatial processing | Inventory, centroids, intersections |
| FastAPI | Optional HTTP API | Local/Docker query surface |
| PostGIS 16 | Optional database | Source of truth when `DATABASE_URL` is set |
| GitHub Actions | CI and schedule | Tests, daily ice job, Pages deploy |
| GitHub Pages | Production host | Serves the built frontend at no cost |

The published map reads JSON snapshots from `frontend/public/data`. FastAPI and PostGIS are for local development and a later hosted API; they are not required to view the site.

## Frontend

Built in `frontend/` with Node 22.

| Package | Role |
| --- | --- |
| `react` / `react-dom` | UI |
| `react-router-dom` | Routes (`/`, `/about`, `/methodology`, lake deep-links) |
| `maplibre-gl` | Vector map (not Mapbox GL; no Mapbox token) |
| `recharts` | Ice charts on the lake panel |
| `tailwindcss` + `@tailwindcss/vite` | CSS |
| `lucide-react` | Icons |
| `class-variance-authority`, `clsx`, `tailwind-merge` | Component class helpers |
| `oxlint` | Lint |
| IBM Plex (Google Fonts) | Type |

Map tiles are requested in the browser from public raster services. Attribution is shown on the map.

| Basemap | Tiles | License note |
| --- | --- | --- |
| Streets | Esri World Street Map | Esri attribution required |
| Satellite | Esri World Imagery | Esri / Maxar attribution required |
| Terrain | OpenTopoMap | OSM + SRTM; CC-BY-SA |

Vite `base` is `/` locally. GitHub Pages builds set `GITHUB_PAGES=true` so assets load under `/colorado-ice-atlas/`.

## Ice model

`modeling/ice_models/stefan.py`, version `stefan_snow_v0.1`.

A Stefan √FDD thickness model with snow insulation, morphometry-dependent freeze-over, and a separate coverage estimate. Inputs are daily air temperature, snow, wind, lake area, depth (measured or heuristic), and elevation. It is not a neural network and is not calibrated to a Colorado ice-thickness network.

See `docs/methodology.md`.

## Data pipeline

Python modules under `data/` run from `scripts/run_pipeline.py`. The daily GitHub Action calls that script with `--skip-elevation` so USGS 3DEP heights are reused from the last snapshot instead of resampling OpenTopoData every morning.

| Step | Code | External service | What is stored |
| --- | --- | --- | --- |
| Inventory | `scripts/download_inventory.py` | Colorado OIT ArcGIS (USGS NHDPlus) | Lake polygons, names, depth where present |
| Places | same | Colorado OIT cities + Census counties | Search index |
| Elevation | `data/ingestion/elevation_ned.py` | OpenTopoData (`ned10m`, ASTER 30 m fallback) | Centroid DEM height (m) |
| Weather | `data/ingestion/weather_openmeteo.py` | Open-Meteo Forecast API | 0.25° grid, 92 past days + 7 forecast days (daily temps; hourly snow depth averaged to daily) |
| Satellite | `data/ingestion/satellite_stac.py` | Microsoft Planetary Computer STAC | Sentinel-2 L2A scene id, time, cloud cover |
| Ice | `modeling/ice_models/stefan.py` | none | Coverage, thickness bounds, ice state, confidence |
| Export | `data/processing/pipeline.py` | none | JSON/GeoJSON under `frontend/public/data` |

No API keys are required for these services. They are fair-use / public APIs. Attribution lives in the UI and in `frontend/public/data/provenance.json`.

Weather is requested once per 0.25° cell (batched, 12 cells at a time), not once per lake. Sentinel-2 imagery is not downloaded; only STAC metadata is kept.

## Snapshot files the map reads

| File | Contents |
| --- | --- |
| `summaries.json` | One row per lake: ice state, thickness, coverage, elevation, aliases |
| `map.geojson` / `outline.geojson` | Simplified polygons for MapLibre |
| `predictions.json` | Daily ice series (hindcast + 7-day forecast) |
| `weather_grid.json` | Cell weather used by the model |
| `catalog.json` | Search/filter fields |
| `satellite.json` | Recent Sentinel-2 scene metadata |
| `counties.json` / `cities.json` | Place search |
| `meta.json` / `model_run.json` / `provenance.json` | Counts, timestamps, sources |

## Optional backend and database

`backend/` is a FastAPI app (`uvicorn`, Pydantic, SQLAlchemy, GeoAlchemy2, psycopg). Locally it serves `/api/*` and can recompute a lake series from the weather grid.

`database/migrations/001_init.sql` defines PostGIS tables. Docker Compose starts `postgis/postgis:16-3.4`. Historical prediction rows are append-only when a database is connected.

Production GitHub Pages does not run this API. The browser loads snapshot files only.

## Hosting, CI, and local containers

| Piece | Role |
| --- | --- |
| `.github/workflows/daily.yml` | Cron `20 12 * * *` UTC (05:20 America/Denver): ingest, model, commit snapshots to `main` |
| `.github/workflows/deploy.yml` | Build Vite with `GITHUB_PAGES=true` and publish to GitHub Pages |
| `.github/workflows/ci.yml` | `ruff` + `pytest`, frontend production build, `terraform fmt` / `validate` |
| `docker-compose.yml` | PostGIS, API, Vite frontend; pipeline as an optional profile |
| `infrastructure/terraform/` | Optional Cloudflare Pages/R2 and future GCP/AWS modules; **not applied** for the live site |

Python lint/format: Ruff. Tests: pytest under `tests/`.

## What this repo does not use in production

- No Mapbox, Google Maps, or paid tile token
- No authentication on the public map
- No application database on GitHub Pages
- No Cloudflare, Supabase, GCP, or AWS SDKs in application code
- No Sentinel COG downloads or NDSI in the daily job
- Terraform apply is manual and gated (`enable_cloudflare=false`)

Those options are documented in `docs/multi_cloud.md` and `docs/cloud_costs.md` as later hosts, not as current dependencies.

## Related docs

- `docs/data_sources.md` — inventory, licenses, what was considered and rejected
- `docs/methodology.md` — ice math
- `docs/architecture.md` — runtime split and data flow
- `docs/deployment.md` — how to run and where it is published
- `docs/limitations.md` — what the estimates cannot do
