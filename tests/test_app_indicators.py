"""Regresiones de comparaciones anuales y filtros del ranking de la app."""

import unittest

import pandas as pd

from src.app_indicators import previous_year_deltas, top3_for_period


class TestAppIndicators(unittest.TestCase):
    def setUp(self):
        self.history = pd.DataFrame({
            "year": [2021, 2022, 2023],
            "cases_men5": [100, 200, 150],
            "cases_rate_men5": [10.0, 20.0, 15.0],
        })

    def test_single_year_view_uses_previous_year_from_history(self):
        selected = self.history.loc[self.history["year"] == 2023]
        self.assertEqual(len(selected), 1)
        self.assertEqual(previous_year_deltas(self.history, "men5", 2023), (-25.0, -5.0))

    def test_missing_previous_year_is_not_zero_change(self):
        self.assertEqual(previous_year_deltas(self.history, "men5", 2021), (None, None))
        with_gap = self.history.loc[self.history["year"] != 2022]
        self.assertEqual(previous_year_deltas(with_gap, "men5", 2023), (None, None))

    def test_zero_previous_cases_has_no_percentage(self):
        self.history.loc[self.history["year"] == 2022, "cases_men5"] = 0
        self.assertEqual(previous_year_deltas(self.history, "men5", 2023), (None, -5.0))

    def test_nonfinite_values_have_no_comparison(self):
        self.history.loc[self.history["year"] == 2022, "cases_men5"] = float("nan")
        self.history.loc[self.history["year"] == 2022, "cases_rate_men5"] = float("inf")
        self.assertEqual(previous_year_deltas(self.history, "men5", 2023), (None, None))

    def test_ranking_changes_with_period_and_retains_ties(self):
        grid = pd.DataFrame({
            "region": ["A", "B", "C", "D"],
            "2022": [1, 2, 3, 3],
            "2023": [5, 1, 2, 3],
        })
        original = grid.copy(deep=True)
        result, years = top3_for_period(grid, (2023, 2023))
        self.assertEqual(years, [2023])
        self.assertEqual(result["region"].tolist(), ["B", "C", "D", "A"])
        self.assertEqual(result["percent_years_in_top3"].tolist(), [100.0, 100.0, 100.0, 0.0])
        all_years, _ = top3_for_period(grid, (2022, 2023))
        self.assertEqual(all_years.set_index("region").loc["A", "percent_years_in_top3"], 50.0)
        pd.testing.assert_frame_equal(grid, original)

    def test_ranking_does_not_invent_years_before_adult_coverage(self):
        grid = pd.DataFrame({"region": ["A"], "2006": [1], "2007": [4]})
        result, years = top3_for_period(grid, (2000, 2005))
        self.assertTrue(result.empty)
        self.assertEqual(years, [])
        result, years = top3_for_period(grid, (2000, 2007))
        self.assertEqual(years, [2006, 2007])
        self.assertEqual(result.iloc[0]["percent_years_in_top3"], 50.0)

    def test_missing_rank_is_not_counted_as_an_observed_year(self):
        grid = pd.DataFrame({"region": ["A", "B"], "2022": [1, None], "2023": [None, None]})
        result, _ = top3_for_period(grid, (2022, 2023))
        self.assertEqual(result["region"].tolist(), ["A"])
        self.assertEqual(result.iloc[0]["observed_years"], 1)
        self.assertEqual(result.iloc[0]["percent_years_in_top3"], 100.0)


if __name__ == "__main__":
    unittest.main()
