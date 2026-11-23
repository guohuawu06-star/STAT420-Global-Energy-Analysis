import json

import numpy as np
import pandas as pd

from src.config import CATEGORIES, RAW, RESULTS


def profile():
    RESULTS.mkdir(exist_ok=True)
    raw = pd.read_csv(RAW / "owid_energy.csv", keep_default_na=False, na_values=[""])
    rows = []
    for name, series in raw.items():
        numeric = pd.to_numeric(series, errors="coerce")
        is_measure = name not in {"country", "iso_code"}
        rows.append({
            "column": name, "dtype": str(series.dtype), "present": int(series.count()),
            "missing": int(series.isna().sum()), "missing_pct": 100 * series.isna().mean(),
            "distinct": int(series.nunique()), "example": series.dropna().iloc[0] if series.count() else "",
            "non_numeric": int((numeric.isna() & series.notna()).sum()) if is_measure else None,
            "non_finite": int(np.isinf(numeric).sum()) if is_measure else None,
            "min": numeric.min() if is_measure else None, "max": numeric.max() if is_measure else None,
            "zeros": int(numeric.eq(0).sum()) if is_measure else None,
        })
    pd.DataFrame(rows).to_csv(RESULTS / "column_profile.csv", index=False)
    coverage = raw.groupby("country").agg(rows=("year", "size"), first_year=("year", "min"), last_year=("year", "max"))
    coverage.to_csv(RESULTS / "raw_geography_coverage.csv")
    metrics = dict(raw_rows=len(raw), raw_columns=len(raw.columns), first_year=int(raw.year.min()),
                   last_year=int(raw.year.max()), geographies=int(raw.country.nunique()),
                   iso_coded=int(raw.iso_code.nunique()), exact_duplicates=int(raw.duplicated().sum()),
                   duplicate_geography_year=int(raw.duplicated(["country", "year"]).sum()),
                   missing_keys=int(raw[["country", "year"]].isna().any(axis=1).sum()))
    (RESULTS / "raw_profile.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    return raw


if __name__ == "__main__":
    profile()
