import json

import numpy as np
import pandas as pd

from src.config import CATEGORIES, META, PROCESSED, RELEASE, RESULTS, SOURCE_SHA256, TOTAL, VERSION
from src.profile_data import profile


def clean(raw):
    PROCESSED.mkdir(parents=True, exist_ok=True)
    codebook = pd.read_csv(META / "data_dictionary.csv").set_index("indicator_id")
    assert codebook.index.is_unique and set(codebook.index) == set(CATEGORIES)
    assert set(codebook.index).issubset(raw.columns)
    assert not raw[["country", "year"]].isna().any().any()
    assert not raw.duplicated(["country", "year"], keep=False).any(), "Resolve source key conflicts before loading"
    assert pd.api.types.is_integer_dtype(raw.year) and raw.year.between(1700, 2100).all()
    assert raw.country.str.strip().eq(raw.country).all()
    assert raw.iso_code.dropna().str.fullmatch("[A-Z]{3}").all()
    assert (raw.groupby("country").iso_code.nunique() <= 1).all()

    geo = raw[["country", "iso_code"]].drop_duplicates().rename(columns={"country": "name"}).copy()
    assert geo.name.is_unique and geo.iso_code.dropna().is_unique
    geo["geo_id"] = geo.iso_code.fillna("OWID:" + geo.name)
    uncoded = pd.read_csv(META / "uncoded_geographies.csv").set_index("name").geography_type
    assert uncoded.index.is_unique and set(uncoded.index) == set(geo.loc[geo.iso_code.isna(), "name"])
    geo["geography_type"] = geo.name.map(uncoded).fillna("iso_coded")
    geo = geo[["geo_id", "name", "iso_code", "geography_type"]].sort_values("geo_id")
    geo.to_csv(PROCESSED / "geography.csv", index=False)

    quality = []
    indicators = []
    for indicator, category in CATEGORIES.items():
        definition = codebook.loc[indicator]
        unit = "TWh" if indicator == TOTAL else "%"
        assert definition.unit == unit
        assert "total energy supply" in definition.title.lower()
        values = pd.to_numeric(raw[indicator], errors="coerce")
        nonnumeric = int((values.isna() & raw[indicator].notna()).sum())
        outside = values.lt(0) | np.isinf(values)
        if unit == "%":
            outside |= values.gt(100)
        assert nonnumeric == 0 and not outside.any(), indicator
        quality.append(dict(indicator=indicator, unit=unit, candidates=len(values), missing=int(values.isna().sum()),
                            present=int(values.count()), missing_pct=100 * values.isna().mean(),
                            zeros=int(values.eq(0).sum()), min=values.min(), max=values.max(),
                            nonnumeric=nonnumeric, out_of_range=int(outside.sum())))
        indicators.append(dict(indicator_id=indicator, energy_category=category,
                               measure="quantity" if unit == "TWh" else "share", unit=unit,
                               accounting_method="total energy supply", title=definition.title, source=definition.source))
    pd.DataFrame(quality).to_csv(RESULTS / "data_quality_summary.csv", index=False)
    pd.DataFrame(indicators).to_csv(PROCESSED / "indicator.csv", index=False)

    obs = raw[["country", "year", *CATEGORIES]].merge(
        geo[["name", "geo_id"]], left_on="country", right_on="name", validate="many_to_one")
    obs = obs.melt(id_vars=["geo_id", "year"], value_vars=list(CATEGORIES),
                   var_name="indicator_id", value_name="value").assign(release_id=RELEASE)
    key = ["release_id", "geo_id", "year", "indicator_id"]
    assert len(obs) == len(raw) * len(CATEGORIES) and not obs.duplicated(key).any()
    obs.sort_values(key)[key + ["value"]].to_csv(PROCESSED / "energy_observation.csv", index=False)
    provenance = json.loads((META / "provenance.json").read_text(encoding="utf-8"))["owid_energy.csv"]
    pd.DataFrame([dict(release_id=RELEASE, provider="Our World in Data", version=VERSION,
                       source_url=provenance["url"], retrieval_date=provenance["acquired_utc"][:10] if provenance["acquired_utc"] else None,
                       sha256=SOURCE_SHA256)]).to_csv(PROCESSED / "source_release.csv", index=False)
    return obs


if __name__ == "__main__":
    clean(profile())
