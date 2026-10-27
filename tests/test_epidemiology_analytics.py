"""
Pruebas Unitarias para el Módulo de Analítica Epidemiológica Avanzada.
Valida el Canal Endémico de Bortman, el Triaje Manchester y la Matriz Bioclimática.
"""

import unittest
from pathlib import Path
import pandas as pd

from src.epidemiology_analytics import (
    compute_bortman_corridor,
    compute_manchester_and_resources,
    compute_bioclimatic_vulnerability,
)
from src.services.data_service import EpidemiologyDataService


class TestEpidemiologyAnalytics(unittest.TestCase):
    def setUp(self):
        self.root_dir = Path(__file__).resolve().parents[1]
        self.data_service = EpidemiologyDataService(self.root_dir)

    def test_bortman_corridor_quartiles_ordering(self):
        """Verifica que Q1 <= Q2 <= Q3 y la asignación correcta de zonas."""
        dummy_df = pd.DataFrame({
            "rate": [10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0, 80.0]
        })
        res = compute_bortman_corridor(dummy_df, "rate", target_value=35.0)
        self.assertLessEqual(res["q1"], res["q2"])
        self.assertLessEqual(res["q2"], res["q3"])
        self.assertEqual(res["zone_code"], "SEGURIDAD")

        # Test epidemic zone
        res_epi = compute_bortman_corridor(dummy_df, "rate", target_value=90.0)
        self.assertEqual(res_epi["zone_code"], "EPIDEMIA")

        # Test alarm zone
        res_alarm = compute_bortman_corridor(dummy_df, "rate", target_value=55.0)
        self.assertEqual(res_alarm["zone_code"], "ALARMA")

        # Test success zone
        res_succ = compute_bortman_corridor(dummy_df, "rate", target_value=5.0)
        self.assertEqual(res_succ["zone_code"], "EXITO")

    def test_manchester_resources_computation(self):
        """Verifica la coherencia en la estimación de UCI y demanda de oxígeno."""
        res_ped = compute_manchester_and_resources(hospitalizations=100, cases=1000, group="men5")
        self.assertEqual(res_ped["hospitalizations"], 100)
        self.assertGreater(res_ped["icu_beds_estimated"], 0)
        self.assertGreater(res_ped["oxygen_demand_m3_day"], 0)
        self.assertEqual(len(res_ped["triage_df"]), 5)

        # Geriátrico requiere mayor proporción de UCI
        res_ger = compute_manchester_and_resources(hospitalizations=100, cases=1000, group="60mas")
        self.assertGreaterEqual(res_ger["icu_beds_estimated"], res_ped["icu_beds_estimated"])

    def test_bioclimatic_vulnerability_matrix(self):
        """Verifica la generación de la matriz bioclimática con 25 departamentos."""
        df_annual = self.data_service.get_annual_measures()
        res_bio = compute_bioclimatic_vulnerability(df_annual, year=2023, group="men5")
        self.assertEqual(len(res_bio), 25)
        self.assertIn("climate_zone", res_bio.columns)
        self.assertIn("composite_risk_score", res_bio.columns)
        # Comprobar orden descendente por score
        scores = res_bio["composite_risk_score"].tolist()
        self.assertEqual(scores, sorted(scores, reverse=True))


if __name__ == "__main__":
    unittest.main()
