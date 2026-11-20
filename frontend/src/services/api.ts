import type { CatalogItem, CompactWeather, Prediction, WaterbodySummary } from "../lib/types";

const API = import.meta.env.VITE_API_URL ?? "";

async function fetchJson<T>(path: string): Promise<T> {
  const response = await fetch(`${API}${path}`, { cache: "no-store" });
  if (!response.ok) throw new Error(`${path} failed (${response.status})`);
  return response.json() as Promise<T>;
}

export async function loadSummaries(): Promise<WaterbodySummary[]> {
  return fetchJson("/data/summaries.json");
}

export async function loadCatalog(): Promise<CatalogItem[]> {
  return fetchJson("/data/catalog.json");
}

export async function loadPredictions(): Promise<Prediction[]> {
  return fetchJson("/data/predictions.json");
}

export async function loadWeatherGrid(): Promise<CompactWeather> {
  return fetchJson("/data/weather_grid.json");
}

export async function loadMeta() {
  return fetchJson<Record<string, unknown>>("/data/meta.json");
}

export async function loadCounties() {
  return fetchJson<{ county: string; county_fips: string }[]>("/data/counties.json");
}

export async function loadCities() {
  return fetchJson<{ name: string; lat: number; lon: number }[]>("/data/cities.json");
}

export async function loadProvenance() {
  return fetchJson<Record<string, unknown>>("/data/provenance.json");
}

export async function loadSatellite() {
  return fetchJson<Record<string, unknown>[]>("/data/satellite.json");
}

export async function loadModelRun() {
  return fetchJson<Record<string, unknown>>("/data/model_run.json");
}

export async function searchApi(q: string) {
  try {
    return await fetchJson<{ items: WaterbodySummary[] }>(`/api/search?q=${encodeURIComponent(q)}`);
  } catch {
    return null;
  }
}
