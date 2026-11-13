import type { StyleSpecification } from "maplibre-gl";

export type BasemapId = "streets" | "satellite" | "terrain";

function rasterStyle(id: string, tiles: string[], attribution: string): StyleSpecification {
  return {
    version: 8,
    sources: {
      [id]: {
        type: "raster",
        tiles,
        tileSize: 256,
        attribution,
        maxzoom: 19,
      },
    },
    layers: [{ id, type: "raster", source: id }],
  };
}

export const BASEMAPS: Record<
  BasemapId,
  { label: string; style: string | StyleSpecification; attribution: string }
> = {
  streets: {
    label: "Streets",
    style: rasterStyle(
      "esri-streets",
      ["https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}"],
      "Tiles © Esri — Esri, TomTom, Garmin, FAO, NOAA, USGS. Powered by Esri.",
    ),
    attribution: "Powered by Esri. Street map © Esri, TomTom, Garmin, FAO, NOAA, USGS.",
  },
  satellite: {
    label: "Satellite",
    style: rasterStyle(
      "esri",
      ["https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"],
      "Tiles © Esri — Source: Esri, Maxar, Earthstar Geographics, and the GIS User Community. Powered by Esri.",
    ),
    attribution: "Powered by Esri. Imagery © Esri, Maxar, Earthstar Geographics.",
  },
  terrain: {
    label: "Terrain",
    style: rasterStyle(
      "topo",
      ["https://tile.opentopomap.org/{z}/{x}/{y}.png"],
      "Map data © OpenStreetMap contributors, SRTM | Map style © OpenTopoMap (CC-BY-SA)",
    ),
    attribution: "© OpenStreetMap contributors, SRTM | © OpenTopoMap (CC-BY-SA)",
  },
};

export const COLORADO_CENTER: [number, number] = [-105.5, 39.0];
export const COLORADO_BOUNDS: [[number, number], [number, number]] = [
  [-113.4, 34.6],
  [-98.6, 43.2],
];
