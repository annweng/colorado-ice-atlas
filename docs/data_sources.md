# Data sources

Evaluated 12 November 2026. Retrieval timestamps are stored in `frontend/public/data/provenance.json` after each pipeline run. How these APIs sit in the stack is in `docs/stack.md`.

## Waterbody inventory

### Operational source: Colorado OIT NHD Waterbodies

- Service: `https://gis.colorado.gov/public/rest/services/OIT/Colorado_State_Basemap/MapServer/48`
- Origin: USGS National Hydrography Dataset / NHDPlus, filtered to Colorado
- License: USGS-authored NHD is public domain; attribute USGS and Colorado GIS
- Filter used: `Lake/Pond`, `Reservoir`, `Playa`
- Count at extract: **7,132** polygons (7,075 lake/pond, 39 reservoir, 18 playa)
- Named (GNIS): 2,408. Some well-known lakes have no GNIS_NAME in NHDPlus. Documented local names live in `data/processing/aliases.json` (Georgetown Lake is `nhd-2884804`, matched to USGS NWIS 394359105411901).
- NHDPlus MeanDepth present: 2,652
- NHD `ELEVATION` present: ~129 (unusable as a statewide elevation field)
- Area range: 0.001–62.2 km² (Navajo Reservoir is the largest polygon; it straddles the New Mexico line and is retained because the source layer includes it)

NHD FCODE descriptions include perennial and intermittent lakes, aquaculture and treatment reservoirs, and a tailings pond. Those classes are stored and shown; they are not hidden.

### Considered and not used as v1 operational inventory

| Source | Why not operational in v1 |
| --- | --- |
| USGS 3DHP Waterbody service | ~113,000 polygons in the Colorado bounding box, including neighboring-state spillover and elevation-derived micro-features. Suitable as a later high-resolution ingest; too large for the first static GeoJSON map without vector tiles. |
| NHD High Resolution statewide GDB | 0.5–1 GB. Same public-domain lineage as the OIT layer, heavier to snapshot. |
| HydroLAKES | Depth estimates for larger lakes only; licensing is CC-BY and useful as an optional depth join later. |
| WQCD 2026 assessed lakes | Regulatory assessment units, not a complete pond inventory. |
| Ice mass / swamp / river polygons in the same NHD layer | Out of scope for lake ice. Counted during evaluation and excluded. |

Duplicate handling keeps source polygons. Named lakes split across polygons (Blue Mesa Reservoir) are flagged `split_named_polygon`. High-IoU unnamed overlaps are flagged `overlap_duplicate` and not deleted.

## Elevation

USGS 3DEP NED 10 m sampled at each centroid through OpenTopoData (`ned10m`, ASTER 30 m fallback). This is a DEM sample, not a surveyed water-surface elevation.

## Weather

Open-Meteo Forecast API with `past_days=92` and `forecast_days=7`, assigned on a 0.25° grid. This is gridded meteorology (GFS/ECMWF blend; ERA5-Land where Open-Meteo uses reanalysis), not a COOP/ASOS station. Direct NOAA ISD or CDS ERA5-Land NetCDF remains a documented alternative if Open-Meteo terms or rate limits change.

Attribution: Weather data by Open-Meteo.com. Contains modified Copernicus Climate Change Service information where ERA5 is used.

## Satellite

Microsoft Planetary Computer STAC, collection `sentinel-2-l2a`, Colorado bbox, last 14 days, cloud cover &lt; 40%. The pipeline records scene id, time, and cloud cover for intersecting lakes. It does **not** download COGs or compute NDSI in the daily job. Pixel ice classification is a future optional module.

## Places

Colorado OIT GIS cities (277 points) and Census counties (64). Used for search, not for ice.

## Field ice measurements

No statewide public in-situ ice thickness network was found that could be redistributed for all inventoried lakes. The `ice_measurements` table is empty by design until observations are contributed. The UI must not imply that model output is measured ice.
