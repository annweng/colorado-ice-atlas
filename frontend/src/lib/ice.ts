import type { CatalogItem, CompactWeather, DailyWeather, IceState, SeriesPoint, WaterbodySummary, WeatherCell } from "./types";

const ALPHA_CLEAR = 2.1;
const ALPHA_LO = 1.3;
const ALPHA_HI = 2.9;

function estimateDepth(areaKm2: number) {
  const area = Math.max(areaKm2, 0.001);
  return Math.min(35, Math.max(0.8, 1.2 + 4.5 * Math.sqrt(area)));
}

function freezeThreshold(lake: CatalogItem) {
  const area = Math.max(lake.surface_area_km2 || 0.001, 0.001);
  const depth = lake.depth_m && lake.depth_m > 0 ? lake.depth_m : estimateDepth(area);
  let threshold = 8 + 16 * Math.log1p(area) + 5.5 * Math.log1p(depth);
  const wtype = (lake.waterbody_type || "").toLowerCase();
  const desc = (lake.nhd_fcode_desc || "").toLowerCase();
  if (wtype.includes("reservoir") || desc.includes("reservoir")) threshold *= 1.15;
  if (desc.includes("intermittent") || wtype.includes("playa") || desc.includes("playa")) threshold *= 1.1;
  if (lake.elevation_m && lake.elevation_m >= 3000) threshold *= 0.92;
  return Math.min(220, Math.max(6, threshold));
}

function coveragePct(fdd: number, tddRecent: number, threshold: number, areaKm2: number, tmean: number | null, wind: number | null) {
  const excess = fdd - threshold;
  if (excess <= 0) {
    if (tmean !== null && tmean < -4 && areaKm2 < 0.05) return 12;
    return 0;
  }
  const scale = 14 + 18 * Math.log1p(areaKm2);
  let coverage = 100 * (1 - Math.exp(-excess / scale));
  coverage *= Math.exp(-tddRecent / 18);
  if (wind !== null && areaKm2 >= 4) coverage *= Math.max(0.72, 1 - 0.01 * Math.max(wind - 15, 0));
  return Math.min(100, Math.max(0, coverage));
}

function iceState(coverage: number | null, thickness: number | null, confidence: string): IceState {
  if (coverage === null || confidence === "unavailable") return "unknown";
  if (coverage < 15) return "open_water";
  if (coverage < 70) return "partial";
  if (coverage < 90 || thickness === null || thickness < 4) return "extensive";
  return "frozen";
}

