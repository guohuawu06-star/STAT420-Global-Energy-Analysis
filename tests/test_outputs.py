import json
import sqlite3
import unittest

import numpy as np
import pandas as pd

from src.config import CATEGORIES, FIGURES, PLACES, PROCESSED, RAW, RENEWABLE, RESULTS, ROOT, TOTAL


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
        diagnostics = pd.read_csv(RESULTS / "model_diagnostics.csv")
        np.testing.assert_array_equal(diagnostics.year, y.year)
        np.testing.assert_allclose(diagnostics.observed, y.value)
        np.testing.assert_allclose(diagnostics.fitted, intercept + slope * x)
        np.testing.assert_allclose(diagnostics.residual, residual, atol=1e-12)
        np.testing.assert_allclose(m.durbin_watson, np.sum(np.diff(residual)**2) / np.sum(residual**2))
        np.testing.assert_allclose(m.lag1, np.corrcoef(residual.iloc[:-1], residual.iloc[1:])[0, 1])
        position = np.argmax(np.abs(residual))
        self.assertEqual(m.largest_residual_year, y.year.iloc[position])
        np.testing.assert_allclose(m.largest_residual, residual.iloc[position])

    def test_endpoints_from_raw(self):
        raw = pd.read_csv(RAW / "owid_energy.csv").set_index(["country", "year"])
        endpoints = pd.read_csv(RESULTS / "endpoints.csv")
        model = pd.read_csv(RESULTS / "model_statistics.csv").iloc[0]
        self.assertEqual(len(endpoints), len(PLACES) * len(CATEGORIES))
        for _, values in endpoints.iterrows():
            first, last = (raw.at[(values["name"], year), values.indicator_id]
                           for year in (model.first_year, model.last_year))
            np.testing.assert_allclose([values["first"], values["last"], values.delta],
                                       [first, last, last - first], atol=1e-12)

    def test_schema_constraints_and_rollback(self):
        with sqlite3.connect(":memory:") as db:
            db.execute("PRAGMA foreign_keys = ON")
            db.executescript((ROOT / "sql/schema.sql").read_text(encoding="utf-8"))
            db.execute("INSERT INTO source_release VALUES ('r', 'OWID', 'test', 'test', NULL, ?)", ("0" * 64,))
            db.execute("INSERT INTO geography VALUES ('AAA', 'Test location', 'AAA', 'iso_coded')")
            db.execute("INSERT INTO indicator VALUES ('share_pct', 'Test', 'share', '%', 'test', 'test', 'test')")
            db.commit()
            sql = "INSERT INTO energy_observation VALUES ('r', ?, ?, 'share_pct', ?)"
            with self.assertRaises(sqlite3.IntegrityError), db:
                db.execute(sql, ("AAA", 2000, 0))
                db.execute(sql, ("BAD", 2000, 1))
            self.assertEqual(db.execute("SELECT COUNT(*) FROM energy_observation").fetchone()[0], 0)
            with db:
                db.execute(sql, ("AAA", 2000, None))
                db.execute(sql, ("AAA", 2001, 0))
            for row in [("AAA", 2001, 2), ("AAA", 2002, 101), ("AAA", 2003, -1)]:
                with self.assertRaises(sqlite3.IntegrityError), db:
                    db.execute(sql, row)
            self.assertEqual(db.execute("SELECT value FROM energy_observation ORDER BY year").fetchall(),
                             [(None,), (0.0,)])

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
