import { X } from "lucide-react";
import type { ReactNode } from "react";
import { LakeCharts } from "../charts/LakeCharts";
import { simulateSeason } from "../lib/ice";
import { ICE_COLORS, ICE_LABELS, TYPE_LABELS, type CatalogItem, type Prediction, type WaterbodySummary, type WeatherCell } from "../lib/types";
import { acres, cToF, formatNumber, metersToFeet } from "../lib/utils";

type Props = {
  summary: WaterbodySummary;
  catalog: CatalogItem | null;
  prediction: Prediction | null;
  weather: WeatherCell | null;
  onClose: () => void;
};

export function LakePanel({ summary, catalog, prediction, weather, onClose }: Props) {
  const series = catalog && weather ? simulateSeason(catalog, weather.daily) : [];
  const latestObs = [...series].reverse().find((row) => !row.is_forecast);
  const forecast = series.filter((row) => row.is_forecast).slice(0, 7);

  return (
    <aside className="pointer-events-auto flex h-full w-full flex-col overflow-hidden rounded-t-2xl border border-white/10 bg-[#0a1624]/95 shadow-2xl backdrop-blur md:rounded-2xl">
      <div className="flex items-start justify-between gap-3 border-b border-white/10 px-4 py-3">
        <div>
          <div className="font-serif text-xl leading-tight text-white">{summary.name}</div>
          <div className="mt-1 text-[12px] text-slate-400">
            {summary.county ? `${summary.county} County` : "Colorado"} · {summary.lat.toFixed(4)}, {summary.lon.toFixed(4)}
          </div>
        </div>
        <button onClick={onClose} className="rounded-lg p-1 text-slate-400 hover:bg-white/5" aria-label="Close">
          <X className="h-5 w-5" />
        </button>
      </div>
      <div className="flex-1 space-y-5 overflow-y-auto px-4 py-4 text-sm">
        <div className="flex items-center gap-2">
          <span className="h-3 w-3 rounded-sm" style={{ background: ICE_COLORS[summary.ice_state] }} />
          <span>{ICE_LABELS[summary.ice_state]}</span>
          <span className="rounded-full bg-white/8 px-2 py-0.5 text-[11px] text-slate-300">{summary.confidence}</span>
        </div>
        <p className="rounded-lg border border-amber-500/20 bg-amber-950/40 px-3 py-2 text-[12px] text-amber-100">
          These values are model estimates. They are not ice measurements and cannot establish that ice is safe to enter.
        </p>
        <Section title="Ice estimate">
          <Stat label="Coverage" value={pct(summary.coverage_pct)} />
          <Stat
            label="Thickness"
            value={
              summary.thickness_cm == null
                ? "Unavailable"
                : `${formatNumber(summary.thickness_cm, 1)} cm (${formatNumber(summary.thickness_cm / 2.54, 1)} in)`
            }
          />
          <Stat
            label="Uncertainty range"
            value={
              summary.thickness_lo_cm == null
                ? "—"
                : `${formatNumber(summary.thickness_lo_cm, 1)}–${formatNumber(summary.thickness_hi_cm, 1)} cm`
            }
          />
          <Stat label="As of" value={summary.as_of ?? "—"} />
          <Stat label="Freezing degree days" value={formatNumber(summary.fdd, 0)} />
          <Stat label="Model" value={prediction?.model_version ?? "stefan_snow_v0.1"} />
        </Section>
        <Section title="Geography">
          <Stat label="Classification" value={TYPE_LABELS[summary.type] ?? summary.type} />
          <Stat label="Elevation" value={summary.elevation_m == null ? "—" : `${formatNumber(summary.elevation_m, 0)} m (${metersToFeet(summary.elevation_m)})`} />
          <Stat label="Surface area" value={`${formatNumber(summary.area_km2, 3)} km² (${acres(summary.area_km2)})`} />
          <Stat label="Perimeter" value={`${formatNumber(summary.perimeter_km, 2)} km`} />
          <Stat
            label="Mean depth"
            value={
              catalog?.depth_m == null
                ? "Not reported in NHDPlus"
                : `${formatNumber(catalog.depth_m, 1)} m (NHDPlus MeanDepth)`
            }
          />
          <Stat label="Source id" value={catalog?.source_identifier ?? summary.id} />
        </Section>
        <Section title="Latest weather at grid cell">
          <Stat label="Air temperature" value={latestObs ? `${formatNumber(latestObs.tmean_c, 1)} °C (${cToF(latestObs.tmean_c)})` : "—"} />
          <Stat label="Min / max" value={latestObs ? `${formatNumber(latestObs.tmin_c, 1)} / ${formatNumber(latestObs.tmax_c, 1)} °C` : "—"} />
          <Stat label="Snow depth" value={latestObs?.snow_depth_m == null ? "—" : `${formatNumber(latestObs.snow_depth_m * 100, 1)} cm`} />
          <Stat label="Wind" value={latestObs?.wind_speed_kmh == null ? "—" : `${formatNumber(latestObs.wind_speed_kmh, 0)} km/h`} />
          <Stat label="Precipitation" value={latestObs?.precipitation_mm == null ? "—" : `${formatNumber(latestObs.precipitation_mm, 1)} mm`} />
          <Stat label="Weather source" value={weather?.source ? "Open-Meteo grid cell" : "Unavailable"} />
        </Section>
        {forecast.length > 0 && (
          <Section title="Seven-day weather forecast">
            {forecast.map((day) => (
              <div key={day.date} className="flex justify-between text-[12px] text-slate-300">
                <span>{day.date}</span>
                <span>
                  {formatNumber(day.tmin_c, 0)} / {formatNumber(day.tmax_c, 0)} °C
                </span>
              </div>
            ))}
            <p className="text-[11px] text-slate-400">Forecast temperatures, not observed ice. Ice charts below continue the model through this window.</p>
          </Section>
        )}
        <Section title="Satellite">
          <Stat label="Latest scene" value={summary.sat_at ?? "No low-cloud Sentinel-2 scene in the search window"} />
          <Stat label="Classification" value={summary.sat_class ? "Scene available, ice not pixel-classified" : "None"} />
          <p className="text-[11px] text-slate-400">
            Satellite data here is scene metadata. It is not a thickness measurement and is not treated as confirmation of the model.
          </p>
        </Section>
        <LakeCharts series={series} />
        <Section title="Data and methods">
          <p className="text-[12px] leading-relaxed text-slate-300">
            Inventory from Colorado OIT NHD waterbodies (USGS NHDPlus). Elevation from USGS 3DEP NED 10 m sampled at the
            centroid. Weather from Open-Meteo on a 0.25° grid. Ice from a Stefan-type model with snow insulation. Depth is
            used when NHDPlus reports it; otherwise freeze-over timing uses an area-based heuristic, which is not stored as
            measured depth.
          </p>
          {prediction?.notes?.map((note) => (
            <p key={note} className="text-[12px] text-slate-400">
              {note}
            </p>
          ))}
        </Section>
      </div>
    </aside>
  );
}

function Section({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section>
      <h3 className="mb-2 font-serif text-base text-white">{title}</h3>
      <div className="space-y-1.5">{children}</div>
    </section>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-baseline justify-between gap-4">
      <span className="text-[12px] text-slate-400">{label}</span>
      <span className="text-right text-[13px] text-slate-100">{value}</span>
    </div>
  );
}

function pct(value: number | null) {
  return value == null ? "—" : `${formatNumber(value, 0)}%`;
}
