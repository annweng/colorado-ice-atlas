-- Colorado Ice Atlas PostGIS schema
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS pg_trgm;

CREATE TABLE IF NOT EXISTS counties (
    fips TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    geometry geometry(MultiPolygon, 4326)
);
CREATE INDEX IF NOT EXISTS counties_gix ON counties USING GIST (geometry);

CREATE TABLE IF NOT EXISTS places (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    geom geometry(Point, 4326) NOT NULL
);
CREATE INDEX IF NOT EXISTS places_gix ON places USING GIST (geom);
CREATE INDEX IF NOT EXISTS places_name_trgm ON places USING GIN (name gin_trgm_ops);

CREATE TABLE IF NOT EXISTS weather_grid_cells (
    id TEXT PRIMARY KEY,
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    geom geometry(Point, 4326) NOT NULL,
    elevation_m DOUBLE PRECISION
);

CREATE TABLE IF NOT EXISTS waterbodies (
    id TEXT PRIMARY KEY,
    official_name TEXT,
    alternative_names TEXT[],
    display_name TEXT NOT NULL,
    geometry geometry(Geometry, 4326) NOT NULL,
    centroid geometry(Point, 4326) NOT NULL,
    county TEXT,
    county_fips TEXT REFERENCES counties(fips),
    elevation_m DOUBLE PRECISION,
    elevation_source TEXT,
    surface_area_km2 DOUBLE PRECISION,
    perimeter_km DOUBLE PRECISION,
    waterbody_type TEXT,
    depth_m DOUBLE PRECISION,
    max_depth_m DOUBLE PRECISION,
    source TEXT NOT NULL,
    source_identifier TEXT,
    gnis_id TEXT,
    source_feature_date DATE,
    duplicate_flag TEXT,
    grid_cell_id TEXT REFERENCES weather_grid_cells(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS waterbodies_gix ON waterbodies USING GIST (geometry);
CREATE INDEX IF NOT EXISTS waterbodies_centroid_gix ON waterbodies USING GIST (centroid);
CREATE INDEX IF NOT EXISTS waterbodies_name_trgm ON waterbodies USING GIN (display_name gin_trgm_ops);
CREATE INDEX IF NOT EXISTS waterbodies_county_idx ON waterbodies (county);
CREATE INDEX IF NOT EXISTS waterbodies_type_idx ON waterbodies (waterbody_type);

CREATE TABLE IF NOT EXISTS weather_observations (
    id BIGSERIAL PRIMARY KEY,
    grid_cell_id TEXT NOT NULL REFERENCES weather_grid_cells(id),
    waterbody_id TEXT REFERENCES waterbodies(id),
    timestamp DATE NOT NULL,
    temperature DOUBLE PRECISION,
    minimum_temperature DOUBLE PRECISION,
    maximum_temperature DOUBLE PRECISION,
    precipitation DOUBLE PRECISION,
    snowfall DOUBLE PRECISION,
    snow_depth DOUBLE PRECISION,
    wind_speed DOUBLE PRECISION,
    solar_radiation DOUBLE PRECISION,
    is_forecast BOOLEAN NOT NULL DEFAULT FALSE,
    source TEXT NOT NULL,
    quality_metadata JSONB,
    UNIQUE (grid_cell_id, timestamp, source)
);
CREATE INDEX IF NOT EXISTS weather_obs_time_idx ON weather_observations (grid_cell_id, timestamp);

CREATE TABLE IF NOT EXISTS satellite_observations (
    id BIGSERIAL PRIMARY KEY,
    waterbody_id TEXT NOT NULL REFERENCES waterbodies(id),
    acquisition_timestamp TIMESTAMPTZ,
    ice_coverage_percentage DOUBLE PRECISION,
    classification TEXT NOT NULL,
    cloud_coverage DOUBLE PRECISION,
    quality_metadata JSONB,
    source TEXT NOT NULL,
    scene_id TEXT,
    processed_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS satellite_wb_idx ON satellite_observations (waterbody_id, acquisition_timestamp DESC);

CREATE TABLE IF NOT EXISTS ice_predictions (
    id BIGSERIAL PRIMARY KEY,
    waterbody_id TEXT NOT NULL REFERENCES waterbodies(id),
    prediction_timestamp TIMESTAMPTZ NOT NULL,
    as_of_date DATE,
    estimated_ice_coverage DOUBLE PRECISION,
    estimated_ice_thickness DOUBLE PRECISION,
    lower_thickness_estimate DOUBLE PRECISION,
    upper_thickness_estimate DOUBLE PRECISION,
    ice_state TEXT,
    confidence TEXT,
    data_quality TEXT,
    model_version TEXT NOT NULL,
    input_data_references JSONB,
    fdd_c_day DOUBLE PRECISION,
    is_stale BOOLEAN NOT NULL DEFAULT FALSE
);
CREATE INDEX IF NOT EXISTS ice_pred_wb_time_idx ON ice_predictions (waterbody_id, prediction_timestamp DESC);
CREATE INDEX IF NOT EXISTS ice_pred_state_idx ON ice_predictions (ice_state);

CREATE TABLE IF NOT EXISTS model_runs (
    id TEXT PRIMARY KEY,
    model_version TEXT NOT NULL,
    execution_timestamp TIMESTAMPTZ NOT NULL,
    ingestion_status TEXT,
    processing_status TEXT,
    execution_duration INTERVAL,
    error_details TEXT,
    waterbodies INTEGER,
    predictions INTEGER
);

CREATE TABLE IF NOT EXISTS ice_measurements (
    id BIGSERIAL PRIMARY KEY,
    waterbody_id TEXT NOT NULL REFERENCES waterbodies(id),
    measurement_coordinates geometry(Point, 4326),
    measurement_timestamp TIMESTAMPTZ NOT NULL,
    measured_thickness DOUBLE PRECISION NOT NULL,
    measurement_source TEXT NOT NULL,
    ice_type TEXT,
    supporting_metadata JSONB
);

CREATE TABLE IF NOT EXISTS data_provenance (
    id BIGSERIAL PRIMARY KEY,
    dataset TEXT NOT NULL,
    original_source TEXT NOT NULL,
    retrieval_timestamp TIMESTAMPTZ,
    processing_timestamp TIMESTAMPTZ,
    geographic_coverage TEXT,
    quality_metadata JSONB,
    units JSONB,
    methodology TEXT
);

COMMENT ON TABLE ice_predictions IS 'Modeled estimates. Never treat as field measurements.';
COMMENT ON TABLE satellite_observations IS 'Surface-scene metadata or classifications. Not ice thickness.';
COMMENT ON TABLE ice_measurements IS 'Direct in-situ ice thickness measurements.';
