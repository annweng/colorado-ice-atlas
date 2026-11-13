from __future__ import annotations

from typing import Annotated, Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from app.core.config import settings
from app.services import query, store
from modeling.ice_models.stefan import MODEL_NAME, MODEL_VERSION, LakeParams, estimate_depth_m, simulate_season

app = FastAPI(
    title="Colorado Ice Atlas API",
    description=(
        "Statewide Colorado waterbody inventory, environmental inputs, and "
        "physics-informed ice estimates. Model outputs are estimates, not field measurements."
    ),
    version="0.1.0",
)

origins = [origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins or ["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict[str, Any]:
    meta = store.meta()
    return {"status": "ok", "meta": meta, "database": bool(settings.database_url)}


@app.get("/api/stats")
def stats() -> dict[str, Any]:
    rows = store.summaries()
    states: dict[str, int] = {}
    for row in rows:
        states[row.get("ice_state") or "unknown"] = states.get(row.get("ice_state") or "unknown", 0) + 1
    return {
        "waterbodies": len(rows),
        "named": sum(1 for row in rows if row.get("named")),
        "ice_states": states,
        "meta": store.meta(),
        "model_run": store.model_run(),
    }


@app.get("/api/counties")
def counties() -> list[dict[str, Any]]:
    return store.counties()


@app.get("/api/search")
def search_waterbodies(q: str = "", limit: int = 20) -> dict[str, Any]:
    return {"query": q, "items": query.search(q, limit=limit)}


@app.get("/api/waterbodies")
def list_waterbodies(
    q: str | None = None,
    county: str | None = None,
    waterbody_type: str | None = None,
    ice_state: str | None = None,
    confidence: str | None = None,
    named_only: bool = False,
    min_elevation: float | None = None,
    max_elevation: float | None = None,
    min_area: float | None = None,
    max_area: float | None = None,
    min_coverage: float | None = None,
    max_coverage: float | None = None,
    min_thickness: float | None = None,
    max_thickness: float | None = None,
    bbox: str | None = Query(default=None, description="minLon,minLat,maxLon,maxLat"),
    has_satellite: bool | None = None,
    limit: int = 100,
    offset: int = 0,
) -> dict[str, Any]:
    box = None
    if bbox:
        parts = [float(p) for p in bbox.split(",")]
        if len(parts) != 4:
            raise HTTPException(400, "bbox must be minLon,minLat,maxLon,maxLat")
        box = (parts[0], parts[1], parts[2], parts[3])
    rows = query.apply_filters(
        store.summaries(),
        q=q,
        county=county,
        waterbody_type=waterbody_type,
        ice_state=ice_state,
        confidence=confidence,
        named_only=named_only,
        min_elevation=min_elevation,
        max_elevation=max_elevation,
        min_area=min_area,
        max_area=max_area,
        min_coverage=min_coverage,
        max_coverage=max_coverage,
        min_thickness=min_thickness,
        max_thickness=max_thickness,
        bbox=box,
        has_satellite=has_satellite,
    )
    return query.paginate(rows, limit, offset)


@app.get("/api/waterbodies/{waterbody_id}")
def waterbody_detail(waterbody_id: str) -> dict[str, Any]:
    lake = store.by_id().get(waterbody_id)
    if not lake:
        raise HTTPException(404, "Waterbody not found")
    pred = store.predictions().get(waterbody_id)
    sat = store.satellite().get(waterbody_id)
    weather_meta = store.weather_grid().get(lake.get("grid_cell_id", ""))
    series = _series_for(lake, weather_meta)
    return {
        "waterbody": lake,
        "prediction": pred,
        "satellite": sat,
        "weather": {
            "meta": {
                "grid_cell_id": lake.get("grid_cell_id"),
                "source": None if not weather_meta else weather_meta.get("source"),
                "retrieved_at": None if not weather_meta else weather_meta.get("retrieved_at"),
                "grid_latitude": None if not weather_meta else weather_meta.get("latitude"),
                "grid_longitude": None if not weather_meta else weather_meta.get("longitude"),
            },
            "daily": None if not weather_meta else weather_meta.get("daily"),
        },
        "timeseries": series,
        "observation_classes": {
            "model_estimate": True,
            "satellite_observation": sat is not None,
            "field_measurement": False,
        },
    }


@app.get("/api/waterbodies/{waterbody_id}/predictions")
def waterbody_predictions(waterbody_id: str) -> dict[str, Any]:
    if waterbody_id not in store.by_id():
        raise HTTPException(404, "Waterbody not found")
    return {
        "current": store.predictions().get(waterbody_id),
        "historical_note": (
            "Daily pipeline appends predictions without overwriting. This snapshot "
            "includes the current season hindcast plus a 7-day modeled forecast."
        ),
        "timeseries": waterbody_detail(waterbody_id)["timeseries"],
    }


@app.get("/api/waterbodies/{waterbody_id}/satellite")
def waterbody_satellite(waterbody_id: str) -> dict[str, Any]:
    if waterbody_id not in store.by_id():
        raise HTTPException(404, "Waterbody not found")
    sat = store.satellite().get(waterbody_id)
    return {"observation": sat, "kind": "satellite_scene_metadata"}


@app.get("/api/compare")
def compare(ids: Annotated[str, Query(description="Comma-separated waterbody ids")]) -> dict[str, Any]:
    wanted = [part.strip() for part in ids.split(",") if part.strip()][:6]
    items = []
    for waterbody_id in wanted:
        try:
            items.append(waterbody_detail(waterbody_id))
        except HTTPException:
            continue
    return {"items": items}


@app.get("/api/pipeline/status")
def pipeline_status() -> dict[str, Any]:
    return {
        "model_run": store.model_run(),
        "provenance": store.provenance(),
        "paths": store.data_paths(),
    }


@app.get("/api/model")
def model_metadata() -> dict[str, Any]:
    return {
        "name": MODEL_NAME,
        "version": MODEL_VERSION,
        "outputs": [
            "estimated_ice_coverage",
            "estimated_ice_thickness_cm",
            "lower_thickness_estimate_cm",
            "upper_thickness_estimate_cm",
            "confidence",
        ],
        "does_not": [
            "classify recreational safety",
            "compute vehicle weight limits",
            "treat satellite scenes as thickness measurements",
        ],
    }


@app.get("/api/map.geojson")
def map_geojson() -> FileResponse:
    path = settings.data_dir / "map.geojson"
    if not path.exists():
        raise HTTPException(404, "Map snapshot missing")
    return FileResponse(path, media_type="application/geo+json")


def _series_for(lake: dict[str, Any], weather_meta: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not weather_meta or not weather_meta.get("daily"):
        return []
    depth = lake.get("depth_m")
    params = LakeParams(
        area_km2=lake.get("surface_area_km2") or 0.01,
        depth_m=depth if depth is not None else estimate_depth_m(lake.get("surface_area_km2") or 0.01),
        elevation_m=lake.get("elevation_m"),
        waterbody_type=lake.get("waterbody_type") or "lake_pond",
        fcode_desc=lake.get("nhd_fcode_desc"),
        depth_is_estimated=depth is None,
    )
    daily = weather_meta["daily"]
    series = simulate_season(
        dates=[d["date"] for d in daily],
        tmean_c=[d.get("tmean_c") for d in daily],
        tmin_c=[d.get("tmin_c") for d in daily],
        tmax_c=[d.get("tmax_c") for d in daily],
        snow_depth_m=[d.get("snow_depth_m") for d in daily],
        snowfall_cm=[d.get("snowfall_cm") for d in daily],
        wind_speed_kmh=[d.get("wind_speed_kmh") for d in daily],
        precipitation_mm=[d.get("precipitation_mm") for d in daily],
        shortwave_mjm2=[d.get("shortwave_mjm2") for d in daily],
        is_forecast=[d.get("is_forecast") for d in daily],
        params=params,
    )
    return [
        {
            "date": row.date,
            "is_forecast": row.is_forecast,
            "tmin_c": row.tmin_c,
            "tmax_c": row.tmax_c,
            "tmean_c": row.tmean_c,
            "snow_depth_m": row.snow_depth_m,
            "snowfall_cm": row.snowfall_cm,
            "wind_speed_kmh": row.wind_speed_kmh,
            "precipitation_mm": row.precipitation_mm,
            "fdd_c_day": row.fdd_c_day,
            "tdd_c_day": row.tdd_c_day,
            "estimated_ice_coverage": row.estimated_ice_coverage_pct,
            "estimated_ice_thickness_cm": row.estimated_ice_thickness_cm,
            "lower_thickness_cm": row.lower_thickness_cm,
            "upper_thickness_cm": row.upper_thickness_cm,
            "ice_state": row.ice_state,
            "confidence": row.confidence,
        }
        for row in series
    ]
