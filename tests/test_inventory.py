import geopandas as gpd
from shapely.geometry import Polygon, mapping

from data.processing.inventory import classify_waterbody, detect_duplicates


def test_classify_intermittent_and_reservoir():
    assert classify_waterbody("Lake/Pond", "Intermittent Lake/Pond") == "intermittent_lake_pond"
    assert classify_waterbody("Reservoir", "Aquaculture Reservoir") == "reservoir"
    assert classify_waterbody("Playa", "Playa") == "playa"


def test_overlap_duplicate_flag():
    a = Polygon([(-105, 40), (-105, 40.1), (-104.9, 40.1), (-104.9, 40)])
    b = Polygon([(-105.01, 40), (-105.01, 40.1), (-104.91, 40.1), (-104.91, 40)])
    gdf = gpd.GeoDataFrame(
        {"GNIS_ID": [None, None], "geometry": [a, b]},
        geometry="geometry",
        crs="EPSG:4326",
    )
    flags = detect_duplicates(gdf)
    assert list(flags) == ["overlap_duplicate", "overlap_duplicate"]


def test_split_named_polygon_not_deleted():
    a = Polygon([(-105, 40), (-105, 40.2), (-104.8, 40.2), (-104.8, 40)])
    b = Polygon([(-104.7, 40), (-104.7, 40.2), (-104.5, 40.2), (-104.5, 40)])
    gdf = gpd.GeoDataFrame(
        {"GNIS_ID": ["001", "001"], "geometry": [a, b]},
        geometry="geometry",
        crs="EPSG:4326",
    )
    flags = detect_duplicates(gdf)
    assert list(flags) == ["split_named_polygon", "split_named_polygon"]
    assert mapping(a)["type"] == "Polygon"
