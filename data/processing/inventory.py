"""Build a statewide Colorado waterbody inventory from NHD polygons."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from typing import Any

import geopandas as gpd
import pandas as pd
from shapely.geometry import mapping, shape
from shapely.ops import unary_union
from shapely.validation import make_valid

EQUAL_AREA_CRS = "EPSG:5070"
MAP_SIMPLIFY_DEG = 0.00025
IOU_DUPLICATE = 0.65


def _ms_to_iso(value: Any) -> str | None:
    if value is None:
        return None
    try:
        ms = float(value)
    except (TypeError, ValueError):
        return None
    if ms > 1e12:
        ms /= 1000.0
    if ms > 1e12:
        ms /= 1000.0
    try:
        return datetime.fromtimestamp(ms, tz=timezone.utc).date().isoformat()
    except (OSError, OverflowError, ValueError):
        return None


def load_waterbodies(path: str) -> gpd.GeoDataFrame:
    gdf = gpd.read_file(path)
    if gdf.crs is None:
        gdf = gdf.set_crs("EPSG:4326")
    else:
        gdf = gdf.to_crs("EPSG:4326")
    gdf["geometry"] = gdf.geometry.apply(lambda geom: make_valid(geom) if geom is not None else geom)
    gdf = gdf[~gdf.geometry.is_empty & gdf.geometry.notna()].copy()
    return gdf


def load_counties(path: str) -> gpd.GeoDataFrame:
    counties = gpd.read_file(path)
    if counties.crs is None:
        counties = counties.set_crs("EPSG:4326")
    else:
        counties = counties.to_crs("EPSG:4326")
    counties["county"] = counties["NAME"].str.replace(r"\s+County$", "", regex=True)
    counties["county_fips"] = counties["FIPS"].astype(str)
    return counties[["county", "county_fips", "geometry"]]


def load_cities(path: str) -> gpd.GeoDataFrame:
    cities = gpd.read_file(path)
    if cities.crs is None:
        cities = cities.set_crs("EPSG:4326")
    else:
        cities = cities.to_crs("EPSG:4326")
    cities = cities.rename(columns={"NAME": "name"})
    cities["lon"] = cities.geometry.x
    cities["lat"] = cities.geometry.y
    return cities


def compute_metrics(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    projected = gdf.to_crs(EQUAL_AREA_CRS)
    gdf = gdf.copy()
    gdf["area_m2"] = projected.geometry.area
    gdf["perimeter_m"] = projected.geometry.length
    gdf["area_km2_calc"] = gdf["area_m2"] / 1_000_000.0
    gdf["perimeter_km"] = gdf["perimeter_m"] / 1000.0
    centroids = gdf.geometry.centroid
    # shapely centroid on geographic CRS is acceptable for small polygons
    gdf["lon"] = centroids.x
    gdf["lat"] = centroids.y
    return gdf


def attach_counties(lakes: gpd.GeoDataFrame, counties: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    points = lakes[["geometry"]].copy()
    points["geometry"] = gpd.points_from_xy(lakes["lon"], lakes["lat"], crs="EPSG:4326")
    joined = gpd.sjoin(points, counties, how="left", predicate="within")
    lakes = lakes.copy()
    lakes["county"] = joined["county"].values
    lakes["county_fips"] = joined["county_fips"].values
    missing = lakes["county"].isna()
    if missing.any():
        nearest = gpd.sjoin_nearest(
            points.loc[missing, ["geometry"]],
            counties,
            how="left",
            max_distance=0.2,
        )
        lakes.loc[missing, "county"] = nearest["county"].values
        lakes.loc[missing, "county_fips"] = nearest["county_fips"].values
    return lakes


def detect_duplicates(gdf: gpd.GeoDataFrame) -> pd.Series:
    """Flag source polygons that overlap another feature at high IoU.

    Named GNIS features that are split (e.g. Blue Mesa) are related, not deleted.
    """
    flags = pd.Series(["unique"] * len(gdf), index=gdf.index)
    by_gnis: dict[str, list] = defaultdict(list)
    for idx, row in gdf.iterrows():
        gnis = row.get("GNIS_ID")
        if gnis:
            by_gnis[str(gnis)].append(idx)
    for indexes in by_gnis.values():
        if len(indexes) > 1:
            for idx in indexes:
                flags.loc[idx] = "split_named_polygon"

    sindex = gdf.sindex
    seen: set[tuple[int, int]] = set()
    for idx, geom in gdf.geometry.items():
        if geom is None:
            continue
        for other in sindex.intersection(geom.bounds):
            other_idx = gdf.index[other]
            if other_idx <= idx:
                continue
            key = (idx, other_idx)
            if key in seen:
                continue
            seen.add(key)
            other_geom = gdf.geometry.loc[other_idx]
            if other_geom is None or not geom.intersects(other_geom):
                continue
            inter = geom.intersection(other_geom).area
            union = geom.union(other_geom).area
            if union <= 0:
                continue
            iou = inter / union
            if iou >= IOU_DUPLICATE:
                if flags.loc[idx] == "unique":
                    flags.loc[idx] = "overlap_duplicate"
                if flags.loc[other_idx] == "unique":
                    flags.loc[other_idx] = "overlap_duplicate"
    return flags


def classify_waterbody(ftype: str | None, fcode_desc: str | None) -> str:
    desc = (fcode_desc or "").lower()
    ftype = (ftype or "").lower()
    if "playa" in ftype or "playa" in desc:
        return "playa"
    if "reservoir" in ftype or "reservoir" in desc:
        return "reservoir"
    if "pond" in desc and "lake" not in (ftype or ""):
        return "pond"
    if "intermittent" in desc:
        return "intermittent_lake_pond"
    if "lake" in ftype or "pond" in ftype:
        return "lake_pond"
    return ftype.replace("/", "_") or "waterbody"


def to_records(gdf: gpd.GeoDataFrame, retrieved_at: str) -> list[dict[str, Any]]:
    records = []
    for _, row in gdf.iterrows():
        comid = row.get("COMID")
        waterbody_id = f"nhd-{int(comid)}" if pd.notna(comid) else f"oid-{int(row.get('OBJECTID'))}"
        name = row.get("GNIS_NAME")
        official = None if not isinstance(name, str) or not name.strip() else name.strip()
        source_area = row.get("AREASQKM")
        area = float(row["area_km2_calc"])
        if pd.notna(source_area) and float(source_area) > 0:
            area = float(source_area)
        depth = row.get("MeanDepth")
        max_depth = row.get("MaxDepth")
        elev_src = row.get("ELEVATION")
        elev_dem = row.get("elevation_dem_m")
        records.append(
            {
                "id": waterbody_id,
                "official_name": official,
                "alternative_names": [],
                "display_name": official or _unnamed_label(row, area),
                "geometry": mapping(row.geometry),
                "geometry_simplified": mapping(row.geometry.simplify(MAP_SIMPLIFY_DEG, preserve_topology=True)),
                "lon": float(row["lon"]),
                "lat": float(row["lat"]),
                "county": None if pd.isna(row.get("county")) else str(row.get("county")),
                "county_fips": None if pd.isna(row.get("county_fips")) else str(row.get("county_fips")),
                "elevation_m": None if pd.isna(elev_dem) and pd.isna(elev_src) else float(elev_dem if pd.notna(elev_dem) else elev_src),
                "elevation_nhd_m": None if pd.isna(elev_src) else float(elev_src),
                "elevation_dem_m": None if pd.isna(elev_dem) else float(elev_dem),
                "elevation_source": "USGS 3DEP NED 10m" if pd.notna(elev_dem) else ("NHD ELEVATION" if pd.notna(elev_src) else None),
                "surface_area_km2": round(area, 6),
                "perimeter_km": round(float(row["perimeter_km"]), 4),
                "waterbody_type": classify_waterbody(row.get("FTYPE"), row.get("FCODEDesc")),
                "nhd_ftype": row.get("FTYPE"),
                "nhd_fcode": None if pd.isna(row.get("FCODE")) else int(row.get("FCODE")),
                "nhd_fcode_desc": row.get("FCODEDesc"),
                "depth_m": None if pd.isna(depth) else float(depth),
                "max_depth_m": None if pd.isna(max_depth) else float(max_depth),
                "volume_reported": None if pd.isna(row.get("LakeVolume")) else float(row.get("LakeVolume")),
                "source": "Colorado OIT NHD Waterbodies (USGS NHDPlus)",
                "source_identifier": None if pd.isna(comid) else str(int(comid)),
                "gnis_id": None if not isinstance(row.get("GNIS_ID"), str) else row.get("GNIS_ID"),
                "reachcode": None if pd.isna(row.get("REACHCODE")) else str(row.get("REACHCODE")),
                "source_feature_date": _ms_to_iso(row.get("FDATE")),
                "duplicate_flag": row.get("duplicate_flag"),
                "retrieved_at": retrieved_at,
            }
        )
    return records


def _unnamed_label(row: pd.Series, area: float) -> str:
    county = row.get("county")
    kind = classify_waterbody(row.get("FTYPE"), row.get("FCODEDesc")).replace("_", " ")
    acres = area * 247.105
    if county:
        return f"Unnamed {kind} in {county} County ({acres:.1f} acres)"
    return f"Unnamed {kind} ({acres:.1f} acres)"


def colorado_outline(counties: gpd.GeoDataFrame) -> dict[str, Any]:
    union = unary_union(list(counties.geometry))
    simplified = make_valid(union).simplify(0.005, preserve_topology=True)
    return mapping(simplified)


def bbox_of(geom: dict[str, Any]) -> list[float]:
    g = shape(geom)
    minx, miny, maxx, maxy = g.bounds
    return [minx, miny, maxx, maxy]
