"""
Pruebas unitarias de integridad para el catálogo ISO/IEC 25010 y data/quality/respuestas.csv.
Verifica que exista una correspondencia biyectiva exacta (sin preguntas sueltas),
que no existan campos obligatorios vacíos y que no haya auto-aprobaciones ficticias con 'TODO'.
"""
import csv
from pathlib import Path
import re
import unittest

from src.quality.catalog import (
    ALL_CRITERIA,
    ALL_QUESTIONS,
    CATALOG,
    QUESTIONS_BY_ID,
)


class TestQualityCatalogIntegrity(unittest.TestCase):
    """Verificación formal de integridad de catálogo y fuente de verdad CSV."""

    def setUp(self):
        self.root_dir = Path(__file__).resolve().parents[1]
        self.csv_path = self.root_dir / "data" / "quality" / "respuestas.csv"

    def test_catalog_dataclasses_immutable(self):
        """Verifica que las dataclasses del catálogo sean estrictamente inmutables (frozen)."""
        q = ALL_QUESTIONS[0]
        with self.assertRaises(Exception):
            q.question = "Pregunta modificada"  # type: ignore

        c = ALL_CRITERIA[0]
        with self.assertRaises(Exception):
            c.name = "Nombre modificado"  # type: ignore

    def test_respuestas_csv_exists_and_loads(self):
        """El archivo respuestas.csv debe existir y ser legible como CSV estándar."""
        self.assertTrue(self.csv_path.exists(), "respuestas.csv no existe")
        with open(self.csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        self.assertGreaterEqual(len(rows), 54)

    def test_bijection_between_catalog_and_csv(self):
        """Correspondencia biyectiva exacta: ni una pregunta más, ni una menos."""
        with open(self.csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            csv_ids = [r["id"].strip() for r in reader]

        cat_ids = [q.id for q in ALL_QUESTIONS]

        # Verificar unicidad de IDs
        self.assertEqual(len(csv_ids), len(set(csv_ids)), "Hay IDs duplicados en respuestas.csv")
        self.assertEqual(len(cat_ids), len(set(cat_ids)), "Hay IDs duplicados en CATALOG")

        # Comprobar conjuntos idénticos
        missing_in_csv = set(cat_ids) - set(csv_ids)
        extra_in_csv = set(csv_ids) - set(cat_ids)
        self.assertEqual(missing_in_csv, set(), f"Preguntas del catálogo faltantes en CSV: {missing_in_csv}")
        self.assertEqual(extra_in_csv, set(), f"Preguntas extrañas en CSV no reconocidas: {extra_in_csv}")

    def test_mandatory_evidence_and_justification(self):
        """
        Principio de honestidad:
        - NA exige justificación no vacía.
        - DOCUMENTAL (SI/NO) exige evidencia verificable con referencia exacta.
        - Ninguna respuesta SI contiene el literal TODO o PENDIENTE.
        """
        with open(self.csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for r in reader:
                qid = r["id"]
                resp = r.get("respuesta", "").strip()
                orig = r.get("origen", "").strip()
                ev = r.get("evidencia", "").strip()
                just = r.get("justificacion", "").strip()

                if resp == "NA":
                    self.assertTrue(
                        len(just) > 0,
                        f"Pregunta {qid} marcada como NA carece de justificación escrita"
                    )

                if orig == "DOCUMENTAL" and resp in ("SI", "NO"):
                    self.assertTrue(
                        len(ev) > 0,
                        f"Pregunta {qid} ({orig}) con respuesta {resp} carece de evidencia documental"
                    )

                if resp == "SI":
                    has_todo = bool(re.search(r"\b(TODO|PENDIENTE)\b", ev, re.IGNORECASE))
                    self.assertFalse(
                        has_todo,
                        f"Pregunta {qid} auto-aprobada (SI) contiene TODO/pendiente en evidencia"
                    )

    def test_security_questions_unlp_count(self):
        """El modelo UNLP debe contener exactamente las 33 preguntas Q1 a Q33 y 15 criterios."""
        q_seg_ids = [f"Q{i}" for i in range(1, 34)]
        for qid in q_seg_ids:
            self.assertIn(qid, QUESTIONS_BY_ID, f"Pregunta UNLP {qid} falta en el catálogo")

        # 15 criterios en catálogo para Seguridad
        sec_char = next(c for c in CATALOG if c.id == "SEG")
        all_sec_crit_ids = [c.id for sub in sec_char.subcharacteristics for c in sub.criteria]
        self.assertEqual(len(all_sec_crit_ids), 15, "Deben existir exactamente 15 criterios para Seguridad")


if __name__ == "__main__":
    unittest.main()
