"""
Pruebas unitarias de la portada Quality Nexus (src/ui/landing.py y src/ui/landing_chart.py).
Verifican la figura SVG, el cálculo de cifras (con y sin auditoría), la navegación portada/panel y el render.
"""
import unittest
from unittest.mock import MagicMock, patch

import pandas as pd

from src.services.data_service import EpidemiologyDataService
from src.ui import landing, landing_chart


def _nat_frame() -> pd.DataFrame:
    """Serie nacional mínima: 60+ sin casos antes de 2006, como en los datos reales."""
    years = list(range(2004, 2009))
    return pd.DataFrame(
        {
            "year": years,
            "cases_men5": [100, 90, 80, 70, 60],
            "cases_60mas": [0, 0, 10, 20, 30],
            "cases_rate_men5": [200.0, 180.0, 160.0, 140.0, 120.0],
            "cases_rate_60mas": [0.0, 0.0, 20.0, 40.0, 60.0],
        }
    )


class TestHeroChart(unittest.TestCase):
    def test_svg_has_both_series_and_labels(self):
        svg = landing_chart.build_hero_chart_svg(_nat_frame())
        self.assertTrue(svg.startswith("<svg"))
        self.assertEqual(svg.count('class="ln'), 2)
        self.assertIn("Menores de 5 años", svg)
        self.assertIn("60 años a más", svg)

    def test_series_skips_years_without_cases(self):
        pts = landing_chart._series_points(_nat_frame(), "60mas")
        self.assertEqual([y for y, _ in pts], [2006, 2007, 2008])

    def test_labels_are_separated_but_keep_order(self):
        out = landing_chart._spread_labels([100.0, 102.0], gap=38)
        self.assertGreaterEqual(abs(out[1] - out[0]), 38)
        self.assertLess(out[0], out[1])

    def test_labels_far_apart_are_untouched(self):
        self.assertEqual(landing_chart._spread_labels([10.0, 200.0], gap=38), [10.0, 200.0])

    def test_alt_text_reports_real_values(self):
        alt = landing_chart.chart_alt_text(_nat_frame())
        self.assertIn("200.0", alt)
        self.assertIn("2004", alt)
        self.assertIn("120.0", alt)

    def test_respects_reduced_motion(self):
        self.assertIn("prefers-reduced-motion", landing_chart.build_hero_chart_svg(_nat_frame()))


class TestFacts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.service = EpidemiologyDataService()

    def test_facts_without_audit_omit_quality_numbers(self):
        facts = landing.collect_facts(self.service, None)
        labels = [lbl for _, lbl in landing.fact_items(facts)]
        self.assertEqual(len(labels), 2)
        self.assertEqual(facts["n_depts"], 25)

    def test_facts_with_audit(self):
        audit = {
            "questions_count": 3,
            "questions": [
                {"caracteristica": "Seguridad", "respuesta": "SI"},
                {"caracteristica": "Seguridad", "respuesta": "NO"},
                {"caracteristica": "Usabilidad", "respuesta": "NA"},
            ],
            "unit_tests": {"passed": 7, "total": 8},
            "security": {"applicability_coverage": "7/15"},
        }
        facts = landing.collect_facts(self.service, audit)
        values = dict(landing.fact_items(facts))
        self.assertEqual(values["3"], "preguntas en la auditoría de calidad")
        self.assertEqual(values["7/8"], "pruebas automáticas aprobadas")
        names = [c["name"] for c in facts["characteristics"]]
        self.assertEqual(names, ["Seguridad", "Usabilidad"])
        self.assertEqual(facts["characteristics"][0]["total"], 2)
        self.assertEqual(facts["security_coverage"], "7/15")

    def test_quality_section_without_data_has_no_bars(self):
        facts = landing.collect_facts(self.service, None)
        self.assertNotIn("nx-bar", landing._quality_section(facts))

    def test_html_blocks_have_no_blank_lines_or_indentation(self):
        facts = landing.collect_facts(self.service, None)
        for block in (landing._topbar(), landing._views_section(facts), landing._data_section(facts)):
            for line in block.splitlines():
                self.assertEqual(line, line.strip())
                self.assertTrue(line)


class TestNavigation(unittest.TestCase):
    def test_default_shows_landing(self):
        with patch.object(landing.st, "session_state", {}), patch.object(landing.st, "query_params", {}):
            self.assertFalse(landing.is_dashboard_view())

    def test_session_flag_opens_dashboard(self):
        with patch.object(landing.st, "session_state", {landing.SESSION_KEY: True}), \
                patch.object(landing.st, "query_params", {}):
            self.assertTrue(landing.is_dashboard_view())

    def test_query_param_opens_dashboard(self):
        with patch.object(landing.st, "session_state", {}), \
                patch.object(landing.st, "query_params", {landing.QUERY_KEY: landing.QUERY_VALUE}):
            self.assertTrue(landing.is_dashboard_view())

    def test_enter_and_leave(self):
        state, params = {}, {landing.QUERY_KEY: landing.QUERY_VALUE}
        with patch.object(landing.st, "session_state", state), patch.object(landing.st, "query_params", params):
            landing.enter_dashboard()
            self.assertTrue(state[landing.SESSION_KEY])
            landing.leave_dashboard()
            self.assertFalse(state[landing.SESSION_KEY])
            self.assertNotIn(landing.QUERY_KEY, params)


class TestRender(unittest.TestCase):
    def test_render_runs_and_creates_two_entry_buttons(self):
        service = EpidemiologyDataService()
        with patch("streamlit.markdown") as md, \
                patch("streamlit.button") as button, \
                patch("streamlit.columns", side_effect=lambda spec, **kw: [MagicMock(), MagicMock()]):
            landing.render(service)
        self.assertEqual(button.call_count, 2)
        for call in button.call_args_list:
            self.assertEqual(call.kwargs["on_click"], landing.enter_dashboard)
        self.assertGreaterEqual(md.call_count, 8)


if __name__ == "__main__":
    unittest.main()
