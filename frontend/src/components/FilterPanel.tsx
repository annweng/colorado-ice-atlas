import { SlidersHorizontal, X } from "lucide-react";
import type { ReactNode } from "react";
import type { Filters, IceState } from "../lib/types";
import { ICE_LABELS, TYPE_LABELS } from "../lib/types";

type Props = {
  open: boolean;
  onToggle: () => void;
  filters: Filters;
  setFilters: (next: Filters) => void;
  counties: string[];
  matchCount: number;
  onClear: () => void;
};

const STATES: IceState[] = ["open_water", "partial", "extensive", "frozen", "unknown"];

export function FilterPanel({ open, onToggle, filters, setFilters, counties, matchCount, onClear }: Props) {
  return (
    <div className="pointer-events-auto">
      <button
        onClick={onToggle}
        className="mb-2 inline-flex items-center gap-2 rounded-xl border border-white/15 bg-[#0b1a2b]/90 px-3 py-2 text-sm text-white"
      >
        <SlidersHorizontal className="h-4 w-4" />
        Filters
      </button>
      {open && (
        <div className="max-h-[min(70vh,calc(100dvh-9rem))] w-full overflow-y-auto rounded-xl border border-white/10 bg-[#0a1624]/95 p-3 text-sm shadow-2xl backdrop-blur">
          <div className="mb-3 flex items-center justify-between">
            <div className="font-serif">Filter waterbodies</div>
            <button onClick={onToggle} aria-label="Close filters">
              <X className="h-4 w-4" />
            </button>
          </div>
          <p className="mb-3 text-[12px] text-slate-400">
            {matchCount.toLocaleString()} {matchCount === 1 ? "lake matches" : "lakes match"}
          </p>
          <label className="mb-3 flex items-center gap-2 text-[13px]">
            <input
              type="checkbox"
              checked={filters.namedOnly}
              onChange={(e) => setFilters({ ...filters, namedOnly: e.target.checked })}
            />
            Named lakes only
          </label>
          <label className="mb-3 flex items-center gap-2 text-[13px]">
            <input
              type="checkbox"
              checked={filters.hasSatellite}
              onChange={(e) => setFilters({ ...filters, hasSatellite: e.target.checked })}
            />
            Has recent Sentinel-2 scene
          </label>
          <Field label="Ice state">
            {STATES.map((state) => (
              <Chip
                key={state}
                active={filters.iceStates.includes(state)}
                onClick={() => toggle(filters.iceStates, state, (iceStates) => setFilters({ ...filters, iceStates }))}
              >
                {ICE_LABELS[state]}
              </Chip>
            ))}
          </Field>
          <Field label="Type">
            {Object.entries(TYPE_LABELS).map(([value, label]) => (
              <Chip
                key={value}
                active={filters.types.includes(value)}
                onClick={() => toggle(filters.types, value, (types) => setFilters({ ...filters, types }))}
              >
                {label}
              </Chip>
            ))}
          </Field>
          <Field label="County">
            <select
              className="w-full rounded-lg border border-white/15 bg-[#08111c] px-2 py-1.5 text-[13px]"
              value={filters.counties[0] ?? ""}
              onChange={(e) => setFilters({ ...filters, counties: e.target.value ? [e.target.value] : [] })}
            >
              <option value="">All counties</option>
              {counties.map((county) => (
                <option key={county} value={county}>
                  {county}
                </option>
              ))}
            </select>
          </Field>
          <Range
            label="Elevation (m)"
            min={1000}
            max={4400}
            step={50}
            value={filters.elevation}
            onChange={(elevation) => setFilters({ ...filters, elevation })}
          />
          <Range
            label="Surface area (km²)"
            min={0}
            max={70}
            step={0.1}
            value={filters.area}
            onChange={(area) => setFilters({ ...filters, area })}
          />
          <Range
            label="Modeled ice coverage (%)"
            min={0}
            max={100}
            step={1}
            value={filters.coverage}
            onChange={(coverage) => setFilters({ ...filters, coverage })}
          />
          <Range
            label="Modeled thickness (cm)"
            min={0}
            max={80}
            step={1}
            value={filters.thickness}
            onChange={(thickness) => setFilters({ ...filters, thickness })}
          />
          <Field label="Confidence">
            {["high", "moderate", "low", "unavailable"].map((value) => (
              <Chip
                key={value}
                active={filters.confidence.includes(value)}
                onClick={() => toggle(filters.confidence, value, (confidence) => setFilters({ ...filters, confidence }))}
              >
                {value}
              </Chip>
            ))}
          </Field>
          <button
            onClick={onClear}
            className="mt-2 w-full rounded-lg border border-white/15 py-2 text-[13px] text-slate-200"
          >
            Clear filters
          </button>
        </div>
      )}
    </div>
  );
}

function Field({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className="mb-3">
      <div className="mb-1.5 text-[11px] tracking-wide text-slate-400 uppercase">{label}</div>
      <div className="flex flex-wrap gap-1.5">{children}</div>
    </div>
  );
}

function Chip({ active, onClick, children }: { active: boolean; onClick: () => void; children: ReactNode }) {
  return (
    <button
      onClick={onClick}
      className={`rounded-full px-2 py-1 text-[11px] ${active ? "bg-sky-400/20 text-sky-100" : "bg-white/5 text-slate-300"}`}
    >
      {children}
    </button>
  );
}

function Range({
  label,
  min,
  max,
  step,
  value,
  onChange,
}: {
  label: string;
  min: number;
  max: number;
  step: number;
  value: [number, number];
  onChange: (value: [number, number]) => void;
}) {
  return (
    <div className="mb-3">
      <div className="mb-1 flex justify-between text-[11px] text-slate-400">
        <span className="uppercase">{label}</span>
        <span>
          {value[0]} – {value[1]}
        </span>
      </div>
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value[0]}
        onChange={(e) => onChange([Number(e.target.value), value[1]])}
        className="w-full"
      />
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value[1]}
        onChange={(e) => onChange([value[0], Number(e.target.value)])}
        className="w-full"
      />
    </div>
  );
}

function toggle<T>(list: T[], value: T, write: (next: T[]) => void) {
  write(list.includes(value) ? list.filter((item) => item !== value) : [...list, value]);
}
