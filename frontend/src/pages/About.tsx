import type { ReactNode } from "react";
import { Link } from "react-router-dom";
import { SafetyBanner } from "../components/SafetyBanner";

export function About() {
  return (
    <Doc>
      <h1 className="font-serif text-4xl text-white">Colorado Ice Atlas</h1>
      <p className="text-lg text-slate-300">Explore. Observe. Forecast.</p>
      <p>
        Colorado Ice Atlas is a public geospatial application that inventories mapped inland waterbodies in Colorado and
        estimates ice coverage and thickness from weather, lake morphometry, and satellite scene metadata.
      </p>
      <p>
        It is built as a portfolio-grade environmental information system: PostGIS-ready inventory, a FastAPI, a MapLibre
        map, a daily GitHub Actions pipeline, Docker Compose, and Terraform modules for a $0/month starting architecture
        with a documented path to GCP or AWS.
      </p>
      <h2>What this is not</h2>
      <ul>
        <li>Not an ice-safety rating, skating report, or load-capacity calculator.</li>
        <li>Not a substitute for field measurements.</li>
        <li>Not a claim that every farm pond or 3DHP micro-waterbody is included.</li>
      </ul>
      <p>
        The operational inventory is the Colorado OIT NHD waterbodies layer (USGS NHDPlus), which currently includes more
        than 7,000 lakes, ponds, reservoirs, and playas. USGS 3DHP contains a much larger set of elevation-derived
        polygons and is documented as a future ingest path.
      </p>
    </Doc>
  );
}

export function Methodology() {
  return (
    <Doc>
      <h1 className="font-serif text-4xl text-white">Methodology</h1>
      <h2>Model version stefan_snow_v0.1</h2>
      <p>
        Daily mean air temperature is accumulated as freezing degree days (FDD) below 0 °C. A freeze-over threshold rises
        with surface area and depth. After that threshold, thickness follows a Stefan √FDD form. Snow depth increases
        thermal resistance and lowers the effective Stefan coefficient. Wind on large reservoirs slightly reduces
        coverage. Thawing degree days reduce net FDD.
      </p>
      <p>
        Coverage is a separate estimate from thickness. A lake can show extensive coverage with only thin modeled ice.
        Thickness is withheld below 1 cm and whenever weather is missing. Missing inputs produce an unknown state rather
        than a fabricated number.
      </p>
      <h2>Observation classes</h2>
      <ul>
        <li>
          <strong>Direct measurements</strong> — field ice thickness. The schema exists; this release has no statewide
          in-situ network, so the class is empty until observations are contributed.
        </li>
        <li>
          <strong>Satellite observations</strong> — Sentinel-2 L2A scene intersection and cloud metadata from the
          Planetary Computer STAC. Pixel ice classification is not performed in the daily job, so scenes are not treated
          as thickness.
        </li>
        <li>
          <strong>Model estimates</strong> — coverage, thickness, and confidence from stefan_snow_v0.1.
        </li>
      </ul>
      <h2>Known biases</h2>
      <ul>
        <li>Weather is a 0.25° grid, not a lake-shore station. Alpine basins can be colder than the cell.</li>
        <li>Centroid DEM elevation is not a surveyed water-surface elevation.</li>
        <li>Most lakes lack bathymetry. Freeze-over timing then uses an area-depth heuristic.</li>
        <li>Flow-through reservoirs, aeration, and groundwater are not observed.</li>
        <li>Intermittent lakes and playas may be dry; ice is only meaningful if water is present.</li>
      </ul>
    </Doc>
  );
}

export function DataPage() {
  return (
    <Doc>
      <h1 className="font-serif text-4xl text-white">Data sources</h1>
      <ul>
        <li>Colorado OIT NHD Waterbodies — USGS NHDPlus polygons, public domain hydrography, Colorado GIS REST.</li>
        <li>Colorado Census Counties — US Census TIGER via Colorado OIT GIS.</li>
        <li>USGS 3DEP NED 10 m elevation sampled at centroids via OpenTopoData.</li>
        <li>Open-Meteo forecast and past-days weather (GFS/ECMWF blend; ERA5 attribution where applicable).</li>
        <li>Sentinel-2 L2A scene search — Microsoft Planetary Computer STAC. Raw imagery is not archived.</li>
      </ul>
      <p>
        See <code>docs/data_sources.md</code> in the repository for licensing, coverage, and why 3DHP was not the
        operational v1 inventory.
      </p>
    </Doc>
  );
}

function Doc({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-full bg-[#08111c] text-slate-200">
      <header className="border-b border-white/10 px-4 py-3">
        <Link to="/" className="font-serif text-xl text-white">
          Colorado Ice Atlas
        </Link>
      </header>
      <SafetyBanner />
      <article className="prose prose-invert mx-auto max-w-3xl px-4 py-10 [&_h2]:mt-8 [&_h2]:font-serif [&_h2]:text-2xl [&_h2]:text-white [&_li]:my-1 [&_p]:leading-relaxed [&_strong]:text-white">
        {children}
      </article>
    </div>
  );
}
