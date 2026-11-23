import json
import unittest

import numpy as np
import pandas as pd

from src.config import CATEGORIES, FIGURES, PLACES, PROCESSED, RAW, RENEWABLE, RESULTS, TOTAL


class OutputChecks(unittest.TestCase):
    def test_source_to_fact_reconciliation(self):
        raw = pd.read_csv(RAW / "owid_energy.csv")
        fact = pd.read_csv(PROCESSED / "energy_observation.csv")
        geo = pd.read_csv(PROCESSED / "geography.csv")
        quality = pd.read_csv(RESULTS / "data_quality_summary.csv")
        key = ["release_id", "geo_id", "year", "indicator_id"]
        self.assertFalse(raw.duplicated(["country", "year"]).any())
        self.assertFalse(fact.duplicated(key).any())
        self.assertEqual(len(fact), len(raw) * len(CATEGORIES))
        mapped = fact.merge(geo, on="geo_id", validate="many_to_one").pivot(
            index=["name", "year"], columns="indicator_id", values="value")
        source = raw.set_index(["country", "year"])[list(CATEGORIES)].sort_index()
        pd.testing.assert_frame_equal(mapped[list(CATEGORIES)].sort_index(), source, check_names=False)
        self.assertTrue(fact.year.between(1700, 2100).all())
        self.assertTrue(fact.loc[fact.indicator_id.ne(TOTAL), "value"].dropna().between(0, 100).all())
        db = json.loads((RESULTS / "database_run.json").read_text())
        self.assertEqual(db["duplicate_keys"], 0)
        self.assertEqual(db["tables"]["energy_observation"], len(fact))
        self.assertEqual(db["present"], int(quality.present.sum()))
        self.assertEqual(db["missing"], int(fact.value.isna().sum()))
        self.assertEqual(db["zeros"], int(fact.value.eq(0).sum()))
        coverage = pd.read_csv(RESULTS / "annual_coverage.csv")
        self.assertEqual(int(coverage.slots.sum()), len(fact))
        self.assertEqual(int(coverage.observed.sum()), db["present"])
        self.assertEqual(int(coverage.observed_zero.sum()), db["zeros"])

    def test_panel_and_model(self):
        p = pd.read_csv(RESULTS / "analysis_panel.csv")
        countries = pd.read_csv(RESULTS / "countries_series.csv")
        self.assertEqual(set(countries.name), set(PLACES) - {"World"})
        self.assertEqual(set(countries.iso_code), {code for code in PLACES.values() if code})
        self.assertEqual(set(p.unit), {"TWh", "%"})
        self.assertFalse(p.value.isna().any())
        self.assertFalse(p.duplicated(["name", "year", "indicator_id"]).any())
        m = pd.read_csv(RESULTS / "model_statistics.csv").iloc[0]
        self.assertEqual(len(p), int(m.n) * len(CATEGORIES) * len(PLACES))
        y = p.loc[p.name.eq("World") & p.indicator_id.eq(RENEWABLE)].sort_values("year")
        self.assertEqual(list(y.year), list(range(int(m.first_year), int(m.last_year) + 1)))
        self.assertEqual(len(y), m.n)
        x = y.year.to_numpy() - m.first_year
        slope, intercept = np.polyfit(x, y.value, 1)
        np.testing.assert_allclose([m.slope, m.intercept], [slope, intercept])
        residual = y.value - (intercept + slope * x)
        np.testing.assert_allclose(m.rmse, np.sqrt(np.mean(residual ** 2)))
        np.testing.assert_allclose(m.r_squared, 1 - np.sum(residual ** 2) / np.sum((y.value - y.value.mean()) ** 2))

    def test_descriptive_statistics(self):
        panel = pd.read_csv(RESULTS / "analysis_panel.csv")
        summary = pd.read_csv(RESULTS / "descriptive_statistics.csv")
        key = ["name", "indicator_id", "unit"]
        self.assertFalse(summary.duplicated(key).any())
        self.assertEqual(len(summary), len(PLACES) * len(CATEGORIES))
        self.assertEqual(summary.n.sum(), len(panel))
        world = panel.loc[panel.name.eq("World") & panel.indicator_id.eq(TOTAL), "value"].to_numpy()
        world_summary = summary.loc[summary.name.eq("World") & summary.indicator_id.eq(TOTAL)].iloc[0]
        self.assertEqual(world_summary.unit, "TWh")
        self.assertEqual(world_summary.n, len(world))
        np.testing.assert_allclose(
            world_summary[["mean", "std", "min", "median", "max"]].to_numpy(dtype=float),
            [world.mean(), world.std(ddof=1), world.min(), np.median(world), world.max()])

    def test_figures(self):
        figures = list(FIGURES.glob("*.png"))
        self.assertEqual(len(figures), 4)
        self.assertTrue(all(path.stat().st_size > 10000 for path in figures))


if __name__ == "__main__":
    unittest.main()
