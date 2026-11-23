# Data and database

## Sources, measures, and attribution

| Source | Role |
| --- | --- |
| [OWID Energy dataset](https://catalog.ourworldindata.org/energy/owid_energy/) and [upstream repository](https://github.com/owid/energy-data) | Analysis input and indicator documentation. The pipeline downloads the [September 10, 2026 CSV](https://catalog.ourworldindata.org/garden/energy/2026-09-10/owid_energy/owid_energy.csv) and verifies its SHA-256 hash. |
| Energy Institute (2026), [*Statistical Review of World Energy*](https://www.energyinst.org/statistical-review/resources-and-data-downloads) | Upstream energy data and accounting methodology. The analysis uses the series as processed by OWID. |
| Hannah Ritchie (2021), [*How have the world's energy sources changed over the last two centuries?*](https://ourworldindata.org/global-energy-200-years) | Historical context. Its series are outside the fitted panel. |

OWID's catalog credits the Energy Institute, Vaclav Smil's *Energy Transitions: Global and National Perspectives* (2017), and the U.S. Energy Information Administration's *International Energy Data* (2026) for the selected indicators. The published artifacts are the project's original figures and compact summaries, with attribution to OWID and the underlying providers. Original source files, database dumps, and full extracts are regenerated locally. OWID applies its [license terms](https://catalog.ourworldindata.org/energy/owid_energy/#license) to its own work and identifies third-party sources separately. The [Energy Institute review](https://www.energyinst.org/?a=1822009) provides attribution and reuse guidance for its data.

The seven [selected fields](../data/metadata/data_dictionary.csv) use total energy supply: one annual quantity in TWh and six source shares in percent. This release uses the energy supply accounting documented in the OWID catalog. Electricity generation, final consumption, older substitution-method primary energy series, and per-capita metrics use different definitions. The pipeline takes a single OWID release and does not join the EI workbook or the historical article's chart series. Fossil fuels include coal, oil, and natural gas, so the combined fossil share is not added to those component shares.

## Workflow and validation

1. Download the fixed CSV and verify the checksum in `src/config.py`. The generated manifest records the URL, CSV format, release, byte count, hash, acquisition time when known, and verification time. See the [publication run's manifest](source_snapshot.json).
2. Profile all columns for missing and observed values, distinct values, types, and numeric ranges. Profile geographic and annual coverage. The source has 19,494 rows, 130 fields, and 260 geographic labels over 1700–2025. There were zero duplicate geography–year pairs, exact duplicate rows, or missing geography/year keys.
3. Keep the raw geography label and use its ISO code where supplied (220 locations, including territories). Assign a documented `OWID:` key to the [40 uncoded labels](../data/metadata/uncoded_geographies.csv), which include World, regional or membership aggregates, historical entities, and Kosovo. Use World directly and restrict country comparisons to four explicit ISO codes.
4. Validate the seven selected fields against the project data dictionary and reject invalid numeric values, negative quantities, and shares over 100%. Reshape from wide columns to long observations. Preserve recorded zeros and blank cells as explicit nulls, with no imputation or unit conversion. See the [indicator quality summary](../results/data_quality_summary.csv).
5. Load four CSVs in dependency order inside one transaction. PostgreSQL enforces primary, foreign, and uniqueness keys during COPY. The loader counts rows and runs the analytical queries before committing. A failed load rolls back the table replacements.
6. Export World, selected-country, and coverage queries. From 2000 forward, the analytical panel ends at the last consecutive year with complete coverage for all seven indicators and all five locations. This yields 910 values across 26 years. Report sample counts, means, sample standard deviations, medians, extrema, and endpoint changes by location and unit. Fit ordinary least squares to world renewable share versus year centered at 2000. Report in-sample fit and inspect residuals by year and fitted value.

## Relationships

| Table | Grain and keys |
| --- | --- |
| `source_release` | One upstream release per `release_id`, plus provider, version, URL, acquisition date when known, and checksum. |
| `geography` | One location per `geo_id`, with a unique name, an optional unique ISO code, and a geography type. |
| `indicator` | One metric per `indicator_id`, with category, measure, unit, accounting method, title, and source. |
| `energy_observation` | One slot per `(release_id, geo_id, year, indicator_id)`. Three foreign keys reference the lookup tables above. The value can be null. |

The [relationship diagram](data_model.mmd) shows the three one-to-many relationships. The [workflow diagram](data_flow.mmd) shows the processing stages. After connecting with `psql`, run `SET search_path TO stat420_energy;` and then `\i sql/queries.sql` from the project root to inspect the example queries.

The [live database run](../results/database_run.json) recorded 136,458 observation slots, of which 50,406 contain values and 86,052 are null. Observed values include 9,596 zeros. [Backup and restore verification](../results/postgres_restore_check.json) confirms the fact row count after restoration.
