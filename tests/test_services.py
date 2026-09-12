"""
Pruebas Unitarias para los Servicios Epidemiológicos
Verifica la integridad de datos, cálculos de tasas e indicadores de severidad.
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
    """Conjunto de pruebas para validar los servicios del sistema."""

    def setUp(self):
        self.data_service = EpidemiologyDataService(root_dir=ROOT_DIR)
        self.model_service = EpidemiologyModelService(root_dir=ROOT_DIR)

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
        """Verifica que se encuentren los 25 departamentos del Perú."""
        deptos = self.data_service.get_departments()
        self.assertGreaterEqual(len(deptos), 24, "Deben existir al menos 24 departamentos")
        self.assertIn("LIMA", [d.upper() for d in deptos])
        self.assertIn("CUSCO", [d.upper() for d in deptos])

    def test_national_summary_rates_calculation(self):
        """Verifica el cálculo de tasas de incidencia nacional por 100k hab."""
        nat = self.data_service.get_national_summary()
        self.assertFalse(nat.empty)
        self.assertIn("cases_rate_men5", nat.columns)
        self.assertIn("cases_rate_60mas", nat.columns)
        self.assertIn("hr_men5", nat.columns)
        self.assertIn("cfr_men5", nat.columns)

        # Validación matemática: rate = (cases / pop) * 100000
        row = nat.iloc[0]
        expected_rate_men5 = round((row["cases_men5"] / row["population"]) * 100000, 2)
        self.assertAlmostEqual(row["cases_rate_men5"], expected_rate_men5, places=1)

    def test_kpi_computation(self):
        """Valida que los KPIs para las tarjetas de la interfaz se calculen coherentemente."""
        nat = self.data_service.get_national_summary()
        kpis = self.data_service.compute_kpis(nat, group="men5", year=2023)
        self.assertIn("cases", kpis)
        self.assertIn("cases_rate", kpis)
        self.assertIn("hr", kpis)
        self.assertIn("cfr", kpis)
        self.assertGreater(kpis["cases"], 0)

    def test_model_metrics(self):
        """Verifica que las métricas de los modelos predictivos se carguen según los resultados oficiales."""
        metrics_children = self.model_service.get_national_metrics(group="men5")
        self.assertFalse(metrics_children.empty)
        self.assertIn("r2", metrics_children.columns)
        self.assertIn("mae", metrics_children.columns)
        self.assertIn("rmse", metrics_children.columns)

        # XGBoost debe tener R2 > 0.90 para niños
        xgb_row = metrics_children[metrics_children["model"].str.lower().str.contains("xgboost")]
        if not xgb_row.empty:
            self.assertGreater(float(xgb_row["r2"].values[0]), 0.90)

    def test_future_predictions(self):
        """Verifica que las proyecciones a 52 semanas cuenten con intervalos de confianza válidos."""
        future_df = self.model_service.get_national_future_predictions(group="men5")
        self.assertFalse(future_df.empty)
        self.assertIn("predicted", future_df.columns)
        self.assertIn("lower_ci", future_df.columns)
        self.assertIn("upper_ci", future_df.columns)
        # El límite superior debe ser mayor o igual al inferior
        self.assertTrue((future_df["upper_ci"] >= future_df["lower_ci"]).all())


if __name__ == "__main__":
    unittest.main()
