"""
Pruebas unitarias para el motor de puntuación de calidad ISO/IEC 25010 y GQM.
Valida la reproducción estricta de los Casos de Estudio a, b, c de Calabrese et al. (2018),
la clasificación de rangos, la regla de la cadena débil y el manejo de aplicabilidad.
"""
import unittest

from src.quality.catalog import CriterionExpr
from src.quality.scoring import (
    classify,
    evaluate_criterion,
    global_index,
    score_security_subcharacteristics,
    score_subcharacteristic,
    weak_link_status,
)


class TestQualityScoringUNLP(unittest.TestCase):
    """
    Validación formal de la reproducción de los casos de estudio publicados por
    Calabrese et al. (2018) 'Assistant for the Evaluation of Software Product Quality
    Characteristics Proposed by ISO/IEC 25010 Based on GQM-Defined Metrics' (§4.4 y §4.5).
    """

    def test_paper_case_a(self):
        """
        Caso a (Sistema en producción, 18 meses, >3200 usuarios):
        Resultados esperados en el paper:
        - Confidencialidad: 88 % (3.5 / 4 = 87.5 %, redondeado a 88 %)
        - Integridad: 67 % (2.0 / 3 = 66.67 %, redondeado a 67 %)
        - No Repudio: 50 % (2.0 / 4 = 50 %)
        - Responsabilidad: 50 % (1.0 / 2 = 50 %)
        - Autenticidad: 0 % (0.0 / 2 = 0 %)
        Veredicto del paper: REPROBADO por Autenticidad = 0 % (< 40 %).
        """
        answers_a = {f"Q{i}": False for i in range(1, 34)}
        # C-4 Contraseña de nivel medio (0.5 ptos)
        answers_a["Q1"] = True
        # C-1 Conexión HTTPS sin redirección insegura (1.0 pto)
        answers_a["Q5"] = True
        # C-3 Datos cifrados en base de datos (1.0 pto)
        answers_a["Q6"] = True
        # C-2 Sin accesos indebidos (Q7..Q11 son False -> 1.0 pto)
        # Suma Confidencialidad = 1.0 + 1.0 + 1.0 + 0.5 = 3.5 / 4 = 87.5 %

        # I-5 Sin acceso indebido ni inyección SQL (Q7..Q9, Q16 son False -> 1.0 pto)
        # I-6 Sin modificación no autorizada (Q14, Q15 son False -> 1.0 pto)
        # I-7 Sin confirmación de email (Q13 es False -> 0.0 ptos)
        # Suma Integridad = 2.0 / 3 = 66.67 %

        # NR-8 Historial de acciones (Q17 es True -> 1.0 pto)
        answers_a["Q17"] = True
        # NR-9 Certificado SSL activo (Q21 es True -> 1.0 pto)
        answers_a["Q21"] = True
        # NR-10 Sin confirmación de acción (Q20 es False -> 0.0)
        # NR-11 Sin advertencia de ubicación (Q22 es False -> 0.0)
        # Suma No Repudio = 2.0 / 4 = 50 %

        # R-12 Historial de acciones registrado (Q17 es True -> 1.0 pto)
        # R-13 Sin control de ubicación (Q22 es False -> 0.0)
        # Suma Responsabilidad = 1.0 / 2 = 50 %

        # A-14 Sin método de autenticación primaria (0.0 ptos)
        # A-15 Sin verificación adicional ni 2FA (0.0 ptos)
        # Suma Autenticidad = 0.0 / 2 = 0 %

        scores = score_security_subcharacteristics(answers_a, strict=True)

        self.assertAlmostEqual(scores["Confidencialidad"], 87.5, places=1)
        self.assertEqual(round(scores["Confidencialidad"]), 88)

        self.assertAlmostEqual(scores["Integridad"], 66.67, places=1)
        self.assertEqual(round(scores["Integridad"]), 67)

        self.assertEqual(scores["No repudio"], 50.0)
        self.assertEqual(scores["Responsabilidad"], 50.0)
        self.assertEqual(scores["Autenticidad"], 0.0)

        # Regla de la cadena débil: reprobado por Autenticidad
        weak_ok, weak_msg = weak_link_status(scores)
        self.assertFalse(weak_ok)
        self.assertIn("Autenticidad", weak_msg)

    def test_paper_case_b(self):
        """
        Caso b (Sistema en producción, 30 meses, 160 usuarios):
        Resultados esperados en el paper:
        - Confidencialidad: 75 % (3.0 / 4 = 75 %)
        - Integridad: 100 % (3.0 / 3 = 100 %)
        - No Repudio: 75 % (3.0 / 4 = 75 %)
        - Responsabilidad: 50 % (1.0 / 2 = 50 %)
        - Autenticidad: 50 % (1.0 / 2 = 50 %)
        Veredicto del paper: APROBADO (todas las subcaracterísticas >= 50 %).
        """
        answers_b = {f"Q{i}": False for i in range(1, 34)}
        # C-4 Contraseña de nivel alto (1.0 pto)
        answers_b["Q1"] = answers_b["Q2"] = answers_b["Q3"] = answers_b["Q4"] = True
        # C-1 Conexión HTTPS (1.0 pto)
        answers_b["Q5"] = True
        # C-2 Control de acceso seguro (1.0 pto)
        # C-3 Sin cifrado de BD (Q6 es False -> 0.0 ptos)
        # Confidencialidad = 3.0 / 4 = 75 %

        # I-5 Sin acceso indebido (1.0 pto)
        # I-6 Sin modificación arbitraria (1.0 pto)
        # I-7 Confirmación de registro por email (Q13 es True -> 1.0 pto)
        answers_b["Q13"] = True
        # Integridad = 3.0 / 3 = 100 %

        # NR-8 Historial de acciones (Q17 es True -> 1.0 pto)
        answers_b["Q17"] = True
        # NR-9 Certificado SSL (Q21 es True -> 1.0 pto)
        answers_b["Q21"] = True
        # NR-10 Confirmación de acción (Q20 es True -> 1.0 pto)
        answers_b["Q20"] = True
        # NR-11 Sin alerta de ubicación (0.0 ptos)
        # No Repudio = 3.0 / 4 = 75 %

        # R-12 Historial registrado (Q17 es True -> 1.0 pto)
        # R-13 Sin control de ubicación (0.0 ptos)
        # Responsabilidad = 1.0 / 2 = 50 %

        # A-14 Sin método primario (0.0 ptos)
        # A-15 Verificación por email (Q13 es True -> 1.0 pto)
        # Autenticidad = 1.0 / 2 = 50 %

        scores = score_security_subcharacteristics(answers_b, strict=True)

        self.assertEqual(scores["Confidencialidad"], 75.0)
        self.assertEqual(scores["Integridad"], 100.0)
        self.assertEqual(scores["No repudio"], 75.0)
        self.assertEqual(scores["Responsabilidad"], 50.0)
        self.assertEqual(scores["Autenticidad"], 50.0)

        # Regla de la cadena débil: aprobado
        weak_ok, weak_msg = weak_link_status(scores)
        self.assertTrue(weak_ok)

    def test_paper_case_c(self):
        """
        Caso c (Fase de pruebas, 10 usuarios):
        Resultados esperados en el paper:
        - Confidencialidad: 0 %
        - Integridad: 33 % (1.0 / 3 = 33.33 %, redondeado a 33 %)
        - No Repudio: 50 % (2.0 / 4 = 50 %)
        - Responsabilidad: 0 %
        - Autenticidad: 0 %
        Veredicto del paper: REPROBADO por múltiples fallas críticas.
        """
        answers_c = {f"Q{i}": False for i in range(1, 34)}
        # Q7 es True (permite accesos indebidos sin permiso)
        answers_c["Q7"] = True
        # NR-9 SSL activo (Q21 es True -> 1.0 pto)
        answers_c["Q21"] = True
        # NR-8 Reporte por email (Q23 es True -> 1.0 pto)
        answers_c["Q23"] = True

        scores = score_security_subcharacteristics(answers_c, strict=True)

        self.assertEqual(scores["Confidencialidad"], 0.0)
        self.assertAlmostEqual(scores["Integridad"], 33.33, places=1)
        self.assertEqual(round(scores["Integridad"]), 33)
        self.assertEqual(scores["No repudio"], 50.0)
        self.assertEqual(scores["Responsabilidad"], 0.0)
        self.assertEqual(scores["Autenticidad"], 0.0)

        weak_ok, _ = weak_link_status(scores)
        self.assertFalse(weak_ok)


