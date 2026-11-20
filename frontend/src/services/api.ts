import { assetUrl } from "../lib/paths";
import type { CatalogItem, CompactWeather, Prediction, WaterbodySummary } from "../lib/types";

const API = import.meta.env.VITE_API_URL ?? "";

async function fetchJson<T>(path: string): Promise<T> {
  const response = await fetch(`${API}${path}`, { cache: "no-store" });
  if (!response.ok) throw new Error(`${path} failed (${response.status})`);
  return response.json() as Promise<T>;
}

export async function loadSummaries(): Promise<WaterbodySummary[]> {
  return fetchJson(assetUrl("data/summaries.json"));
}

export async function loadCatalog(): Promise<CatalogItem[]> {
  return fetchJson(assetUrl("data/catalog.json"));
}

export async function loadPredictions(): Promise<Prediction[]> {
  return fetchJson(assetUrl("data/predictions.json"));
}

export async function loadWeatherGrid(): Promise<CompactWeather> {
  return fetchJson(assetUrl("data/weather_grid.json"));
}

export async function loadMeta() {
  return fetchJson<Record<string, unknown>>(assetUrl("data/meta.json"));
}

export async function loadCounties() {
  return fetchJson<{ county: string; county_fips: string }[]>(assetUrl("data/counties.json"));
}

export async function loadCities() {
  return fetchJson<{ name: string; lat: number; lon: number }[]>(assetUrl("data/cities.json"));
}

export async function loadProvenance() {
  return fetchJson<Record<string, unknown>>(assetUrl("data/provenance.json"));
}

export async function loadSatellite() {
  return fetchJson<Record<string, unknown>[]>(assetUrl("data/satellite.json"));
}

export async function loadModelRun() {
  return fetchJson<Record<string, unknown>>(assetUrl("data/model_run.json"));
}

export async function searchApi(q: string) {
  try {
    return await fetchJson<{ items: WaterbodySummary[] }>(`/api/search?q=${encodeURIComponent(q)}`);
  } catch {
    return null;
  }
}
