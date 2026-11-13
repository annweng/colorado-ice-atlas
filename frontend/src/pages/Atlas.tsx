import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { FilterPanel } from "../components/FilterPanel";
import { LakePanel } from "../components/LakePanel";
import { Legend } from "../components/Legend";
import { SafetyBanner } from "../components/SafetyBanner";
import { SearchBar } from "../components/SearchBar";
import { useAtlasData } from "../hooks/useAtlasData";
import { MapView } from "../map/MapView";
import { BASEMAPS, type BasemapId } from "../map/basemaps";

export function Atlas() {
  const data = useAtlasData();
  const [filtersOpen, setFiltersOpen] = useState(false);
  const [basemap, setBasemap] = useState<BasemapId>("streets");
  const searchIds = useMemo(() => {
    if (!data.filters.query.trim()) return null;
    return data.filtered.map((row) => row.id);
  }, [data.filters.query, data.filtered]);

  return (
    <div className="flex h-full flex-col bg-[#08111c]">
      <header className="z-20 flex flex-wrap items-center gap-3 border-b border-white/10 bg-[#08111c]/90 px-3 py-2.5 backdrop-blur md:px-4">
        <Link to="/" className="min-w-max">
          <div className="font-serif text-lg text-white md:text-xl">Colorado Ice Atlas</div>
          <div className="text-[11px] tracking-[0.18em] text-sky-200/80 uppercase">Explore. Observe. Forecast.</div>
        </Link>
        <div className="min-w-[220px] flex-1">
          <SearchBar
            value={data.filters.query}
            onChange={(query) => data.setFilters({ ...data.filters, query })}
            results={data.filtered}
            onSelect={(id) => data.setSelectedId(id)}
          />
        </div>
        <nav className="flex flex-wrap items-center gap-3 text-[13px] text-slate-300">
          <Link to="/methodology">Methodology</Link>
          <Link to="/data">Data</Link>
          <Link to="/about">About</Link>
        </nav>
      </header>
      <SafetyBanner />
      <div className="relative min-h-0 flex-1">
        {data.loading && (
          <div className="absolute inset-0 z-10 flex items-center justify-center bg-[#08111c]">
            <div className="text-slate-300">Loading statewide waterbody inventory…</div>
          </div>
        )}
        {data.error && (
          <div className="absolute inset-0 z-10 flex items-center justify-center bg-[#08111c] p-6 text-center text-red-200">
            Could not load atlas snapshots. {data.error}
          </div>
        )}
        <MapView
          filters={data.filters}
          searchIds={searchIds}
          selectedId={data.selectedId}
          onSelect={data.setSelectedId}
          basemap={basemap}
          focus={data.selected}
        />
        <div className="pointer-events-none absolute top-3 left-3 z-20 flex max-h-[calc(100%-1.5rem)] w-[min(92vw,360px)] flex-col gap-2 overflow-y-auto">
          <FilterPanel
            open={filtersOpen}
            onToggle={() => setFiltersOpen((v) => !v)}
            filters={data.filters}
            setFilters={data.setFilters}
            counties={data.counties}
            matchCount={data.filtered.length}
            onClear={data.resetFilters}
          />
          <div className="pointer-events-auto flex w-fit overflow-hidden rounded-xl border border-white/15 bg-[#0b1a2b]/90 text-[12px]">
            {(Object.keys(BASEMAPS) as BasemapId[]).map((id) => (
              <button
                key={id}
                onClick={() => setBasemap(id)}
                className={`px-3 py-2 ${basemap === id ? "bg-sky-400/20 text-white" : "text-slate-300"}`}
              >
                {BASEMAPS[id].label}
              </button>
            ))}
          </div>
          {!filtersOpen && (
            <div className="hidden w-72 md:block">
              <Legend />
            </div>
          )}
        </div>
        <div className="pointer-events-none absolute right-0 bottom-0 z-10 h-[min(78vh,720px)] w-full md:top-3 md:right-3 md:h-auto md:max-h-[calc(100%-1.5rem)] md:w-[400px]">
          {data.selected && (
            <LakePanel
              summary={data.selected}
              catalog={data.selectedCatalog}
              prediction={data.selectedPred}
              weather={data.selectedWeather}
              onClose={() => data.setSelectedId(null)}
            />
          )}
        </div>
        <div className="absolute bottom-8 left-1/2 z-10 -translate-x-1/2 rounded-full border border-white/10 bg-[#0a1624]/80 px-3 py-1 text-[11px] text-slate-300 md:left-auto md:right-24 md:translate-x-0">
          {data.filtered.length.toLocaleString()} waterbodies
          {data.meta?.as_of ? ` · estimates as of ${String(data.meta.as_of)}` : ""}
        </div>
      </div>
    </div>
  );
}
