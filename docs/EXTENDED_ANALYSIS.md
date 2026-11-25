# Geographic and historical analysis

Both extensions use the fixed OWID Energy release and run in [Completed Analysis](../notebooks/Completed_Analysis.ipynb). See the [README](../README.md#extended-notebook-and-html) for execution and export instructions.

## Geographic reporting

The tabular panel includes 220 ISO-coded OWID locations, including territories and historical labels. A location-year is **Reported** if its total energy supply field contains a value, including zero. It is **Missing** if OWID supplies the location-year row and the total field is empty. **Outside source grid** means the release contains no row and the project cannot assess applicability. These are data classifications. They do not infer sovereignty, legal existence, or historic land boundaries. A location can report total supply and lack a renewable share.

The broad comparison ends in 2024. Total supply is reported for 218 locations in 2024 and 79 in 2025. All seven indicators for the five core study locations are available through 2025. [Yearly tabular counts](../results/geographic_coverage.csv) include every ISO-coded location and are independently reconciled with the source and SQL export.

The animations cover 1965–2024. The 2024 snapshot and renewable-share animation display reported shares on a 0–100% scale. The supply availability map uses three colors for the source statuses. Maps use the contemporary Natural Earth 1:50m outlines served by Plotly.js. The [checked map identifiers](../data/metadata/plotly_world_50m.json) match 213 locations. Seven location IDs remain in the tables without polygons in the chosen map. They are ANT (Netherlands Antilles), GIB (Gibraltar), GLP (Guadeloupe), GUF (French Guiana), MTQ (Martinique), REU (Réunion), and TUV (Tuvalu). The modern outlines can group some territories into another geometry. See the [Plotly basemap documentation](https://plotly.com/blog/improved-map-accuracy-plotlyjs-un-geodata/) and [Natural Earth terms](https://www.naturalearthdata.com/about/terms-of-use/).

## Historical World series

The historical charts use nine individual source quantities from the published World series. Aggregate fossil, renewable, and low-carbon series are excluded from the stacks. Sums require all relevant components. The 78 complete observation years are decadal from 1800 through 1960 and annual from 1965 through 2025. Bars and animation frames appear only for observed years.

The sum of five renewable components agrees with the published renewable quantity to within 0.001 TWh. This threshold allows for small differences in the recorded numerical precision. The largest absolute difference between the nine-component sum and published total is 126.392334 TWh in 2022, around 0.08% of the published total. Its cause remains unresolved. The charts show the published total alongside the component bars at the original value. See the [checks](../results/extension_verification.json) and [source attribution](DATA_AND_DATABASE.md#sources-measures-and-attribution).