class TestScoringFunctions(unittest.TestCase):
    """Pruebas de funciones auxiliares: clasificación, N/A, cadena débil e índice global."""

    def test_classify_thresholds(self):
        """Verifica los 4 rangos de aceptabilidad de Calabrese et al. §4.2."""
        self.assertEqual(classify(0.0), "No aceptable")
        self.assertEqual(classify(39.99), "No aceptable")
        self.assertEqual(classify(40.0), "Mínimamente aceptable")
        self.assertEqual(classify(59.99), "Mínimamente aceptable")
        self.assertEqual(classify(60.0), "Objetivo")
        self.assertEqual(classify(89.99), "Objetivo")
        self.assertEqual(classify(90.0), "Supera")
        self.assertEqual(classify(100.0), "Supera")

    def test_na_handling_strict_vs_applicable(self):
        """Un criterio con todas sus preguntas en None (N/A) se excluye en modo aplicable."""
        expr_single = CriterionExpr("single", ("Q6",))
        # Si Q6 es None (NO_APLICA)
        self.assertIsNone(evaluate_criterion({"Q6": None}, expr_single))

        # En subcaracterística con 3 criterios donde 1 es None
        criteria_scores = [1.0, 1.0, None]
        # Modo estricto: denominador fijo 3 -> 2/3 = 66.67 %
        strict_score = score_subcharacteristic(criteria_scores, strict=True)
        self.assertAlmostEqual(strict_score, 66.67, places=1)

        # Modo aplicable: denominador 2 -> 2/2 = 100.0 %
        app_score = score_subcharacteristic(criteria_scores, strict=False)
        self.assertEqual(app_score, 100.0)

        # Si todos los criterios son None, modo aplicable retorna None
        all_na_score = score_subcharacteristic([None, None], strict=False)
        self.assertIsNone(all_na_score)

    def test_global_index_validation(self):
        """Verifica cálculo ponderado y detección de suma inválida de pesos."""
        scores = {
            "Adecuación funcional": 100.0,
            "Eficiencia de desempeño": 100.0,
            "Fiabilidad": 100.0,
            "Seguridad": 100.0,
            "Mantenibilidad": 100.0,
            "Usabilidad": 100.0,
        }
        # Con pesos por defecto (suman 1.0)
        idx = global_index(scores)
        self.assertEqual(idx, 100.0)

        # Códigos cortos AF, ED, FI...
        idx_short = global_index(scores, {"AF": 0.25, "ED": 0.15, "FI": 0.20, "SEG": 0.15, "MA": 0.15, "US": 0.10})
        self.assertEqual(idx_short, 100.0)

        # Pesos que no suman 1.0 deben lanzar ValueError
        with self.assertRaises(ValueError):
            global_index(scores, {"AF": 0.50, "ED": 0.20})


if __name__ == "__main__":
    unittest.main()
