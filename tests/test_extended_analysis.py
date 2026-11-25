import unittest

import numpy as np
import pandas as pd

from src.config import PROCESSED, RAW, RENEWABLE, RESULTS, TOTAL
from src.extended_analysis import (
    HISTORICAL_SOURCES, MAP_END, MAP_START, MISSING, OUTSIDE, REPORTED,
    RENEWABLE_TOLERANCE_TWH, geographic_coverage, geographic_figures, geographic_panel,
    historical_figures, historical_values, map_codes,
)


class ExtendedAnalysisChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = pd.read_csv(RAW / "owid_energy.csv")
        cls.geography = pd.read_csv(PROCESSED / "geography.csv")
        observations = pd.read_csv(PROCESSED / "energy_observation.csv")
        cls.panel = geographic_panel(cls.geography, observations, MAP_START, int(cls.raw.year.max()))
        cls.coverage = geographic_coverage(cls.panel).set_index("year")
        cls.history = historical_values(cls.raw)

    def test_source_grid_status_and_recorded_zero(self):
        raw = self.raw.dropna(subset=["iso_code"]).set_index(["iso_code", "year"])
        self.assertFalse(self.panel.duplicated(["iso_code", "year"]).any())
        self.assertEqual(set(self.panel.iso_code), set(raw.index.get_level_values("iso_code")))
        for row in self.panel.itertuples(index=False):
            key = (row.iso_code, row.year)
            expected = OUTSIDE if key not in raw.index else (
                MISSING if pd.isna(raw.at[key, TOTAL]) else REPORTED
            )
            self.assertEqual(row.status, expected)
        all_missing = self.panel[self.panel.source_row & self.panel[list(
            pd.read_csv(PROCESSED / "indicator.csv").indicator_id)].isna().all(axis=1)]
        self.assertGreater(len(all_missing), 0)
        self.assertTrue(all_missing.status.eq(MISSING).all())
        self.assertTrue(self.panel.loc[self.panel[TOTAL].eq(0), "status"].eq(REPORTED).all())
        self.assertEqual(
            self.panel.loc[self.panel.iso_code.eq("SSD") & self.panel.year.eq(MAP_START), "status"].item(), OUTSIDE
        )

    def test_yearly_geo_counts_match_raw_and_sql(self):
        raw = self.raw.loc[self.raw.iso_code.notna()].groupby("year")[[TOTAL, RENEWABLE]].count()
        sql = pd.read_csv(RESULTS / "annual_coverage.csv").query("geography_type == 'iso_coded'")
        sql = sql.pivot(index="year", columns="indicator_id", values="observed")
        for source, field in ((TOTAL, "total_reported"), (RENEWABLE, "renewable_reported")):
            for data in (raw, sql):
                np.testing.assert_array_equal(self.coverage[field], data.reindex(self.coverage.index)[source])
        self.assertGreater(self.coverage.at[MAP_END, "total_reported"],
                           self.coverage.at[MAP_END + 1, "total_reported"])

    def test_availability_frames_use_map_geometry_and_all_statuses(self):
        _, renewables, availability, _ = geographic_figures(self.panel, self.coverage.reset_index())
        years = list(range(MAP_START, MAP_END + 1))
        self.assertEqual([int(frame.name) for frame in availability.frames], years)
        self.assertEqual([int(frame.name) for frame in renewables.frames], years)
        visible = self.panel.loc[self.panel.iso_code.isin(map_codes())]
        self.assertNotIn("ANT", map_codes())
        self.assertIn("ANT", set(self.panel.iso_code))
        status_code = {OUTSIDE: 0, MISSING: 1, REPORTED: 2}
        seen = set()
        for frame in availability.frames:
            expected = visible.loc[visible.year.eq(int(frame.name))].set_index("iso_code").status.map(status_code)
            trace = frame.data[0]
            actual = dict(zip(trace.locations, trace.z))
            self.assertEqual(actual, expected.to_dict())
            seen.update(actual.values())
        self.assertEqual(seen, set(status_code.values()))

    def test_historical_reconciliation_and_animation(self):
        raw = self.raw.loc[self.raw.country.eq("World")].set_index("year")
        columns = list(HISTORICAL_SOURCES.values())
        complete = raw[[TOTAL, *columns]].dropna()
        self.assertEqual(set(self.history.dropna(subset=["component_sum_twh", TOTAL]).index), set(complete.index))
        self.assertEqual(set(self.history["renewable_sum_twh"].dropna().index),
                         set(raw[columns[4:]].dropna().index))
        delta = self.history.renewable_difference_twh.dropna()
        self.assertTrue(delta.abs().le(RENEWABLE_TOLERANCE_TWH).all())
        pd.testing.assert_series_equal(self.history[TOTAL], raw[TOTAL].sort_index())
        self.assertGreater(self.history.total_difference_twh.abs().max(), RENEWABLE_TOLERANCE_TWH)
        _, animation = historical_figures(self.history)
        self.assertEqual([int(frame.name) for frame in animation.frames], sorted(complete.index))
        for frame in animation.frames:
            self.assertTrue(all(max(trace.x) == int(frame.name) for trace in frame.data))
        self.assertEqual([trace.name for trace in animation.data][:-1], list(HISTORICAL_SOURCES))

    def test_incomplete_historical_components_are_not_filled_with_zero(self):
        broken = self.raw.loc[self.raw.country.eq("World") & self.raw.year.eq(2024)].copy()
        broken.loc[:, "wind_energy_twh"] = np.nan
        test = historical_values(broken).iloc[0]
        self.assertTrue(pd.isna(test.renewable_sum_twh))
        self.assertTrue(pd.isna(test.component_sum_twh))
        self.assertTrue(pd.notna(test[TOTAL]))
