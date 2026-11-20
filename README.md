# Colorado Ice Atlas

**Explore. Observe. Forecast.**

A public map of Colorado lakes, reservoirs, and ponds with modeled ice coverage and thickness. Every estimate is timestamped, versioned, and separated from satellite scene metadata and field measurements.

This is not an ice-safety product. Modeled thickness is not a measurement and does not mean ice is safe to walk, skate, fish, or drive on.

## What you can do

- Browse the statewide inventory (NHDPlus lakes, ponds, reservoirs, and playas).
- Search by name, county, town, or coordinates.
- Filter by elevation, area, ice state, thickness, coverage, and confidence.
- Open a lake profile for morphometry, weather, a 7-day forecast, and ice charts.
- Read sources, acquisition dates, and model version `stefan_snow_v0.1`.

## Quick start (local, no cloud)

```bash
python3 -m pip install -r backend/requirements.txt
python3 scripts/download_inventory.py
PYTHONPATH=. python3 scripts/run_pipeline.py

# API
PYTHONPATH=.:backend python3 -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8765

# Map
cd frontend && npm install && npm run dev
```

Open [http://127.0.0.1:3847](http://127.0.0.1:3847). API docs: [http://127.0.0.1:8765/docs](http://127.0.0.1:8765/docs).

### Docker

```bash
docker compose up --build
```

PostGIS starts automatically. The map still works from snapshot files if the database is empty.

## Stack

The public site is a static Vite app. A Python job rebuilds ice snapshots every morning. FastAPI and PostGIS are optional for local work; GitHub Pages does not run them.

| | |
| --- | --- |
| Map | React 19, TypeScript, Vite, MapLibre GL JS, Tailwind CSS, Recharts |
| Ice | Python 3.12, GeoPandas, NumPy — model `stefan_snow_v0.1` |
| Optional API | FastAPI, PostGIS 16 |
| Hosting | GitHub Pages + GitHub Actions (daily ingest, CI, deploy) |
| Basemaps | Esri World Street Map, Esri World Imagery, OpenTopoMap |

What each library and API is for: [`docs/stack.md`](docs/stack.md). Full doc index: [`docs/README.md`](docs/README.md).

## Data

Operational inventory: Colorado OIT NHD Waterbodies (USGS NHDPlus), 7,132 polygons. Elevation: USGS 3DEP via OpenTopoData (cached on daily runs). Weather: Open-Meteo 0.25° grid. Satellite: Sentinel-2 L2A scene metadata from Microsoft Planetary Computer STAC, not pixel ice. Details in `docs/data_sources.md` and `docs/methodology.md`.

## Costs

Public map: [https://annweng.github.io/colorado-ice-atlas/](https://annweng.github.io/colorado-ice-atlas/). The daily ice pipeline commits snapshots to `main`, then GitHub Pages rebuilds. v1 targets **$0/month**. See `docs/cloud_costs.md` and `docs/deployment.md`.

## Repository layout

```
frontend/   MapLibre app
backend/    FastAPI
modeling/   Ice model
data/       Ingestion and processing
database/   PostGIS migrations
infrastructure/terraform/
docs/
```
