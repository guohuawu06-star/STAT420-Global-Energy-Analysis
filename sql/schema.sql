CREATE TABLE source_release (
    release_id TEXT PRIMARY KEY,
    provider TEXT NOT NULL,
    version TEXT NOT NULL,
    source_url TEXT NOT NULL,
    retrieval_date DATE,
    sha256 TEXT NOT NULL CHECK (length(sha256) = 64)
);

CREATE TABLE geography (
    geo_id TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    iso_code TEXT UNIQUE CHECK (length(iso_code) = 3),
    geography_type TEXT NOT NULL CHECK (geography_type IN ('world', 'iso_coded', 'aggregate', 'historical', 'uncoded_entity')),
    CHECK ((geography_type = 'iso_coded' AND iso_code IS NOT NULL) OR
           (geography_type <> 'iso_coded' AND iso_code IS NULL))
);

CREATE TABLE indicator (
    indicator_id TEXT PRIMARY KEY,
    energy_category TEXT NOT NULL,
    measure TEXT NOT NULL,
    unit TEXT NOT NULL,
    accounting_method TEXT NOT NULL,
    title TEXT NOT NULL,
    source TEXT NOT NULL,
    CHECK ((measure = 'quantity' AND unit = 'TWh') OR (measure = 'share' AND unit = '%'))
);

CREATE TABLE energy_observation (
    release_id TEXT NOT NULL REFERENCES source_release(release_id),
    geo_id TEXT NOT NULL REFERENCES geography(geo_id),
    year INTEGER NOT NULL CHECK (year BETWEEN 1700 AND 2100),
    indicator_id TEXT NOT NULL REFERENCES indicator(indicator_id),
    value DOUBLE PRECISION CHECK (value >= 0),
    CHECK (indicator_id NOT LIKE '%share%' OR value <= 100),
    PRIMARY KEY (release_id, geo_id, year, indicator_id)
);
CREATE INDEX observation_indicator_year ON energy_observation (indicator_id, year);
