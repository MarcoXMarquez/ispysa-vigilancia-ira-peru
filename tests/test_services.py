"""
Pruebas Unitarias para los Servicios Epidemiológicos
Verifica la integridad de datos, cálculos de tasas e indicadores de severidad.
Cobertura objetivo: >= 80% (Estándar ISO/IEC 25010 y TDD)
"""

import unittest
from pathlib import Path
import pandas as pd
import numpy as np
import sys

# Agregar src al path
ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from src.services.data_service import EpidemiologyDataService
from src.services.model_service import EpidemiologyModelService


class TestEpidemiologyServices(unittest.TestCase):
    """Conjunto de pruebas exhaustivas para validar los servicios del sistema."""

    def setUp(self):
        self.data_service = EpidemiologyDataService(root_dir=ROOT_DIR)
        self.model_service = EpidemiologyModelService(root_dir=ROOT_DIR)

    # --------------------------------------------------------------------------
    # PRUEBAS DEL SERVICIO DE DATOS (DataService)
    # --------------------------------------------------------------------------
    def test_get_annual_measures_not_empty(self):
        """Verifica que el dataset de medidas anuales se cargue correctamente con 24 años de historia."""
        df = self.data_service.get_annual_measures()
        self.assertFalse(df.empty, "El dataset anual no debe estar vacío")
        self.assertIn("department", df.columns)
        self.assertIn("cases_men5", df.columns)
        self.assertIn("cases_60mas", df.columns)
        self.assertIn("population", df.columns)
        
        # Verificar rango de años (2000 a 2023)
        self.assertEqual(df["year"].min(), 2000)
        self.assertEqual(df["year"].max(), 2023)

    def test_departments_count(self):
        """Verifica que se encuentren los departamentos del Perú."""
        deptos = self.data_service.get_departments()
        self.assertGreaterEqual(len(deptos), 24, "Deben existir al menos 24 departamentos")
        self.assertIn("LIMA", [d.upper() for d in deptos])
        self.assertIn("CUSCO", [d.upper() for d in deptos])
        self.assertIn("AREQUIPA", [d.upper() for d in deptos])

    def test_national_summary_rates_calculation(self):
        """Verifica el cálculo de tasas de incidencia nacional por 100k hab."""
        nat = self.data_service.get_national_summary()
        self.assertFalse(nat.empty)
        self.assertIn("cases_rate_men5", nat.columns)
        self.assertIn("cases_rate_60mas", nat.columns)
        self.assertIn("hr_men5", nat.columns)
        self.assertIn("cfr_men5", nat.columns)
        self.assertIn("hr_60mas", nat.columns)
        self.assertIn("cfr_60mas", nat.columns)

        # Validación matemática: rate = (cases / pop) * 100000
        row = nat.iloc[0]
        expected_rate_men5 = round((row["cases_men5"] / row["population"]) * 100000, 2)
        self.assertAlmostEqual(row["cases_rate_men5"], expected_rate_men5, places=1)

    def test_get_department_data(self):
        """Verifica la extracción y cálculo de tasas departamentales (Lima y Ucayali)."""
        for depto in ["LIMA", "UCAYALI", "CUSCO"]:
            df_dep = self.data_service.get_department_data(depto)
            self.assertFalse(df_dep.empty)
            self.assertEqual(df_dep["department"].iloc[0], depto)
            self.assertIn("hr_men5", df_dep.columns)
            self.assertIn("cfr_men5", df_dep.columns)
            self.assertIn("hr_60mas", df_dep.columns)
            self.assertIn("cfr_60mas", df_dep.columns)
            # Verificar no negatividad de indicadores
            self.assertTrue((df_dep["hr_men5"] >= 0).all())
            self.assertTrue((df_dep["cfr_men5"] >= 0).all())

    def test_kpi_computation(self):
        """Valida que los KPIs para las tarjetas de la interfaz se calculen coherentemente."""
        nat = self.data_service.get_national_summary()
        # Prueba con año explícito
        kpis_2023 = self.data_service.compute_kpis(nat, group="men5", year=2023)
        self.assertIn("cases", kpis_2023)
        self.assertIn("cases_rate", kpis_2023)
        self.assertIn("hr", kpis_2023)
        self.assertIn("cfr", kpis_2023)
        self.assertGreater(kpis_2023["cases"], 0)

        # Prueba con año None (debe tomar automáticamente el año más reciente)
        kpis_auto = self.data_service.compute_kpis(nat, group="60mas", year=None)
        self.assertEqual(kpis_auto["year"], 2023)
        self.assertIn("delta_cases_pct", kpis_auto)
        self.assertIn("delta_rate", kpis_auto)

    def test_rank_grid_and_top3_frequencies(self):
        """Verifica la carga de tablas de ranking anual y persistencia en Top 3."""
        for grp in ["men5", "60mas"]:
            grid = self.data_service.get_rank_grid(group=grp)
            self.assertIsInstance(grid, pd.DataFrame)

            top3 = self.data_service.get_top3_frequencies(group=grp)
            self.assertIsInstance(top3, pd.DataFrame)
            if not top3.empty:
                self.assertIn("region", top3.columns)
                self.assertIn("top3_appearances", top3.columns)

    def test_severity_annual_series(self):
        """Verifica la serie anual de severidad clínica (HR y CFR)."""
        for grp in ["men5", "60mas"]:
            sev = self.data_service.get_severity_annual_series(group=grp)
            self.assertFalse(sev.empty)
            self.assertIn("year", sev.columns)

    # --------------------------------------------------------------------------
    # PRUEBAS DEL SERVICIO DE MODELOS (ModelService)
    # --------------------------------------------------------------------------
    def test_model_metrics(self):
        """Verifica que las métricas de los modelos predictivos se carguen según los resultados oficiales."""
        for grp in ["men5", "60mas"]:
            metrics = self.model_service.get_national_metrics(group=grp)
            self.assertFalse(metrics.empty)
            self.assertIn("r2", metrics.columns)
            self.assertIn("mae", metrics.columns)
            self.assertIn("rmse", metrics.columns)

            xgb_row = metrics[metrics["model"].str.lower().str.contains("xgboost")]
            if not xgb_row.empty:
                expected_min_r2 = 0.90 if grp == "men5" else 0.85
                self.assertGreater(float(xgb_row["r2"].values[0]), expected_min_r2)

    def test_national_weekly_series(self):
        """Verifica la carga de series históricas semanales observadas."""
        for grp in ["men5", "60mas"]:
            weekly = self.model_service.get_national_weekly_series(group=grp)
            self.assertIsInstance(weekly, pd.DataFrame)
            if not weekly.empty:
                self.assertIn("date", weekly.columns)

    def test_national_predictions(self):
        """Verifica la carga de predicciones históricas rodantes."""
        for grp in ["men5", "60mas"]:
            preds = self.model_service.get_national_predictions(group=grp)
            self.assertIsInstance(preds, pd.DataFrame)
            if not preds.empty:
                self.assertIn("date", preds.columns)

    def test_future_predictions(self):
        """Verifica que las proyecciones a 52 semanas cuenten con intervalos de confianza válidos."""
        for grp in ["men5", "60mas"]:
            future_df = self.model_service.get_national_future_predictions(group=grp)
            self.assertFalse(future_df.empty)
            self.assertIn("predicted", future_df.columns)
            self.assertIn("lower_ci", future_df.columns)
            self.assertIn("upper_ci", future_df.columns)
            # El límite superior debe ser mayor o igual al inferior
            self.assertTrue((future_df["upper_ci"] >= future_df["lower_ci"]).all())

    def test_feature_importance_summary(self):
        """Verifica que las variables predictoras estén clasificadas por importancia."""
        for grp in ["men5", "60mas"]:
            feat_df = self.model_service.get_feature_importance_summary(group=grp)
            self.assertFalse(feat_df.empty)
            self.assertIn("feature", feat_df.columns)
            self.assertIn("importance", feat_df.columns)
            # La suma de importancias debe ser positiva
            self.assertGreater(feat_df["importance"].sum(), 0)


if __name__ == "__main__":
    unittest.main()
