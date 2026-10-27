"""
Pruebas unitarias para ISO25010QualityService (Trabajo Parcial 6).
Verifica la fachada de calidad, integración con last_audit.json y evaluación dinámica.
"""
from pathlib import Path
import unittest
from unittest.mock import patch

from src.services.quality_service import ISO25010QualityService


class TestISO25010QualityService(unittest.TestCase):
    def setUp(self):
        self.service = ISO25010QualityService()

    def test_default_evaluation_passes(self):
        result = self.service.evaluate_product_quality()
        self.assertIn("caracteristicas", result)
        self.assertIn("iq_salud_global", result)
        self.assertGreaterEqual(result["iq_salud_global"], 60.0)
        self.assertIn("APROBADO", result["estado_evaluacion"])
        self.assertIn("weak_link", result)
        self.assertIn("cobertura_aplicabilidad", result)

    def test_security_subcharacteristics_unlp(self):
        result = self.service.evaluate_product_quality()
        seg = result["caracteristicas"]["Seguridad (Modelo UNLP)"]
        sub = seg["subcaracteristicas"]
        self.assertIn("Confidencialidad", sub)
        self.assertIn("Integridad", sub)
        self.assertIn("No repudio", sub)
        self.assertIn("Responsabilidad", sub)
        self.assertIn("Autenticidad", sub)

    def test_custom_degraded_scenario_fails(self):
        # Simulación de fallas masivas de seguridad (brechas activadas)
        custom = {f"Q{i}": False for i in range(1, 34)}
        custom["Q7"] = True
        custom["Q8"] = True
        custom["Q14"] = True
        custom["Q16"] = True

        result = self.service.evaluate_product_quality(custom_responses=custom, strict=True)
        seg = result["caracteristicas"]["Seguridad (Modelo UNLP)"]
        self.assertLess(seg["puntaje"], 40.0)
        self.assertEqual(seg["rango"], "No aceptable")
        self.assertFalse(result["weak_link"]["passed"])

    def test_custom_legacy_keys_mapping(self):
        """Verifica que acepte claves legacy Q1_1..Q6_4."""
        custom = {"Q1_1": True, "Q1_2": True, "Q1_3": True, "Q1_4": True, "Q1_5": True}
        norm = self.service._normalize_custom_responses(custom)
        self.assertTrue(norm["AF-1"])
        self.assertTrue(norm["AF-2"])
        self.assertTrue(norm["AF-3"])
        self.assertTrue(norm["AF-4"])
        self.assertTrue(norm["AF-5"])

    def test_load_answers_from_csv(self):
        answers = self.service.load_answers_from_csv()
        self.assertIn("AF-1", answers)
        self.assertIn("Q5", answers)
        self.assertIsNone(answers.get("Q1"))  # Q1 es NA -> None

    def test_blank_template_csv(self):
        csv_text = self.service.get_blank_template_csv()
        self.assertIn("id,caracteristica,subcaracteristica", csv_text)
        self.assertIn("AF-1", csv_text)
        self.assertIn("Q33", csv_text)

    def test_get_last_audit(self):
        audit = self.service.get_last_audit()
        self.assertIsNotNone(audit)
        self.assertIn("git_commit", audit)
        self.assertIn("status", audit)

    def test_get_last_audit_missing_file(self):
        with patch.object(self.service, "last_audit_file", Path("/tmp/nonexistent_audit.json")):
            self.assertIsNone(self.service.get_last_audit())

    def test_format_from_last_audit_fallback(self):
        fake_audit = {
            "global_index": 75.0,
            "global_index_equal_weights": 75.0,
            "status": "APROBADO",
            "scores": {"Adecuación funcional": 80.0, "Seguridad": 70.0},
            "security": {"applicable_scores": {"Confidencialidad": 75.0}},
            "weak_link": {"passed": True, "message": "OK"},
        }
        res = self.service._format_from_last_audit(fake_audit)
        self.assertEqual(res["iq_salud_global"], 75.0)
        self.assertEqual(res["estado_evaluacion"], "APROBADO (CONFORME)")


if __name__ == "__main__":
    unittest.main()
