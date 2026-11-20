# Cloud costs (target $0/month)

Figures checked November 2026. Free tiers change. Do not assume they are permanent. Do not apply Terraform in CI.

Production is GitHub Pages. Other rows are optional later hosts or the APIs the daily job already calls. See `docs/stack.md` for how they fit together.

| Service | Role | Free-tier notes | Expected v1 use | Risk |
| --- | --- | --- | --- | --- |
| GitHub Pages | Public map | Free for public repos | Static Vite `dist/` | Custom domain is optional; HTTPS is included |
| GitHub-hosted Actions | Daily pipeline + CI + Pages deploy | 2,000 min/month on free private repos; public repos more generous | ~20–40 min/day ingest + CI | Minutes overage if Sentinel processing is added |
| Cloudflare Pages | Optional later frontend host | Unlimited sites on free plan; build limits apply | Not used in production | Stay on the free plan; no Workers paid features |
| Cloudflare R2 | Snapshots / optional tfstate | 10 GB stored / month, 1 million Class A, 10 million Class B, no egress fees | &lt; 1 GB GeoJSON + JSON | Avoid storing raw Sentinel tiles |
| Supabase free project | Optional PostGIS | 500 MB database, paused after inactivity on some plans | Schema + predictions well under 500 MB | Pauses; keep file snapshots so the map still works |
| Open-Meteo | Weather | No key; fair-use rate limits (~600 req/min) | ~200 grid cells batched | Do not query per lake |
| OpenTopoData | 3DEP sample | 1 req/s public | ~72 batched elevation calls per full rebuild | Cache elevations; `--skip-elevation` on daily runs |
| Planetary Computer STAC | Sentinel-2 search | Anonymous STAC; asset downloads throttled | Metadata only | Never bulk-download COGs in Actions |
| Esri World Street Map | Streets basemap | Public tiles; attribution required | Map views | Do not scrape tiles for storage |
| Esri World Imagery | Satellite basemap | Public tiles; attribution required | Map views | Do not scrape tiles for storage |
| OpenTopoMap | Terrain basemap | Tile usage policy / CC-BY-SA | Map views | Keep attribution |
| Google Cloud / AWS | Future | Always-free and 12-month credits exist but are easy to exceed | Not provisioned | Require approval before `terraform apply` |

## Satellite cost control

The daily job searches STAC and stores scene JSON. It does not persist imagery. Derived ice products, if added later, should be per-lake samples of COG windows, not statewide GeoTIFFs.

## Local fallback

`docker compose up --build` and `python scripts/run_pipeline.py` do not require cloud accounts. If a free API is down, the previous snapshot remains on disk and the UI labels it with its last successful `as_of` date.