export function simulateSeason(lake: CatalogItem, daily: DailyWeather[]): SeriesPoint[] {
  const threshold = freezeThreshold(lake);
  let fdd = 0;
  let tdd = 0;
  let iceOn = false;
  let fddSinceOn = 0;
  const tddWindow: number[] = [];
  let valid = 0;
  let missing = 0;
  const out: SeriesPoint[] = [];

  for (const day of daily) {
    const tm = day.tmean_c;
    if (tm === null || Number.isNaN(tm)) {
      missing += 1;
      out.push({
        date: day.date,
        is_forecast: day.is_forecast,
        tmin_c: day.tmin_c,
        tmax_c: day.tmax_c,
        tmean_c: null,
        snow_depth_m: day.snow_depth_m,
        snowfall_cm: day.snowfall_cm,
        precipitation_mm: day.precipitation_mm,
        wind_speed_kmh: day.wind_speed_kmh,
        fdd_c_day: fdd,
        tdd_c_day: tdd,
        estimated_ice_coverage: null,
        estimated_ice_thickness_cm: null,
        lower_thickness_cm: null,
        upper_thickness_cm: null,
        ice_state: "unknown",
        confidence: valid < 5 ? "unavailable" : "low",
      });
      continue;
    }
    valid += 1;
    if (tm < 0) {
      fdd += -tm;
      if (iceOn) fddSinceOn += -tm;
    } else {
      tdd += tm;
      if (iceOn) fddSinceOn = Math.max(0, fddSinceOn - 0.65 * tm);
    }
    tddWindow.push(Math.max(tm, 0));
    if (tddWindow.length > 7) tddWindow.shift();
    const tddRecent = tddWindow.reduce((a, b) => a + b, 0);
    if (!iceOn && fdd >= threshold) {
      iceOn = true;
      fddSinceOn = Math.max(fdd - threshold, 0);
    }
    const coverage = coveragePct(fdd, tddRecent, threshold, lake.surface_area_km2, tm, day.wind_speed_kmh);
    let thickness: number | null = null;
    let lower: number | null = null;
    let upper: number | null = null;
    if (iceOn && fddSinceOn > 0) {
      const snowCm = (day.snow_depth_m ?? 0) * 100;
      const windFactor = 1 + 0.04 * Math.min(Math.max((day.wind_speed_kmh ?? 0) - 8, 0), 25) / 25;
      const alpha = (ALPHA_CLEAR * windFactor) / (1 + 0.075 * snowCm);
      const alphaLo = ALPHA_LO / (1 + 0.11 * snowCm);
      const alphaHi = (ALPHA_HI * windFactor) / (1 + 0.04 * snowCm);
      thickness = alpha * Math.sqrt(fddSinceOn);
      lower = alphaLo * Math.sqrt(fddSinceOn);
      upper = alphaHi * Math.sqrt(fddSinceOn);
      if (thickness < 1) thickness = lower = upper = null;
    }
    const confidence =
      lake.depth_m == null || (lake.nhd_fcode_desc || "").toLowerCase().includes("intermittent")
        ? "moderate"
        : "high";
    out.push({
      date: day.date,
      is_forecast: day.is_forecast,
      tmin_c: day.tmin_c,
      tmax_c: day.tmax_c,
      tmean_c: tm,
      snow_depth_m: day.snow_depth_m,
      snowfall_cm: day.snowfall_cm,
      precipitation_mm: day.precipitation_mm,
      wind_speed_kmh: day.wind_speed_kmh,
      fdd_c_day: Number(fdd.toFixed(2)),
      tdd_c_day: Number(tdd.toFixed(2)),
      estimated_ice_coverage: Number(coverage.toFixed(1)),
      estimated_ice_thickness_cm: thickness === null ? null : Number(thickness.toFixed(1)),
      lower_thickness_cm: lower === null ? null : Number(lower.toFixed(1)),
      upper_thickness_cm: upper === null ? null : Number(upper.toFixed(1)),
      ice_state: iceState(coverage, thickness, confidence),
      confidence,
    });
  }
  return out;
}

export function expandWeatherCell(compact: CompactWeather, gridCellId: string): WeatherCell | null {
  const cell = compact.cells[gridCellId];
  if (!cell) return null;
  return {
    grid_cell_id: gridCellId,
    latitude: cell.latitude,
    longitude: cell.longitude,
    elevation_m: cell.elevation_m,
    source: compact.source,
    retrieved_at: compact.retrieved_at,
    daily: compact.dates.map((date, i) => ({
      date,
      is_forecast: compact.is_forecast[i] ?? false,
      tmin_c: cell.tmin_c[i] ?? null,
      tmax_c: cell.tmax_c[i] ?? null,
      tmean_c: cell.tmean_c[i] ?? null,
      precipitation_mm: cell.precipitation_mm[i] ?? null,
      snowfall_cm: cell.snowfall_cm[i] ?? null,
      wind_speed_kmh: cell.wind_speed_kmh[i] ?? null,
      shortwave_mjm2: cell.shortwave_mjm2[i] ?? null,
      snow_depth_m: cell.snow_depth_m[i] ?? null,
    })),
  };
}

export function summaryToCatalog(row: WaterbodySummary): CatalogItem {
  return {
    id: row.id,
    official_name: row.official_name,
    display_name: row.name,
    lon: row.lon,
    lat: row.lat,
    county: row.county,
    elevation_m: row.elevation_m,
    elevation_source: row.elevation_source ?? null,
    surface_area_km2: row.area_km2,
    perimeter_km: row.perimeter_km,
    waterbody_type: row.type,
    nhd_ftype: null,
    nhd_fcode_desc: row.nhd_fcode_desc ?? null,
    depth_m: row.depth_m,
    max_depth_m: row.max_depth_m ?? null,
    source: row.source ?? "Colorado OIT NHD Waterbodies (USGS NHDPlus)",
    source_identifier: row.source_identifier ?? null,
    gnis_id: row.gnis_id ?? null,
    source_feature_date: null,
    duplicate_flag: null,
    grid_cell_id: row.grid_cell_id ?? undefined,
  };
}

export function cellId(lat: number, lon: number, step = 0.25) {
  const latC = Math.floor(lat / step) * step + step / 2;
  const lonC = Math.floor(lon / step) * step + step / 2;
  return `g:${latC.toFixed(3)}:${lonC.toFixed(3)}`;
}
