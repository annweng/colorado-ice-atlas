import {
  LngLatBounds,
  Map as MapLibreMap,
  NavigationControl,
  ScaleControl,
  setWorkerUrl,
  type FilterSpecification,
  type MapLayerMouseEvent,
} from "maplibre-gl";
import maplibreWorker from "maplibre-gl/dist/maplibre-gl-worker.mjs?worker&url";
import "maplibre-gl/dist/maplibre-gl.css";

setWorkerUrl(maplibreWorker);
import { useEffect, useRef } from "react";
import { assetUrl } from "../lib/paths";
import type { Filters, IceState, WaterbodySummary } from "../lib/types";
import { ICE_COLORS } from "../lib/types";
import { BASEMAPS, COLORADO_BOUNDS, COLORADO_CENTER, type BasemapId } from "./basemaps";

type Props = {
  filters: Filters;
  searchIds: string[] | null;
  selectedId: string | null;
  onSelect: (id: string) => void;
  basemap: BasemapId;
  focus: WaterbodySummary | null;
};

export function MapView({ filters, searchIds, selectedId, onSelect, basemap, focus }: Props) {
  const container = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<MapLibreMap | null>(null);
  const onSelectRef = useRef(onSelect);
  const filterRef = useRef({ filters, searchIds, selectedId });
  const focusRef = useRef(focus);
  const skipStyleSwap = useRef(true);
  onSelectRef.current = onSelect;
  filterRef.current = { filters, searchIds, selectedId };
  focusRef.current = focus;

  useEffect(() => {
    if (!container.current || mapRef.current) return;
    const map = new MapLibreMap({
      container: container.current,
      style: BASEMAPS[basemap].style,
      center: COLORADO_CENTER,
      zoom: 6.15,
      maxBounds: COLORADO_BOUNDS,
      renderWorldCopies: false,
    });
    map.addControl(new NavigationControl({ visualizePitch: false }), "bottom-right");
    map.addControl(new ScaleControl({ unit: "imperial" }), "bottom-left");
    mapRef.current = map;

    const ready = () => {
      addDataLayers(map);
      applyFilters(map, filterRef.current.filters, filterRef.current.searchIds, filterRef.current.selectedId);
      if (focusRef.current) fitLake(map, focusRef.current);
    };
    map.on("load", ready);
    map.on("click", "water-fill", (event: MapLayerMouseEvent) => {
      const id = event.features?.[0]?.properties?.id as string | undefined;
      if (id) onSelectRef.current(id);
    });
    map.on("mouseenter", "water-fill", () => {
      map.getCanvas().style.cursor = "pointer";
    });
    map.on("mouseleave", "water-fill", () => {
      map.getCanvas().style.cursor = "";
    });

    return () => {
      map.remove();
      mapRef.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;
    if (skipStyleSwap.current) {
      skipStyleSwap.current = false;
      return;
    }
    const readd = () => {
      addDataLayers(map);
      applyFilters(map, filterRef.current.filters, filterRef.current.searchIds, filterRef.current.selectedId);
      if (focusRef.current) fitLake(map, focusRef.current);
    };
    map.setStyle(BASEMAPS[basemap].style);
    map.once("idle", readd);
  }, [basemap]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map?.getLayer("water-fill")) return;
    applyFilters(map, filters, searchIds, selectedId);
  }, [filters, searchIds, selectedId]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !focus) return;
    const targetId = focus.id;
    let cancelled = false;
    const run = () => {
      if (cancelled || mapRef.current !== map) return;
      const current = focusRef.current;
      if (!current || current.id !== targetId) return;
      map.resize();
      fitLake(map, current);
    };
    if (map.isStyleLoaded()) {
      requestAnimationFrame(run);
    }
    map.once("idle", run);
    return () => {
      cancelled = true;
      map.off("idle", run);
    };
  }, [focus?.id]);

  return <div ref={container} className="h-full w-full" />;
}

function lakeBounds(focus: WaterbodySummary): LngLatBounds {
  const raw = focus.bbox;
  let minx = focus.lon;
  let miny = focus.lat;
  let maxx = focus.lon;
  let maxy = focus.lat;
  if (Array.isArray(raw) && raw.length === 4) {
    minx = Number(raw[0]);
    miny = Number(raw[1]);
    maxx = Number(raw[2]);
    maxy = Number(raw[3]);
  }
  const minSpan = 0.006;
  if (maxx - minx < minSpan) {
    const mid = (minx + maxx) / 2;
    minx = mid - minSpan / 2;
    maxx = mid + minSpan / 2;
  }
  if (maxy - miny < minSpan) {
    const mid = (miny + maxy) / 2;
    miny = mid - minSpan / 2;
    maxy = mid + minSpan / 2;
  }
  return new LngLatBounds([minx, miny], [maxx, maxy]);
}

function lakePadding(width: number, height: number) {
  const panel = width >= 768 ? Math.min(412, Math.round(width * 0.38)) : 0;
  const fill = 0.46;
  const usableW = Math.max(160, width - panel);
  const xPad = Math.round((usableW * (1 - fill)) / 2);
  const yPad = Math.round((height * (1 - fill)) / 2);
  const left = Math.max(12, xPad);
  const top = Math.max(48, yPad);
  const bottom = Math.max(40, yPad);
  const right = Math.max(12, xPad) + panel;
  const maxLeftRight = Math.max(24, width - 80);
  const maxTopBottom = Math.max(24, height - 80);
  return {
    top: Math.min(top, Math.floor(maxTopBottom / 2)),
    bottom: Math.min(bottom, Math.floor(maxTopBottom / 2)),
    left: Math.min(left, Math.floor(maxLeftRight * 0.35)),
    right: Math.min(right, Math.floor(maxLeftRight * 0.65)),
  };
}

