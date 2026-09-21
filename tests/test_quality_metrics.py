"""Tests for ISO/IEC 25000 product-quality measurement helpers."""

from pathlib import Path
from tempfile import TemporaryDirectory
import json
import unittest

from src.services.quality_metrics import (
    load_ci_metrics, metrics_from_evidence, usability_metrics, usability_template_csv,
)


class TestQualityMetrics(unittest.TestCase):
    def test_session_metrics_are_calculated_from_real_evidence(self):
        metrics = metrics_from_evidence([
            {"estado": "Verificado", "sha256": "abc", "leido_utc": "2026-01-01T00:00:00+00:00"},
            {"estado": "No válido"},
        ])
        by_id = {metric["id"]: metric for metric in metrics}
        self.assertEqual(by_id["validation_compliance_rate"]["value"], 50.0)
        self.assertEqual(by_id["traceable_source_rate"]["value"], 100.0)

    def test_missing_ci_evidence_is_not_reported_as_a_pass(self):
        with TemporaryDirectory() as temporary:
            metrics = load_ci_metrics(Path(temporary))
        self.assertTrue(all(metric["value"] is None for metric in metrics))
        self.assertTrue(all(metric["status"] == "No medido" for metric in metrics))

    def test_ci_evidence_is_loaded_when_valid(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            output = root / "quality-results"
            output.mkdir()
            (output / "ci_quality_metrics.json").write_text(json.dumps({
                "generated_at_utc": "2026-01-01T00:00:00+00:00", "commit": "abc123",
                "metrics": [
                    {"id": "service_test_coverage", "value": 97.0},
                    {"id": "critical_flake8_errors", "value": 0},
                ],
            }), encoding="utf-8")
            metrics = load_ci_metrics(root)
        self.assertEqual(metrics[0]["value"], 97.0)
        self.assertEqual(metrics[1]["status"], "Cumple la meta")

    def test_usability_metrics_require_observed_valid_rows(self):
        self.assertIn(b"id_participante", usability_template_csv())
        metrics = usability_metrics(
            b"id_participante,id_tarea,completada,duracion_segundos,claridad_1_a_5\np1,t1,yes,30,5\np1,t2,no,10,2\n"
        )
        self.assertEqual(metrics[0]["value"], 50.0)
        invalid = usability_metrics(b"id_participante,id_tarea\np1,t1\n")
        self.assertIsNone(invalid[0]["value"])


if __name__ == "__main__":
    unittest.main()
