"""
Pruebas unitarias para la renderización de las 5 pestañas de la interfaz (src/ui/tabs/).
Verifica la invocación limpia de cada pestaña sin fallos de renderizado.
"""
import unittest
from unittest.mock import MagicMock, patch

from src.services.data_service import EpidemiologyDataService
from src.services.model_service import EpidemiologyModelService
from src.ui.state import FilterState, build_view_context
from src.ui.theme import register_plotly_template


class TestUITabs(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        register_plotly_template()

    def setUp(self):
        self.data_service = EpidemiologyDataService()
        self.model_service = EpidemiologyModelService()
        self.filters = FilterState(
            group_key="men5",
            group_label="Menores de 5 años",
            scope="Nacional",
            is_national=True,
            year_from=2000,
            year_to=2023,
        )
        self.ctx = build_view_context(self.filters, self.data_service, self.model_service)

    def _mock_cols(self, spec):
        n = spec if isinstance(spec, int) else len(spec)
        return [MagicMock() for _ in range(n)]

    def test_render_all_tabs(self):
        with patch("streamlit.markdown"), \
             patch("streamlit.caption"), \
             patch("streamlit.dataframe"), \
             patch("streamlit.expander"), \
             patch("streamlit.plotly_chart"), \
             patch("streamlit.columns", side_effect=self._mock_cols), \
             patch("streamlit.checkbox", return_value=False):
            from src.ui.tabs import forecast, quality, severity, territory, trend

            trend.render(self.ctx)
            severity.render(self.ctx)
            territory.render(self.ctx)
            forecast.render(self.ctx)
            quality.render(self.ctx)


if __name__ == "__main__":
    unittest.main()
