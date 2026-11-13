import type { StyleSpecification } from "maplibre-gl";

export type BasemapId = "streets" | "satellite" | "terrain";

export const BASEMAPS: Record<
  BasemapId,
  { label: string; style: string | StyleSpecification; attribution: string }
> = {
  streets: {
    label: "Streets",
    style: "https://tiles.openfreemap.org/styles/liberty",
    attribution: "OpenFreeMap © OpenMapTiles © OpenStreetMap contributors",
  },
  satellite: {
    label: "Satellite",
    style: {
      version: 8,
      sources: {
        esri: {
          type: "raster",
          tiles: [
            "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
          ],
          tileSize: 256,
          attribution:
            "Tiles © Esri — Source: Esri, Maxar, Earthstar Geographics, and the GIS User Community. Powered by Esri.",
        },
      },
      layers: [{ id: "esri", type: "raster", source: "esri" }],
    },
    attribution: "Powered by Esri. Imagery © Esri, Maxar, Earthstar Geographics.",
  },
  terrain: {
    label: "Terrain",
    style: {
      version: 8,
      sources: {
        topo: {
          type: "raster",
          tiles: ["https://tile.opentopomap.org/{z}/{x}/{y}.png"],
          tileSize: 256,
          attribution:
            "Map data © OpenStreetMap contributors, SRTM | Map style © OpenTopoMap (CC-BY-SA)",
        },
      },
      layers: [{ id: "topo", type: "raster", source: "topo" }],
    },
    attribution: "© OpenStreetMap contributors, SRTM | © OpenTopoMap (CC-BY-SA)",
  },
};

export const COLORADO_CENTER: [number, number] = [-105.5, 39.0];
export const COLORADO_BOUNDS: [[number, number], [number, number]] = [
  [-109.2, 36.8],
  [-101.9, 41.1],
];
