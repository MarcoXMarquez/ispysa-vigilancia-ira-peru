"""
Pruebas unitarias para la batería de probes automáticos de calidad (src/quality/probes.py)
y el registrador de telemetría sin PII (src/services/usage_logger.py).
"""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import MagicMock

import pandas as pd

from src.quality.probes import (
    contrast_ratio,
    probe_bortman_order,
    probe_cache_resource,
    probe_component_redundancy,
    probe_contrast_ratio,
    probe_coverage,
    probe_coverage_pct,
    probe_cyclomatic_complexity,
    probe_data_manifest,
    probe_file_limits,
    probe_finite_rates,
    probe_forecast_bands,
    probe_hr_cfr,
    probe_incidence_formula,
    probe_latency_p95,
    probe_memory_growth,
    probe_population_nan,
    probe_service_init_time,
    probe_service_layer_isolation,
    probe_unit_tests,
    relative_luminance,
    run_all_probes,
)
from src.services.usage_logger import log_usage_event


class TestQualityProbes(unittest.TestCase):
    """Pruebas funcionales y de robustez para los probes automáticos."""

    def test_probe_incidence_formula_valid_and_corrupt(self):
        res_ok = probe_incidence_formula()
        self.assertTrue(res_ok.value)

        mock_ds = MagicMock()
        corrupt_df = pd.DataFrame([
            {"department": "LIMA", "year": 2020, "cases_men5": 100, "population": 10000, "cases_rate_men5": 500.0,
             "cases_60mas": 50, "cases_rate_60mas": 250.0}
        ])
        mock_ds.get_department_data.return_value = corrupt_df
        res_fail = probe_incidence_formula(data_service=mock_ds)
        self.assertFalse(res_fail.value)

    def test_probe_hr_cfr_valid_and_corrupt(self):
        res_ok = probe_hr_cfr()
        self.assertTrue(res_ok.value)

        mock_ds = MagicMock()
        nat_corrupt = pd.DataFrame([
            {"year": 2020, "cases_men5": 1000, "hosp_men5": 100, "death_men5": 20,
             "hr_men5": 11.5, "cfr_men5": 2.0, "cases_60mas": 500, "hosp_60mas": 50,
             "death_60mas": 10, "hr_60mas": 10.0, "cfr_60mas": 2.0}
        ])
        mock_ds.get_national_summary.return_value = nat_corrupt
        res_fail = probe_hr_cfr(data_service=mock_ds)
        self.assertFalse(res_fail.value)

    def test_probe_bortman_order(self):
        res = probe_bortman_order()
        self.assertTrue(res.value)

    def test_probe_coverage(self):
        res = probe_coverage()
        self.assertTrue(res.value)

    def test_probe_latency_p95_simulated_slow(self):
        res_ok = probe_latency_p95(iterations=3)
        self.assertTrue(res_ok.value)

        mock_ds = MagicMock()

        def very_slow():
            import time
            time.sleep(0.21)
            return pd.DataFrame()
        mock_ds.get_national_summary.side_effect = very_slow
        res_slow = probe_latency_p95(data_service=mock_ds, iterations=2)
        self.assertFalse(res_slow.value)

    def test_probe_service_init_time(self):
        res = probe_service_init_time()
        self.assertTrue(res.value)

    def test_probe_memory_growth(self):
        res = probe_memory_growth(iterations=10)
        self.assertTrue(res.value)

    def test_probe_cache_resource(self):
        res = probe_cache_resource()
        self.assertTrue(res.value)

    def test_probe_finite_rates(self):
        res = probe_finite_rates()
        self.assertTrue(res.value)

    def test_probe_population_nan(self):
        res = probe_population_nan()
        self.assertTrue(res.value)

    def test_probe_forecast_bands(self):
        res = probe_forecast_bands()
        self.assertTrue(res.value)

    def test_probe_unit_tests(self):
        res = probe_unit_tests()
        self.assertTrue(res.value)

    def test_probe_service_layer_isolation(self):
        res = probe_service_layer_isolation()
        self.assertTrue(res.value)

    def test_probe_cyclomatic_complexity(self):
        res = probe_cyclomatic_complexity()
        self.assertTrue(res.value)

    def test_probe_coverage_pct(self):
        res = probe_coverage_pct()
        self.assertTrue(res.value)

    def test_probe_file_limits(self):
        res = probe_file_limits()
        self.assertTrue(res.value)

    def test_probe_contrast_ratio_wcag(self):
        cr_max = contrast_ratio("#FFFFFF", "#000000")
        self.assertAlmostEqual(cr_max, 21.0, places=1)
        self.assertAlmostEqual(relative_luminance("#FFFFFF"), 1.0, places=2)
        self.assertAlmostEqual(relative_luminance("#000000"), 0.0, places=2)
        res = probe_contrast_ratio()
        self.assertTrue(res.value)

    def test_probe_component_redundancy(self):
        res = probe_component_redundancy()
        self.assertTrue(res.value)

    def test_probe_data_manifest(self):
        res = probe_data_manifest()
        self.assertTrue(res.value)

    def test_probe_exception_handling(self):
        mock_ds = MagicMock()
        mock_ds.get_department_data.side_effect = RuntimeError("Fallo de I/O forzado")
        res = probe_incidence_formula(data_service=mock_ds)
        self.assertIsNone(res.value)
        self.assertIsNone(res.measured)
        self.assertIn("Excepción en probe", res.evidence)

    def test_run_all_probes(self):
        all_res = run_all_probes()
        self.assertGreaterEqual(len(all_res), 18)
        self.assertIn("AF-1", all_res)
        self.assertIn("ED-1", all_res)
        self.assertIn("FI-1", all_res)
        self.assertIn("MA-1", all_res)
        self.assertIn("US-1", all_res)
        self.assertIn("NR-9", all_res)


class TestUsageLogger(unittest.TestCase):
    """Pruebas del logger rotativo sin PII (Fase 5-bis)."""

    def test_log_usage_event(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            rec = log_usage_event("filtro_cambiado", {"depto": "CUSCO", "grupo": "men5"}, root_dir=tmp_path)
            self.assertEqual(rec["event"], "filtro_cambiado")
            self.assertEqual(rec["params"]["depto"], "CUSCO")
            self.assertIn("timestamp", rec)

            log_file = tmp_path / "logs" / "usage.jsonl"
            self.assertTrue(log_file.exists())
            lines = log_file.read_text(encoding="utf-8").strip().splitlines()
            self.assertEqual(len(lines), 1)
            parsed = json.loads(lines[0])
            self.assertEqual(parsed["event"], "filtro_cambiado")
            # Verificar privacidad: no se registran IP ni user-agent
            self.assertNotIn("ip", parsed)
            self.assertNotIn("user_agent", parsed)


if __name__ == "__main__":
    unittest.main()