function zoomForArea(areaKm2: number) {
  const sideKm = Math.max(0.55, Math.sqrt(Math.max(areaKm2, 0.01)) * 2.4);
  return Math.min(15.5, Math.max(8.6, 13.8 - Math.log2(sideKm)));
}

function fitLake(map: MapLibreMap, focus: WaterbodySummary) {
  const width = Math.max(1, map.getContainer().clientWidth);
  const height = Math.max(1, map.getContainer().clientHeight);
  const padding = lakePadding(width, height);
  const bounds = lakeBounds(focus);
  const apply = (center: [number, number], zoom: number) => {
    map.easeTo({ center, zoom, duration: 900, essential: true });
  };
  try {
    const camera = map.cameraForBounds(bounds, { padding, maxZoom: 15.75 });
    if (camera?.center && Number.isFinite(camera.zoom)) {
      const point = camera.center as { lng?: number; lon?: number; lat?: number } | [number, number];
      const lng = Array.isArray(point) ? point[0] : (point.lng ?? point.lon);
      const lat = Array.isArray(point) ? point[1] : point.lat;
      if (lng == null || lat == null) throw new Error("missing camera center");
      apply([lng, lat], camera.zoom ?? zoomForArea(focus.area_km2));
      return;
    }
  } catch {
    // Fall through to a size-based zoom if camera math fails.
  }
  apply([focus.lon, focus.lat], zoomForArea(focus.area_km2));
}

function addDataLayers(map: MapLibreMap) {
  if (map.getSource("waterbodies")) return;
  if (!map.getSource("outline")) {
    map.addSource("outline", { type: "geojson", data: assetUrl("data/outline.geojson") });
    map.addLayer({
      id: "outline-line",
      type: "line",
      source: "outline",
      paint: { "line-color": "#9ec9e8", "line-width": 1.2, "line-opacity": 0.7 },
    });
  }
  map.addSource("waterbodies", { type: "geojson", data: assetUrl("data/map.geojson"), promoteId: "id" });
  map.addLayer({
    id: "water-fill",
    type: "fill",
    source: "waterbodies",
    paint: {
      "fill-color": [
        "match",
        ["get", "ice_state"],
        "open_water",
        ICE_COLORS.open_water,
        "partial",
        ICE_COLORS.partial,
        "extensive",
        ICE_COLORS.extensive,
        "frozen",
        ICE_COLORS.frozen,
        ICE_COLORS.unknown,
      ],
      "fill-opacity": 0.62,
    },
  });
  map.addLayer({
    id: "water-line",
    type: "line",
    source: "waterbodies",
    paint: { "line-color": "#d7e7f4", "line-width": 0.7, "line-opacity": 0.85 },
  });
  map.addLayer({
    id: "water-sat",
    type: "line",
    source: "waterbodies",
    paint: {
      "line-color": "#ffffff",
      "line-width": 1.1,
      "line-dasharray": [1.4, 1.4],
      "line-opacity": 0.85,
    },
  });
}

function applyFilters(map: MapLibreMap, filters: Filters, searchIds: string[] | null, selectedId: string | null) {
  if (!map.getLayer("water-fill")) return;
  const expr = buildFilter(filters, searchIds);
  map.setFilter("water-fill", expr);
  map.setFilter("water-line", expr);
  map.setFilter("water-sat", ["all", expr, ["==", ["get", "sat_class"], "scene_available_uncclassified"]] as FilterSpecification);
  map.setPaintProperty("water-fill", "fill-opacity", ["case", ["==", ["get", "id"], selectedId ?? ""], 0.92, 0.62]);
  map.setPaintProperty("water-line", "line-width", ["case", ["==", ["get", "id"], selectedId ?? ""], 2.4, 0.7]);
}

function buildFilter(filters: Filters, searchIds: string[] | null): FilterSpecification {
  const all: unknown[] = ["all"];
  if (searchIds) {
    all.push(["in", ["get", "id"], ["literal", searchIds]]);
  }
  if (filters.namedOnly) all.push(["==", ["get", "named"], true]);
  if (filters.hasSatellite) all.push(["==", ["get", "sat_class"], "scene_available_uncclassified"]);
  if (filters.counties.length) all.push(["in", ["get", "county"], ["literal", filters.counties]]);
  if (filters.types.length) all.push(["in", ["get", "type"], ["literal", filters.types]]);
  if (filters.iceStates.length) all.push(["in", ["get", "ice_state"], ["literal", filters.iceStates]]);
  if (filters.confidence.length) all.push(["in", ["get", "confidence"], ["literal", filters.confidence]]);
  all.push([">=", ["coalesce", ["get", "elevation_m"], 2500], filters.elevation[0]]);
  all.push(["<=", ["coalesce", ["get", "elevation_m"], 2500], filters.elevation[1]]);
  all.push([">=", ["get", "area_km2"], filters.area[0]]);
  all.push(["<=", ["get", "area_km2"], filters.area[1]]);
  all.push([">=", ["coalesce", ["get", "coverage_pct"], 0], filters.coverage[0]]);
  all.push(["<=", ["coalesce", ["get", "coverage_pct"], 100], filters.coverage[1]]);
  all.push([">=", ["coalesce", ["get", "thickness_cm"], 0], filters.thickness[0]]);
  all.push(["<=", ["coalesce", ["get", "thickness_cm"], 80], filters.thickness[1]]);
  return all as FilterSpecification;
}

export function iceStateColor(state: IceState) {
  return ICE_COLORS[state];
}
