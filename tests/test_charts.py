"""Pruebas unitarias completas para los constructores puros de gráficos Plotly (charts.py)."""

import unittest
import pandas as pd
import plotly.graph_objects as go

from src.ui import charts
from src.ui.theme import PALETTE, register_plotly_template


class TestCharts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        register_plotly_template()

    def setUp(self):
        self.sample_trend_df = pd.DataFrame({
            "year": [2018, 2019, 2020, 2021, 2022, 2023],
            "cases_rate_men5": [120.5, 135.2, 85.0, 92.4, 110.1, 105.3],
            "cases_rate_60mas": [45.1, 52.0, 78.4, 65.2, 58.0, 60.1],
            "hr_men5": [12.5, 14.2, 18.0, 15.1, 13.0, 12.8],
            "cfr_men5": [0.45, 0.50, 0.85, 0.60, 0.40, 0.38],
            "cases_men5": [1200, 1350, 850, 924, 1101, 1053],
            "hosp_men5": [150, 192, 153, 140, 143, 135],
            "death_men5": [5, 7, 7, 6, 4, 4],
        })

        self.sample_corridor = {
            "q1": 90.0,
            "q2": 110.0,
            "q3": 130.0,
            "current_value": 105.3,
            "zone_name": "Zona de Seguridad",
            "zone_code": "SEGURIDAD",
            "recommendation": "Incidencia normal esperada.",
        }

    def _assert_common_fig_properties(self, fig: go.Figure, expected_y_title: str = ""):
        self.assertIsInstance(fig, go.Figure)
        # Sin título interno (el título vive en el contenedor de Streamlit)
        self.assertIn(fig.layout.title.text, (None, ""))
        # Template asignado
        self.assertIsNotNone(fig.layout.template)
        # Eje Y con título
        if expected_y_title:
            self.assertEqual(fig.layout.yaxis.title.text, expected_y_title)

    def test_build_trend_figure_valid(self):
        fig = charts.build_trend_figure(
            self.sample_trend_df,
            value_col="cases_rate_men5",
            group_key="men5",
            y_title="Tasa x 100k hab.",
        )
        self._assert_common_fig_properties(fig, "Tasa x 100k hab.")
        self.assertGreaterEqual(len(fig.data), 1)
        self.assertEqual(fig.data[0].line.color, PALETTE["men5"])

    def test_build_trend_figure_empty(self):
        fig = charts.build_trend_figure(pd.DataFrame(), "cases_rate_men5", y_title="Tasa")
        self._assert_common_fig_properties(fig, "Tasa")
        self.assertGreaterEqual(len(fig.layout.annotations), 1)
        self.assertIn("Sin datos", fig.layout.annotations[0].text)

    def test_build_bortman_figure_valid(self):
        fig = charts.build_bortman_figure(
            self.sample_corridor,
            self.sample_trend_df,
            value_col="cases_rate_men5",
            current_value=105.3,
        )
        self._assert_common_fig_properties(fig, "Tasa de Incidencia x 100k hab.")
        # Debe tener 4 bandas como shapes
        self.assertEqual(len(fig.layout.shapes), 4)
        # Debe contener las 4 etiquetas textuales
        annotation_texts = [ann.text for ann in fig.layout.annotations]
        for label in ["Éxito", "Seguridad", "Alarma", "Epidemia"]:
            self.assertIn(label, annotation_texts)
        # Serie observada + umbrales
        self.assertGreaterEqual(len(fig.data), 4)

    def test_build_bortman_figure_empty(self):
        fig = charts.build_bortman_figure(None, pd.DataFrame(), "cases_rate_men5")
        self._assert_common_fig_properties(fig, "Tasa de Incidencia x 100k hab.")
        self.assertGreaterEqual(len(fig.layout.annotations), 1)

    def test_build_severity_figure_valid(self):
        fig = charts.build_severity_figure(self.sample_trend_df, group_key="men5")
        self._assert_common_fig_properties(fig, "Porcentaje (%)")
        self.assertEqual(len(fig.data), 2)
        # HR sólido, CFR punteado
        self.assertEqual(fig.data[0].line.color, "#E69F00")
        self.assertEqual(fig.data[1].line.color, "#000000")
        self.assertEqual(fig.data[1].line.dash, "dot")

    def test_build_severity_figure_empty(self):
        fig = charts.build_severity_figure(pd.DataFrame())
        self._assert_common_fig_properties(fig, "Porcentaje (%)")
        self.assertGreaterEqual(len(fig.layout.annotations), 1)

    def test_build_quadrant_figure_valid(self):
        fig = charts.build_quadrant_figure(self.sample_trend_df, group_key="men5")
        self._assert_common_fig_properties(fig, "Letalidad (CFR %)")
        self.assertGreaterEqual(len(fig.data), 1)
        self.assertEqual(fig.layout.xaxis.title.text, "Tasa de hospitalización (HR %)")

    def test_build_quadrant_figure_empty(self):
        fig = charts.build_quadrant_figure(None)
        self._assert_common_fig_properties(fig, "Letalidad (CFR %)")
        self.assertGreaterEqual(len(fig.layout.annotations), 1)

    def test_build_triage_figure_valid(self):
        triage_df = pd.DataFrame({
            "Nivel de Triaje": ["Nivel 1", "Nivel 2", "Nivel 3"],
            "Pacientes Estimados": [15, 60, 180],
            "Porcentaje": [5.0, 20.0, 60.0],
        })
        fig = charts.build_triage_figure(triage_df)
        self._assert_common_fig_properties(fig, "Nivel de Triaje")
        self.assertEqual(len(fig.data), 1)
        # Regla clave: 'pacientes' y CERO 'pactes'
        self.assertIn("pacientes", fig.data[0].texttemplate)
        self.assertNotIn("pactes", fig.data[0].texttemplate)

    def test_build_triage_figure_empty(self):
        fig = charts.build_triage_figure(pd.DataFrame())
        self._assert_common_fig_properties(fig, "Nivel de Triaje")
        self.assertGreaterEqual(len(fig.layout.annotations), 1)

    def test_build_top3_figure_valid(self):
        top3_df = pd.DataFrame({
            "region": ["LORETO", "UCAYALI", "PUNO"],
            "top3_appearances": [18, 15, 12],
            "percent_years_in_top3": [75.0, 62.5, 50.0],
            "observed_years": [24, 24, 24],
        })
        fig = charts.build_top3_figure(top3_df)
        self._assert_common_fig_properties(fig, "Departamento")
        self.assertEqual(len(fig.data), 1)
        self.assertEqual(fig.layout.xaxis.title.text, "Años en el Top 3")

    def test_build_top3_figure_empty(self):
        fig = charts.build_top3_figure(None)
        self._assert_common_fig_properties(fig, "Departamento")
        self.assertGreaterEqual(len(fig.layout.annotations), 1)

    def test_build_bioclimatic_figure_valid(self):
        bio_df = pd.DataFrame({
            "department": ["PUNO", "LORETO", "LIMA"],
            "climate_zone": [
                "Heladas Altoandinas (>3000 msnm)",
                "Friaje Amazónico (Selva Baja/Alta)",
                "Costa y Valles Interandinos",
            ],
            "composite_risk_score": [250.0, 190.0, 80.0],
            "incidence_rate": [185.0, 152.0, 80.0],
        })
        fig = charts.build_bioclimatic_figure(bio_df, top_n=3)
        self._assert_common_fig_properties(fig, "Departamento")
        self.assertEqual(len(fig.data), 1)
        self.assertEqual(fig.layout.xaxis.title.text, "Índice de Riesgo Compuesto")

    def test_build_bioclimatic_figure_empty(self):
        fig = charts.build_bioclimatic_figure(pd.DataFrame())
        self._assert_common_fig_properties(fig, "Departamento")
        self.assertGreaterEqual(len(fig.layout.annotations), 1)

    def test_build_forecast_figure_valid(self):
        hist_df = pd.DataFrame({
            "date": pd.date_range("2023-01-01", periods=10, freq="W"),
            "cases_rate": [25.0 + i for i in range(10)],
        })
        forecast_df = pd.DataFrame({
            "date": pd.date_range("2023-03-15", periods=5, freq="W"),
            "model": ["xgboost"] * 5,
            "predicted": [35.0, 36.0, 37.0, 38.0, 39.0],
            "lower_ci": [30.0, 31.0, 32.0, 33.0, 34.0],
            "upper_ci": [40.0, 41.0, 42.0, 43.0, 44.0],
        })
        fig = charts.build_forecast_figure(hist_df, forecast_df, model_name="XGBoost")
        self._assert_common_fig_properties(fig, "Tasa de Incidencia Predicha")
        self.assertGreaterEqual(len(fig.data), 2)

    def test_build_forecast_figure_empty(self):
        fig = charts.build_forecast_figure(None, None)
        self._assert_common_fig_properties(fig, "Tasa de Incidencia Predicha")
        self.assertGreaterEqual(len(fig.layout.annotations), 1)

    def test_build_feature_importance_figure_valid(self):
        fi_df = pd.DataFrame({
            "feature": ["lag_1", "roll_mean_4", "lag_52"],
            "importance": [0.45, 0.30, 0.25],
        })
        fig = charts.build_feature_importance_figure(fi_df)
        self._assert_common_fig_properties(fig, "Variable")
        self.assertEqual(len(fig.data), 1)
        self.assertEqual(fig.layout.xaxis.title.text, "Importancia Normalizada")

    def test_build_feature_importance_figure_empty(self):
        fig = charts.build_feature_importance_figure(pd.DataFrame())
        self._assert_common_fig_properties(fig, "Variable")
        self.assertGreaterEqual(len(fig.layout.annotations), 1)

    def test_build_quality_radar_valid(self):
        scores = {
            "Adecuación Funcional": 95.0,
            "Eficiencia": 90.0,
            "Fiabilidad": 88.0,
            "Usabilidad": 92.0,
            "Mantenibilidad": 85.0,
        }
        fig = charts.build_quality_radar(scores)
        self.assertIsInstance(fig, go.Figure)
        self.assertIn(fig.layout.title.text, (None, ""))
        self.assertEqual(len(fig.data), 1)
        # Radar polar
        self.assertIn("polar", fig.layout)

    def test_build_quality_radar_empty(self):
        fig = charts.build_quality_radar({})
        self._assert_common_fig_properties(fig, "Puntaje")
        self.assertGreaterEqual(len(fig.layout.annotations), 1)


if __name__ == "__main__":
    unittest.main()
