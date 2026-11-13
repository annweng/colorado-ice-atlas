import { useEffect, useMemo, useState } from "react";
import { expandWeatherCell, summaryToCatalog } from "../lib/ice";
import { haystack, nameScore, significantTokens } from "../lib/search";
import type { CompactWeather, Filters, IceState, WaterbodySummary } from "../lib/types";
import { loadCities, loadCounties, loadMeta, loadSummaries, loadWeatherGrid } from "../services/api";

const defaultFilters: Filters = {
  query: "",
  counties: [],
  types: [],
  iceStates: [],
  confidence: [],
  namedOnly: false,
  elevation: [1000, 4400],
  area: [0, 70],
  coverage: [0, 100],
  thickness: [0, 80],
  hasSatellite: false,
};

export function useAtlasData() {
  const [summaries, setSummaries] = useState<WaterbodySummary[]>([]);
  const [weather, setWeather] = useState<CompactWeather | null>(null);
  const [counties, setCounties] = useState<string[]>([]);
  const [cities, setCities] = useState<{ name: string; lat: number; lon: number }[]>([]);
  const [meta, setMeta] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState<Filters>(defaultFilters);
  const [selectedId, setSelectedId] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    Promise.all([loadSummaries(), loadCounties(), loadCities(), loadMeta()])
      .then(([s, co, ci, m]) => {
        if (cancelled) return;
        setSummaries(s);
        setCounties(co.map((row) => row.county).sort());
        setCities(ci);
        setMeta(m);
        setLoading(false);
      })
      .catch((err: Error) => {
        if (cancelled) return;
        setError(err.message);
        setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (!selectedId || weather) return;
    loadWeatherGrid()
      .then(setWeather)
      .catch(() => setWeather(null));
  }, [selectedId, weather]);

  const filtered = useMemo(() => {
    const q = filters.query.trim().toLowerCase();
    const rows = summaries.filter((row) => {
      if (q) {
        const blob = `${haystack(row)} ${row.id}`.toLowerCase();
        const tokens = significantTokens(q);
        const coord = q.match(/^(-?\d+(\.\d+)?)[,\s]+(-?\d+(\.\d+)?)$/);
        if (coord) {
          const lat = Number(coord[1]);
          const lon = Number(coord[3]);
          const dlat = row.lat - lat;
          const dlon = row.lon - lon;
          if (dlat * dlat + dlon * dlon > 0.08) return false;
        } else if (blob.includes(q) || (tokens.length > 0 && tokens.every((token) => blob.includes(token)))) {
          // name, alias, county, or all significant tokens
        } else {
          const city = cities.find(
            (c) => c.name.toLowerCase().includes(q) || tokens.some((token) => c.name.toLowerCase() === token),
          );
          if (!city) return false;
          const dlat = row.lat - city.lat;
          const dlon = row.lon - city.lon;
          if (dlat * dlat + dlon * dlon > 0.35) return false;
        }
      }
      if (filters.counties.length && !filters.counties.includes(row.county ?? "")) return false;
      if (filters.types.length && !filters.types.includes(row.type)) return false;
      if (filters.iceStates.length && !filters.iceStates.includes(row.ice_state as IceState)) return false;
      if (filters.confidence.length && !filters.confidence.includes(row.confidence)) return false;
      if (filters.namedOnly && !row.named) return false;
      if (row.elevation_m !== null && (row.elevation_m < filters.elevation[0] || row.elevation_m > filters.elevation[1])) return false;
      if (row.area_km2 < filters.area[0] || row.area_km2 > filters.area[1]) return false;
      if (row.coverage_pct !== null && (row.coverage_pct < filters.coverage[0] || row.coverage_pct > filters.coverage[1])) return false;
      if (row.thickness_cm !== null && (row.thickness_cm < filters.thickness[0] || row.thickness_cm > filters.thickness[1])) return false;
      if (filters.hasSatellite && !row.sat_class) return false;
      return true;
    });
    if (!q) return rows;
    const score = (row: WaterbodySummary) => {
      const value = nameScore(q, row);
      return value || 40;
    };
    return [...rows].sort((a, b) => score(b) - score(a) || b.area_km2 - a.area_km2);
  }, [summaries, filters, cities]);

  const selected = selectedId ? summaries.find((row) => row.id === selectedId) ?? null : null;
  const selectedCatalog = selected ? summaryToCatalog(selected) : null;
  const selectedWeather =
    selected && weather ? expandWeatherCell(weather, selected.grid_cell_id || cellFallback(selected)) : null;
  const selectedPred = selected
    ? {
        waterbody_id: selected.id,
        prediction_timestamp: String(meta?.generated_at ?? ""),
        as_of_date: selected.as_of,
        estimated_ice_coverage: selected.coverage_pct,
        estimated_ice_thickness_cm: selected.thickness_cm,
        lower_thickness_estimate_cm: selected.thickness_lo_cm,
        upper_thickness_estimate_cm: selected.thickness_hi_cm,
        ice_state: selected.ice_state,
        confidence: selected.confidence,
        data_quality: selected.depth_m == null ? "depth_estimated" : "ok",
        model_version: String(meta?.model_version ?? "stefan_snow_v0.1"),
        fdd_c_day: selected.fdd,
        notes: selected.depth_m == null ? ["Mean depth is estimated from surface area; it is not bathymetry."] : [],
        methodology:
          "Accumulated freezing degree days and Stefan-type thickness after a morphometry-dependent freeze-over threshold.",
        input_data_references: {},
      }
    : null;

  return {
    loading,
    error,
    summaries,
    filtered,
    filters,
    setFilters,
    resetFilters: () => setFilters(defaultFilters),
    counties,
    cities,
    meta,
    selected,
    selectedCatalog,
    selectedPred,
    selectedWeather,
    selectedId,
    setSelectedId,
  };
}

function cellFallback(lake: WaterbodySummary) {
  const step = 0.25;
  const latC = Math.floor(lake.lat / step) * step + step / 2;
  const lonC = Math.floor(lake.lon / step) * step + step / 2;
  return `g:${latC.toFixed(3)}:${lonC.toFixed(3)}`;
}
