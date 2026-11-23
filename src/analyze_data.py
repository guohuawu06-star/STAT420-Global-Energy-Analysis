import json
import platform
from importlib.metadata import version

import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.stats.stattools import durbin_watson

from src.config import CATEGORIES, PLACES, RENEWABLE, RESULTS, START_YEAR, TOTAL


def analyze():
    world = pd.read_csv(RESULTS / "world_series.csv").assign(name="World")
    countries = pd.read_csv(RESULTS / "countries_series.csv")
    assert countries.groupby("name").iso_code.first().to_dict() == {k: v for k, v in PLACES.items() if v}
    data = pd.concat([world, countries], ignore_index=True)
    wide = data.pivot(index="year", columns=["name", "indicator_id"], values="value")
    wanted = pd.MultiIndex.from_product([PLACES, CATEGORIES], names=["name", "indicator_id"])
    wide = wide.reindex(index=range(START_YEAR, int(wide.index.max()) + 1), columns=wanted)
    gaps = wide.index[wide.isna().any(axis=1)]
    end = int(gaps[0] - 1) if len(gaps) else int(wide.index.max())
    assert end - START_YEAR + 1 >= 15, "Insufficient balanced coverage for trend study"
    panel = data.loc[data.year.between(START_YEAR, end), ["name", "year", "indicator_id", "unit", "value"]]
    assert len(panel) == len(PLACES) * len(CATEGORIES) * (end - START_YEAR + 1)
    assert panel.value.notna().all() and set(panel.unit) == {"TWh", "%"}
    panel.sort_values(["name", "year", "indicator_id"]).to_csv(RESULTS / "analysis_panel.csv", index=False)

    summary = panel.groupby(["name", "indicator_id", "unit"], as_index=False).value.agg(
        n="count", mean="mean", std="std", min="min", median="median", max="max")
    summary.to_csv(RESULTS / "descriptive_statistics.csv", index=False)

    endpoints = wide.loc[[START_YEAR, end]].T.rename(columns={START_YEAR: "first", end: "last"})
    endpoints["delta"] = endpoints["last"] - endpoints["first"]
    endpoints.to_csv(RESULTS / "endpoints.csv")

    y = wide.loc[START_YEAR:end, ("World", RENEWABLE)]
    years = y.index.to_numpy()
    fit = sm.OLS(y.to_numpy(), sm.add_constant(years - START_YEAR), missing="raise").fit()
    residuals = fit.resid
    peak = int(np.argmax(np.abs(residuals)))
    model = dict(geography="World", indicator=RENEWABLE, response_unit="%", slope_unit="percentage points/year",
                 first_year=START_YEAR, last_year=end, n=int(fit.nobs), intercept=float(fit.params[0]),
                 slope=float(fit.params[1]), r_squared=float(fit.rsquared),
                 rmse=float(np.sqrt(np.mean(residuals**2))), durbin_watson=float(durbin_watson(residuals)),
                 lag1=float(np.corrcoef(residuals[:-1], residuals[1:])[0, 1]),
                 largest_residual_year=int(years[peak]), largest_residual=float(residuals[peak]))
    pd.DataFrame([model]).to_csv(RESULTS / "model_statistics.csv", index=False)
    pd.DataFrame(dict(year=years, observed=y.to_numpy(), fitted=fit.fittedvalues, residual=residuals)).to_csv(
        RESULTS / "model_diagnostics.csv", index=False)
    env = {"python": platform.python_version(), **{name: version(name) for name in (
        "pandas", "numpy", "scipy", "matplotlib", "statsmodels", "nbformat", "nbclient", "ipykernel", "psycopg")}}
    (RESULTS / "environment.json").write_text(json.dumps(env, indent=2), encoding="utf-8")
    return model


if __name__ == "__main__":
    print(analyze())
