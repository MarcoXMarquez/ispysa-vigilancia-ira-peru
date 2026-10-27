"""Pruebas unitarias para construcción de estado inmutable y contexto de vistas (state.py)."""

import unittest
from unittest.mock import MagicMock
import pandas as pd

from src.ui import state
from src.ui.state import FilterState, ViewContext


class TestState(unittest.TestCase):
    def setUp(self):
        self.mock_data_service = MagicMock()
        self.mock_model_service = MagicMock()

        self.mock_data_service.get_departments.return_value = ["AREQUIPA", "CUSCO", "LIMA"]

        self.df_national = pd.DataFrame({
            "year": [2021, 2022, 2023],
            "cases_men5": [1200, 1100, 1050],
            "cases_rate_men5": [120.0, 110.0, 105.0],
            "hosp_men5": [120, 110, 105],
            "death_men5": [5, 4, 3],
            "population": [1000000, 1000000, 1000000],
        })
        self.mock_data_service.get_national_summary.return_value = self.df_national
        self.mock_data_service.get_department_data.return_value = self.df_national
        self.mock_data_service.compute_kpis.return_value = {
            "year": 2023.0,
            "cases": 1050.0,
            "cases_rate": 105.0,
            "hospitalizations": 105.0,
            "deaths": 3.0,
            "hr": 10.0,
            "cfr": 0.28,
        }

    def test_build_filter_state_national_men5(self):
        mock_sidebar = MagicMock()
        mock_sidebar.radio.return_value = "Menores de 5 años"
        mock_sidebar.selectbox.return_value = "Nacional"
        mock_sidebar.slider.return_value = (2005, 2020)

        fstate = state.build_filter_state(mock_sidebar, self.mock_data_service)
        self.assertEqual(fstate.group_key, "men5")
        self.assertIn("men5", fstate.group_label)
        self.assertEqual(fstate.scope, "Nacional")
        self.assertTrue(fstate.is_national)
        self.assertEqual(fstate.year_from, 2005)
        self.assertEqual(fstate.year_to, 2020)

    def test_build_filter_state_department_60mas(self):
        mock_sidebar = MagicMock()
        mock_sidebar.radio.return_value = "Adultos de 60 años a más"
        mock_sidebar.selectbox.return_value = "Arequipa"
        mock_sidebar.slider.return_value = (2010, 2023)

        fstate = state.build_filter_state(mock_sidebar, self.mock_data_service)
        self.assertEqual(fstate.group_key, "60mas")
        self.assertIn("60mas", fstate.group_label)
        self.assertEqual(fstate.scope, "AREQUIPA")
        self.assertFalse(fstate.is_national)

    def test_build_view_context_national(self):
        fstate = FilterState(
            group_key="men5",
            group_label="Menores de 5 años (men5)",
            scope="Nacional",
            is_national=True,
            year_from=2021,
            year_to=2023,
        )
        ctx = state.build_view_context(fstate, self.mock_data_service, self.mock_model_service)
        self.assertIsNotNone(ctx)
        self.assertIsInstance(ctx, ViewContext)
        self.assertEqual(ctx.latest_year, 2023)
        self.assertIn("Nacional", ctx.scope_title)
        self.assertEqual(len(ctx.df), 3)

    def test_build_view_context_department(self):
        fstate = FilterState(
            group_key="men5",
            group_label="Menores de 5 años (men5)",
            scope="AREQUIPA",
            is_national=False,
            year_from=2021,
            year_to=2023,
        )
        ctx = state.build_view_context(fstate, self.mock_data_service, self.mock_model_service)
        self.assertIsNotNone(ctx)
        self.assertIn("Arequipa", ctx.scope_title)

    def test_build_view_context_empty_range(self):
        fstate = FilterState(
            group_key="men5",
            group_label="Menores de 5 años (men5)",
            scope="Nacional",
            is_national=True,
            year_from=1990,
            year_to=1995,
        )
        ctx = state.build_view_context(fstate, self.mock_data_service, self.mock_model_service)
        self.assertIsNone(ctx)


if __name__ == "__main__":
    unittest.main()
