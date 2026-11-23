# Changes in Global Energy

STAT 420 · Data Curation and Management · San Diego State University
Instructor: Ryan Paul Lafler

This project examines changes in global energy use through the annual **total energy supply** and source shares in a fixed Our World in Data (OWID) release. Its analysis covers the World series and China, India, Germany, and the United States from 2000 through 2025.

## Research questions

1. How much did world total energy supply change over the study period?
2. How did the shares of coal, oil, natural gas, nuclear energy, and renewables change?
3. How did total energy supply and fossil fuel shares change across the four selected countries?
4. How well does a straight line describe the change in the world renewable share over this period?

## Reproduce the analysis

Install Python 3.11 and either Docker with the Compose plugin or a local PostgreSQL instance. Clone the repository and run the commands from its root.

```bash
git clone https://github.com/guohuawu06-star/STAT420-Global-Energy-Analysis.git
cd STAT420-Global-Energy-Analysis
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pip check
```

In Windows PowerShell, use `. ./.venv/Scripts/Activate.ps1` in place of `source`. If you already have Docker Engine in the WSL Ubuntu distribution, run `pwsh -NoProfile -File src/run_postgres_wsl.ps1` in the activated environment. The helper starts PostgreSQL, runs the pipeline and checks a backup restore, then removes its temporary container. It needs port 55420 free and keeps the dump locally.

For Docker Compose in a POSIX shell, run the following. Compose waits for the database health check and binds port 55420 to loopback only.

```bash
export STAT420_DB_PASSWORD="$(python -c 'import secrets; print(secrets.token_urlsafe(24))')"
export PGHOST=127.0.0.1 PGPORT=55420 PGUSER=stat420 PGDATABASE=stat420_energy
export PGPASSWORD="$STAT420_DB_PASSWORD"
docker compose up -d --wait
python -m src.run_pipeline --db postgres
docker compose down
unset STAT420_DB_PASSWORD PGPASSWORD
```

For an existing PostgreSQL instance, set the standard `PGHOST`, `PGPORT`, `PGUSER`, `PGDATABASE`, and `PGPASSWORD` variables as appropriate and run the same pipeline command. Use a dedicated project database. Each run replaces the four project tables in the `stat420_energy` schema within a transaction.

After the pipeline, execute the tests and verify the notebook:

```bash
python -m unittest discover -s tests -v
python -m src.build_notebook
```

For an analysis-only reproduction without PostgreSQL, run `python -m src.run_pipeline --db sqlite` before the tests. It writes its own database and regenerates the result files using SQLite. The published database evidence comes from PostgreSQL.

## Verified results

From 2000 to 2025, world total energy supply rose from 105,981 to 166,754 TWh. The renewable share rose from 3.52% to 8.59%, while the fossil fuel share declined from 89.10% to 86.24%. Total supply rose in China and India and fell in Germany and the United States. See the [endpoint table](results/endpoints.csv) and [descriptive statistics](results/descriptive_statistics.csv).

A simple OLS trend on 26 annual observations estimated an increase of **0.209 percentage points per year** in the world renewable share. The model had an in-sample R² of **0.952** and an RMSE of **0.351 percentage points**. The residuals show curvature and strong positive serial dependence (Durbin–Watson **0.189**). Treat the fit as a description of the observed years. [Model statistics](results/model_statistics.csv) · [Diagnostics](figures/04_model_diagnostics.png)

| Figure | Content |
| --- | --- |
| [World total](figures/01_world_total.png) | Annual supply in TWh |
| [World energy mix](figures/02_world_mix.png) | Selected source shares of total supply |
| [Country comparisons](figures/03_countries.png) | Total supply and fossil fuel shares |
| [Model diagnostics](figures/04_model_diagnostics.png) | Observed and fitted share plus residual plots |

## Data and code

- The [data and database guide](docs/DATA_AND_DATABASE.md) explains attribution, coverage, the cleaning workflow, and the schema. See the [data dictionary](data/metadata/data_dictionary.csv) and [relationship diagram](docs/data_model.mmd).
- [Python modules](src/) download, validate, load, analyze, and plot. [SQL](sql/) defines the schema and queries. The [notebook](notebooks/analysis.ipynb) runs the analytical steps after the pipeline.
- [Results](results/) contains compact verification and analysis summaries. [Tests](tests/) reconcile source and database counts and recompute the regression independently.
- The [report appendix](docs/APPENDIX_REPRODUCIBILITY.md) lists the steps and limitations for the written draft.

## Team responsibilities

| Team member | Documented role |
| --- | --- |
| Kevin Schwartz | Project leader and coordination |
| Mariana Khoshaba | Data acquisition, organization, cleaning, and initial exploratory review |
| Jason Wu | Statistical analysis, visualization, and interpretation |

The team shares responsibility for data review, analysis discussions, writing, presentation, and final review.
