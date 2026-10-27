"""Pruebas unitarias para formateo numérico y componentes HTML estructurados."""

from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock, patch
import pandas as pd

from src.ui import components
from src.ui.formatting import fmt_delta, fmt_int, fmt_pct, fmt_rate
from src.ui.state import FilterState, ViewContext


class TestFormatting(unittest.TestCase):
    def test_fmt_int(self):
        self.assertEqual(fmt_int(1234), "1,234")
        self.assertEqual(fmt_int(1000000), "1,000,000")
        self.assertEqual(fmt_int(0), "0")
        self.assertEqual(fmt_int(None), "N/D")
        self.assertEqual(fmt_int(float("nan")), "N/D")
        self.assertEqual(fmt_int("invalido"), "N/D")

    def test_fmt_rate(self):
        self.assertEqual(fmt_rate(123.456, decimals=1), "123.5")
        self.assertEqual(fmt_rate(123.456, decimals=2), "123.46")
        self.assertEqual(fmt_rate(None), "N/D")
        self.assertEqual(fmt_rate(float("nan")), "N/D")
        self.assertEqual(fmt_rate("invalido"), "N/D")

    def test_fmt_pct(self):
        self.assertEqual(fmt_pct(12.345, decimals=2), "12.35 %")
        self.assertEqual(fmt_pct(0.45, decimals=1), "0.5 %")
        self.assertEqual(fmt_pct(None), "N/D")
        self.assertEqual(fmt_pct(float("nan")), "N/D")
        self.assertEqual(fmt_pct("invalido"), "N/D")

    def test_fmt_delta(self):
        # val > 0
        txt, cls = fmt_delta(15.2, unit="%")
        self.assertIn("▲ +15.2%", txt)
        self.assertEqual(cls, "kpi-delta--up")

        # val < 0
        txt, cls = fmt_delta(-8.4, unit=" pts")
        self.assertIn("▼ −8.4 pts", txt)
        self.assertEqual(cls, "kpi-delta--down")

        # val == 0
        txt, cls = fmt_delta(0.0)
        self.assertIn("– 0.0", txt)
        self.assertEqual(cls, "kpi-delta--flat")

        # None o NaN
        txt, cls = fmt_delta(None)
        self.assertEqual(txt, "Sin dato del año anterior")
        self.assertEqual(cls, "kpi-delta--flat")
        txt, cls = fmt_delta("invalido")
        self.assertEqual(txt, "Sin dato del año anterior")


class TestComponents(unittest.TestCase):
    def setUp(self):
        self.filters = FilterState(
            group_key="men5",
            group_label="Menores de 5 años (men5)",
            scope="Nacional",
            is_national=True,
            year_from=2000,
            year_to=2023,
        )
        self.df_sample = pd.DataFrame({
            "year": [2022, 2023],
            "cases_rate_men5": [115.0, 105.0],
            "cases_men5": [1150, 1050],
            "hosp_men5": [115, 105],
            "death_men5": [5, 4],
        })
        self.kpis = {
            "year": 2023.0,
            "cases": 1050.0,
            "cases_rate": 105.0,
            "hospitalizations": 105.0,
            "deaths": 4.0,
            "hr": 10.0,
            "cfr": 0.38,
        }
        self.ctx = ViewContext(
            filters=self.filters,
            scope_title="Nivel Nacional (Consolidado República del Perú)",
            df_raw=self.df_sample,
            df=self.df_sample,
            latest_year=2023,
            kpis=self.kpis,
            cases_delta=-8.7,
            rate_delta=-10.0,
            data_service=None,
            model_service=None,
        )

    @patch("streamlit.markdown")
    def test_page_header_html(self, mock_md):
        components.page_header(self.ctx)
        mock_md.assert_called_once()
        html_output = mock_md.call_args[0][0]
        self.assertIn('data-testid="hero-banner"', html_output)
        self.assertIn('class="page-header"', html_output)
        self.assertIn("Vigilancia epidemiológica de infecciones respiratorias agudas · Perú", html_output)
        self.assertIn("Nivel Nacional (Consolidado República del Perú)", html_output)
        self.assertIn("Menores de 5 años (men5)", html_output)
        self.assertIn("2000–2023", html_output)

    @patch("streamlit.markdown")
    def test_page_header_xss_escape(self, mock_md):
        malicious_ctx = SimpleNamespace(
            scope_title="<script>alert('xss')</script>",
            filters=SimpleNamespace(group_label="<b>bold</b>", year_from=2000, year_to=2023),
        )
        components.page_header(malicious_ctx)
        html_output = mock_md.call_args[0][0]
        self.assertNotIn("<script>", html_output)
        self.assertIn("&lt;script&gt;", html_output)

    @patch("streamlit.markdown")
    def test_bortman_banner_html(self, mock_md):
        components.bortman_banner(self.ctx)
        mock_md.assert_called_once()
        html_output = mock_md.call_args[0][0]
        self.assertIn('data-testid="bortman-alert"', html_output)
        self.assertIn('role="status"', html_output)
        self.assertIn("status-banner", html_output)
        self.assertIn("Canal endémico (Bortman):", html_output)
        self.assertIn("Recomendación OPS/MINSA:", html_output)
        self.assertIn("Umbral de alarma (Q3)", html_output)

    @patch("streamlit.caption")
    @patch("streamlit.columns")
    def test_kpi_row_cards(self, mock_cols, mock_cap):
        col1, col2, col3, col4 = MagicMock(), MagicMock(), MagicMock(), MagicMock()
        mock_cols.return_value = [col1, col2, col3, col4]

        with patch("streamlit.markdown") as mock_md:
            components.kpi_row(self.ctx)
            calls = [call[0][0] for call in mock_md.call_args_list]
            all_html = " ".join(calls)

            self.assertIn('data-testid="kpi-card-cases"', all_html)
            self.assertIn('data-testid="kpi-card-rate"', all_html)
            self.assertIn('data-testid="kpi-card-hr"', all_html)
            self.assertIn('data-testid="kpi-card-cfr"', all_html)
            self.assertIn(".kpi-value", all_html.replace('class="kpi-value"', ".kpi-value"))
            self.assertIn("internamientos", all_html)
            self.assertIn("defunciones", all_html)

    @patch("streamlit.markdown")
    def test_section_header(self, mock_md):
        components.section_header("Mi Título", "Subtítulo explicativo", testid="sec-prueba")
        html_output = mock_md.call_args[0][0]
        self.assertIn('data-testid="sec-prueba"', html_output)
        self.assertIn("<h2>Mi Título</h2>", html_output.replace(' data-testid="sec-prueba"', ""))
        self.assertIn("Subtítulo explicativo", html_output)

    @patch("streamlit.markdown")
    def test_stat_grid(self, mock_md):
        stats = [
            {"label": "Casos", "value": "1,200", "subtext": "Total acumulado"},
            {"label": "Tasa", "value": "95.4"},
        ]
        components.stat_grid(stats)
        html_output = mock_md.call_args[0][0]
        self.assertIn('class="stat-grid"', html_output)
        self.assertIn("1,200", html_output)
        self.assertIn("Total acumulado", html_output)


if __name__ == "__main__":
    unittest.main()
