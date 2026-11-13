import type { ReactNode } from "react";
import {
  Area,
  AreaChart,
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { SeriesPoint } from "../lib/types";

type Props = { series: SeriesPoint[] };

export function LakeCharts({ series }: Props) {
  if (!series.length) {
    return <p className="text-[13px] text-slate-400">No weather series is available for this lake yet.</p>;
  }
  const observed = series.filter((row) => !row.is_forecast);
  const forecastStart = series.find((row) => row.is_forecast)?.date;

  return (
    <div className="space-y-5">
      <ChartCard title="Modeled ice thickness" note="Estimate from air temperature, snow, and morphometry — not measured ice.">
        <ResponsiveContainer width="100%" height={160}>
          <AreaChart data={series} margin={{ left: 0, right: 8, top: 8, bottom: 0 }}>
            <CartesianGrid stroke="rgba(255,255,255,0.06)" />
            <XAxis dataKey="date" tick={{ fill: "#93a4b5", fontSize: 10 }} tickFormatter={shortDate} minTickGap={24} />
            <YAxis tick={{ fill: "#93a4b5", fontSize: 10 }} width={32} />
            <Tooltip contentStyle={tooltipStyle} />
            <Area dataKey="upper_thickness_cm" stroke="none" fill="#4c8fd4" fillOpacity={0.12} />
            <Area dataKey="lower_thickness_cm" stroke="none" fill="#08111c" fillOpacity={1} />
            <Line dataKey="estimated_ice_thickness_cm" stroke="#7eb8da" dot={false} strokeWidth={2} />
          </AreaChart>
        </ResponsiveContainer>
      </ChartCard>
      <ChartCard title="Modeled ice coverage" note="Percentage of the surface estimated as ice. Forecast days are included after the last observation.">
        <ResponsiveContainer width="100%" height={140}>
          <LineChart data={series}>
            <CartesianGrid stroke="rgba(255,255,255,0.06)" />
            <XAxis dataKey="date" tick={{ fill: "#93a4b5", fontSize: 10 }} tickFormatter={shortDate} minTickGap={24} />
            <YAxis domain={[0, 100]} tick={{ fill: "#93a4b5", fontSize: 10 }} width={32} />
            <Tooltip contentStyle={tooltipStyle} />
            <Line dataKey="estimated_ice_coverage" stroke="#e3c34a" dot={false} strokeWidth={2} />
          </LineChart>
        </ResponsiveContainer>
      </ChartCard>
      <ChartCard title="Air temperature" note={forecastStart ? `Solid line is analyzed weather; values after ${forecastStart} are forecast.` : "Daily mean air temperature at the assigned weather grid cell."}>
        <ResponsiveContainer width="100%" height={150}>
          <LineChart data={series}>
            <CartesianGrid stroke="rgba(255,255,255,0.06)" />
            <XAxis dataKey="date" tick={{ fill: "#93a4b5", fontSize: 10 }} tickFormatter={shortDate} minTickGap={24} />
            <YAxis tick={{ fill: "#93a4b5", fontSize: 10 }} width={32} />
            <Tooltip contentStyle={tooltipStyle} />
            <Legend />
            <Line dataKey="tmin_c" name="Min °C" stroke="#7eb8da" dot={false} />
            <Line dataKey="tmean_c" name="Mean °C" stroke="#ffffff" dot={false} />
            <Line dataKey="tmax_c" name="Max °C" stroke="#e07a3d" dot={false} />
          </LineChart>
        </ResponsiveContainer>
      </ChartCard>
      <ChartCard title="Accumulated freezing degree days" note="Sum of degrees below 0 °C from the start of the loaded weather window.">
        <ResponsiveContainer width="100%" height={130}>
          <AreaChart data={observed.length ? series : series}>
            <CartesianGrid stroke="rgba(255,255,255,0.06)" />
            <XAxis dataKey="date" tick={{ fill: "#93a4b5", fontSize: 10 }} tickFormatter={shortDate} minTickGap={24} />
            <YAxis tick={{ fill: "#93a4b5", fontSize: 10 }} width={36} />
            <Tooltip contentStyle={tooltipStyle} />
            <Area dataKey="fdd_c_day" stroke="#4c8fd4" fill="#4c8fd4" fillOpacity={0.25} />
          </AreaChart>
        </ResponsiveContainer>
      </ChartCard>
    </div>
  );
}

function ChartCard({ title, note, children }: { title: string; note: string; children: ReactNode }) {
  return (
    <div>
      <div className="mb-1 font-medium text-slate-100">{title}</div>
      <p className="mb-2 text-[11px] text-slate-400">{note}</p>
      <div className="rounded-lg border border-white/8 bg-black/20 p-1">{children}</div>
    </div>
  );
}

function shortDate(value: string) {
  return value.slice(5);
}

const tooltipStyle = {
  background: "#102033",
  border: "1px solid rgba(255,255,255,0.1)",
  fontSize: 12,
};
