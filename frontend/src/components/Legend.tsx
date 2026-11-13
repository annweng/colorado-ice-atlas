import { ICE_COLORS, ICE_LABELS, type IceState } from "../lib/types";

const STATES: IceState[] = ["open_water", "partial", "extensive", "frozen", "unknown"];

export function Legend() {
  return (
    <div className="pointer-events-auto rounded-xl border border-white/10 bg-[#0a1624]/90 p-3 shadow-xl backdrop-blur">
      <div className="mb-2 font-serif text-sm text-white">Ice state</div>
      <ul className="space-y-1 text-[12px] text-slate-200">
        {STATES.map((state) => (
          <li key={state} className="flex items-center gap-2">
            <span className="h-2.5 w-2.5 rounded-sm" style={{ background: ICE_COLORS[state] }} />
            {ICE_LABELS[state]}
          </li>
        ))}
      </ul>
      <div className="mt-3 border-t border-white/10 pt-2 text-[11px] text-slate-400">
        Colors describe modeled surface condition, not recreational safety. Dashed outlines mark lakes with a recent
        Sentinel-2 scene on file (imagery metadata, not thickness).
      </div>
    </div>
  );
}
