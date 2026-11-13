import { Search, X } from "lucide-react";
import { useMemo, useState } from "react";
import type { WaterbodySummary } from "../lib/types";

type Props = {
  value: string;
  onChange: (value: string) => void;
  results: WaterbodySummary[];
  onSelect: (id: string) => void;
};

export function SearchBar({ value, onChange, results, onSelect }: Props) {
  const [open, setOpen] = useState(false);
  const shown = useMemo(() => results.slice(0, 8), [results]);

  return (
    <div className="relative w-full max-w-xl">
      <Search className="pointer-events-none absolute top-1/2 left-3 h-4 w-4 -translate-y-1/2 text-slate-400" />
      <input
        value={value}
        onChange={(e) => {
          onChange(e.target.value);
          setOpen(true);
        }}
        onFocus={() => setOpen(true)}
        placeholder="Search lakes, counties, towns, or lat, lon"
        className="w-full rounded-xl border border-white/15 bg-[#0b1a2b]/90 py-2.5 pr-10 pl-10 text-sm text-white outline-none placeholder:text-slate-400 focus:border-sky-400/60"
      />
      {value && (
        <button
          className="absolute top-1/2 right-3 -translate-y-1/2 text-slate-400"
          onClick={() => {
            onChange("");
            setOpen(false);
          }}
          aria-label="Clear search"
        >
          <X className="h-4 w-4" />
        </button>
      )}
      {open && value && shown.length > 0 && (
        <ul className="absolute z-20 mt-2 w-full overflow-hidden rounded-xl border border-white/10 bg-[#0b1a2b] shadow-2xl">
          {shown.map((row) => (
            <li key={row.id}>
              <button
                className="flex w-full flex-col items-start px-3 py-2 text-left hover:bg-white/5"
                onClick={() => {
                  onSelect(row.id);
                  onChange(row.name);
                  setOpen(false);
                }}
              >
                <span className="text-sm text-white">{row.name}</span>
                <span className="text-[11px] text-slate-400">
                  {row.county ? `${row.county} County` : "Colorado"} · {row.area_km2.toFixed(2)} km²
                </span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
