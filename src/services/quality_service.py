"""
Servicio de Calidad de Producto Software ISO/IEC 25010 (GQM).
Fachada limpia para el cálculo de métricas y consulta de auditorías automatizadas
basadas en Calabrese et al. (2018).
"""
import csv
import io
import json
from pathlib import Path
from typing import Any, Dict, Optional

from src.quality.catalog import (
    ALL_QUESTIONS,
    CATALOG,
)
from src.quality.scoring import (
    classify,
    evaluate_catalog,
    score_security_subcharacteristics,
)


class ISO25010QualityService:
    """
    Fachada de servicios para auditoría y evaluación cuantitativa de calidad
    según la norma ISO/IEC 25010 y metodología GQM.
    """

    def __init__(self, root_dir: Optional[Path] = None):
        if root_dir is None:
            self.root_dir = Path(__file__).resolve().parents[2]
        else:
            self.root_dir = Path(root_dir)

        self.quality_data_dir = self.root_dir / "data" / "quality"
        self.last_audit_file = self.quality_data_dir / "last_audit.json"
        self.respuestas_csv = self.quality_data_dir / "respuestas.csv"

    def get_last_audit(self) -> Optional[Dict[str, Any]]:
        """Lee y retorna el último informe de auditoría persistido en data/quality/last_audit.json."""
        if not self.last_audit_file.exists():
            return None
        try:
            return json.loads(self.last_audit_file.read_text(encoding="utf-8"))
        except Exception:
            return None

    def run_audit(self) -> Dict[str, Any]:
        """Ejecuta una nueva auditoría automatizada completa."""
        from scripts.run_quality_audit import run_audit
        return run_audit(self.root_dir)

    def load_answers_from_csv(self) -> Dict[str, Optional[bool]]:
        """Carga el diccionario de respuestas activas desde data/quality/respuestas.csv."""
        answers: Dict[str, Optional[bool]] = {}
        if not self.respuestas_csv.exists():
            return answers

        with open(self.respuestas_csv, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for r in reader:
                qid = r.get("id", "").strip()
                resp = r.get("respuesta", "").strip().upper()
                if resp == "SI":
                    answers[qid] = True
                elif resp == "NO":
                    answers[qid] = False
                elif resp == "NA":
                    answers[qid] = None
                else:
                    answers[qid] = False
        return answers

    def evaluate_product_quality(
        self,
        custom_responses: Optional[Dict[str, Any]] = None,
        strict: bool = False
    ) -> Dict[str, Any]:
        """
        Calcula las métricas de calidad para la norma ISO/IEC 25010.
        Si custom_responses es None y existe last_audit.json, reutiliza los datos auditados.
        Si se proporcionan custom_responses, recalcula en memoria de forma pura.
        """
        if custom_responses is None:
            last = self.get_last_audit()
            if last is not None:
                return self._format_from_last_audit(last)
            answers = self.load_answers_from_csv()
        else:
            answers = self._normalize_custom_responses(custom_responses)

        # Evaluación pura
        eval_res = evaluate_catalog(answers, strict=strict)
        sec_scores = score_security_subcharacteristics(answers, strict=strict)

        iq_global = eval_res["global_index"]
        weak_ok = eval_res["weak_link_passed"]
        is_passed = weak_ok and (iq_global >= 60.0)

        # Estructura compatible con interfaz visual y pruebas
        chars_dict = {}
        for char in CATALOG:
            score = eval_res["characteristics"].get(char.name, 0.0)
            entry: Dict[str, Any] = {
                "puntaje": round(score, 1),
                "rango": classify(score),
            }
            if char.id == "SEG":
                entry["subcaracteristicas"] = {
                    sub: round(val, 1) if val is not None else 0.0
                    for sub, val in sec_scores.items()
                }
            chars_dict[char.name] = entry

        # Compatibilidad con alias 'Seguridad (Modelo UNLP)'
        if "Seguridad" in chars_dict:
            chars_dict["Seguridad (Modelo UNLP)"] = chars_dict["Seguridad"]

        return {
            "caracteristicas": chars_dict,
            "iq_salud_global": round(iq_global, 1),
            "iq_salud_global_equal_weights": round(eval_res["global_index_equal_weights"], 1),
            "rango_global": classify(iq_global),
            "estado_evaluacion": "APROBADO (EXCELENCIA TÉCNICA)" if iq_global >= 90.0 else (
                "APROBADO (CONFORME)" if is_passed else "REPROBADO"
            ),
            "weak_link": {
                "passed": weak_ok,
                "message": eval_res["weak_link_message"],
            },
            "cobertura_aplicabilidad": eval_res["security_applicability_coverage"],
            "criteria_scores": eval_res["criteria"],
        }

    def _format_from_last_audit(self, audit: Dict[str, Any]) -> Dict[str, Any]:
        """Da formato a los resultados de last_audit.json para consumo de la UI."""
        chars_dict = {}
        for char in CATALOG:
            score = audit.get("scores", {}).get(char.name, 0.0)
            entry: Dict[str, Any] = {
                "puntaje": round(score, 1),
                "rango": classify(score),
            }
            if char.id == "SEG":
                entry["subcaracteristicas"] = audit.get("security", {}).get("applicable_scores", {})
            chars_dict[char.name] = entry

        if "Seguridad" in chars_dict:
            chars_dict["Seguridad (Modelo UNLP)"] = chars_dict["Seguridad"]

        iq = audit.get("global_index", 0.0)
        return {
            "caracteristicas": chars_dict,
            "iq_salud_global": round(iq, 1),
            "iq_salud_global_equal_weights": round(audit.get("global_index_equal_weights", 0.0), 1),
            "rango_global": classify(iq),
            "estado_evaluacion": "APROBADO (EXCELENCIA TÉCNICA)" if iq >= 90.0 else (
                "APROBADO (CONFORME)" if audit.get("status") == "APROBADO" else "REPROBADO"
            ),
            "weak_link": audit.get("weak_link", {"passed": True, "message": "OK"}),
            "cobertura_aplicabilidad": audit.get("security", {}).get("applicability_coverage", "15/15"),
            "audit_meta": {
                "generated_at": audit.get("generated_at"),
                "git_commit": audit.get("git_commit"),
            },
        }

    def _normalize_custom_responses(self, custom: Dict[str, Any]) -> Dict[str, Optional[bool]]:
        """Mapea respuestas personalizadas (incluyendo claves legacy Q1_1..Q6_4)."""
        answers: Dict[str, Optional[bool]] = {}
        legacy_map = {
            "Q1_1": "AF-1", "Q1_2": "AF-2", "Q1_3": "AF-3", "Q1_4": "AF-4", "Q1_5": "AF-5",
            "Q2_1": "ED-1", "Q2_2": "ED-4", "Q2_3": "ED-3", "Q2_4": "ED-2",
            "Q3_1": "FI-1", "Q3_2": "FI-2", "Q3_3": "FI-3", "Q3_4": "FI-4",
            "Q5_1": "MA-1", "Q5_2": "MA-2", "Q5_3": "MA-3", "Q5_4": "MA-4",
            "Q6_1": "US-1", "Q6_2": "US-2", "Q6_3": "US-3", "Q6_4": "US-4",
        }
        for k, v in custom.items():
            target_id = legacy_map.get(k, k)
            if v is None or v == "NA":
                answers[target_id] = None
            elif isinstance(v, bool):
                answers[target_id] = v
            elif str(v).upper() in ("SI", "TRUE", "1"):
                answers[target_id] = True
            elif str(v).upper() in ("NO", "FALSE", "0"):
                answers[target_id] = False
            else:
                answers[target_id] = False
        return answers

    def get_blank_template_csv(self) -> str:
        """Retorna la plantilla CSV en blanco con cabeceras y catálogo de preguntas."""
        buf = io.StringIO()
        fieldnames = [
            "id", "caracteristica", "subcaracteristica", "pregunta", "respuesta",
            "origen", "evidencia", "justificacion", "verificado_por", "fecha"
        ]
        writer = csv.DictWriter(buf, fieldnames=fieldnames)
        writer.writeheader()
        for q in ALL_QUESTIONS:
            writer.writerow({
                "id": q.id,
                "caracteristica": q.characteristic,
                "subcaracteristica": q.subcharacteristic,
                "pregunta": q.question,
                "respuesta": "",
                "origen": q.origin,
                "evidencia": "",
                "justificacion": "",
                "verificado_por": "",
                "fecha": "",
            })
        return buf.getvalue()
