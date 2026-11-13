export type IceState = "open_water" | "partial" | "extensive" | "frozen" | "unknown";

export type WaterbodySummary = {
  id: string;
  name: string;
  official_name: string | null;
  county: string | null;
  lat: number;
  lon: number;
  elevation_m: number | null;
  area_km2: number;
  perimeter_km: number;
  type: string;
  depth_m: number | null;
  ice_state: IceState;
  coverage_pct: number | null;
  thickness_cm: number | null;
  thickness_lo_cm: number | null;
  thickness_hi_cm: number | null;
  confidence: string;
  fdd: number | null;
  as_of: string | null;
  sat_class: string | null;
  sat_at: string | null;
  named: boolean;
  alternative_names?: string[] | null;
  name_source?: string | null;
  bbox?: [number, number, number, number] | number[] | null;
  gnis_id?: string | null;
  source_identifier?: string | null;
  grid_cell_id?: string | null;
  nhd_fcode_desc?: string | null;
  source?: string | null;
  elevation_source?: string | null;
  max_depth_m?: number | null;
};

export type CatalogItem = {
  id: string;
  official_name: string | null;
  display_name: string;
  lon: number;
  lat: number;
  county: string | null;
  elevation_m: number | null;
  elevation_source: string | null;
  surface_area_km2: number;
  perimeter_km: number;
  waterbody_type: string;
  nhd_ftype: string | null;
  nhd_fcode_desc: string | null;
  depth_m: number | null;
  max_depth_m: number | null;
  source: string;
  source_identifier: string | null;
  gnis_id: string | null;
  source_feature_date: string | null;
  duplicate_flag: string | null;
  grid_cell_id?: string;
};

export type DailyWeather = {
  date: string;
  is_forecast: boolean;
  tmin_c: number | null;
  tmax_c: number | null;
  tmean_c: number | null;
  precipitation_mm: number | null;
  snowfall_cm: number | null;
  wind_speed_kmh: number | null;
  shortwave_mjm2: number | null;
  snow_depth_m: number | null;
};

export type WeatherCell = {
  grid_cell_id: string;
  latitude: number;
  longitude: number;
  elevation_m: number | null;
  source: string;
  retrieved_at: string;
  daily: DailyWeather[];
};

export type CompactWeather = {
  source: string;
  retrieved_at: string;
  dates: string[];
  is_forecast: boolean[];
  cells: Record<
    string,
    {
      latitude: number;
      longitude: number;
      elevation_m: number | null;
      tmin_c: Array<number | null>;
      tmax_c: Array<number | null>;
      tmean_c: Array<number | null>;
      precipitation_mm: Array<number | null>;
      snowfall_cm: Array<number | null>;
      wind_speed_kmh: Array<number | null>;
      shortwave_mjm2: Array<number | null>;
      snow_depth_m: Array<number | null>;
    }
  >;
};

export type Prediction = {
  waterbody_id: string;
  prediction_timestamp: string;
  as_of_date: string | null;
  estimated_ice_coverage: number | null;
  estimated_ice_thickness_cm: number | null;
  lower_thickness_estimate_cm: number | null;
  upper_thickness_estimate_cm: number | null;
  ice_state: IceState;
  confidence: string;
  data_quality: string;
  model_version: string;
  fdd_c_day: number | null;
  tdd_c_day?: number | null;
  notes: string[];
  methodology: string;
  input_data_references: Record<string, unknown>;
};

export type SeriesPoint = {
  date: string;
  is_forecast: boolean;
  tmin_c: number | null;
  tmax_c: number | null;
  tmean_c: number | null;
  snow_depth_m: number | null;
  snowfall_cm: number | null;
  precipitation_mm: number | null;
  wind_speed_kmh: number | null;
  fdd_c_day: number;
  tdd_c_day: number;
  estimated_ice_coverage: number | null;
  estimated_ice_thickness_cm: number | null;
  lower_thickness_cm: number | null;
  upper_thickness_cm: number | null;
  ice_state: IceState;
  confidence: string;
};

export type Filters = {
  query: string;
  counties: string[];
  types: string[];
  iceStates: IceState[];
  confidence: string[];
  namedOnly: boolean;
  elevation: [number, number];
  area: [number, number];
  coverage: [number, number];
  thickness: [number, number];
  hasSatellite: boolean;
};

export const ICE_COLORS: Record<IceState, string> = {
  open_water: "#d64545",
  partial: "#e07a3d",
  extensive: "#e3c34a",
  frozen: "#4c8fd4",
  unknown: "#8b919a",
};

export const ICE_LABELS: Record<IceState, string> = {
  open_water: "Predominantly open water",
  partial: "Partial ice coverage",
  extensive: "Extensive ice / uncertain",
  frozen: "Model-estimated predominantly frozen",
  unknown: "Insufficient information",
};

export const TYPE_LABELS: Record<string, string> = {
  lake_pond: "Lake / pond",
  intermittent_lake_pond: "Intermittent lake / pond",
  reservoir: "Reservoir",
  playa: "Playa",
};
