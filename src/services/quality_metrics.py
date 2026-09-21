"""Indicadores reproducibles de calidad del producto para ISO/IEC 25000.

El módulo no inventa resultados: los indicadores de CI sólo se muestran cuando
existe la evidencia generada por el pipeline y los de usabilidad requieren una
captura explícita de tareas realizadas.
"""

from __future__ import annotations

from datetime import datetime, timezone
from io import BytesIO
import json
from pathlib import Path
from typing import Any, Iterable, Mapping

import pandas as pd


QUALITY_MODEL = [
    {
        "id": "validation_compliance_rate",
        "characteristic": "Adecuación funcional",
        "subcharacteristic": "Corrección funcional",
        "indicator": "Tasa de cumplimiento de validaciones",
        "formula": "contratos de validación verificados / contratos evaluados × 100",
        "unit": "%",
        "target": ">= 95%",
        "source": "Evidencia de validación de datos de la sesión",
        "frequency": "En cada sesión de la aplicación",
        "responsible": "Responsable de datos",
    },
    {
        "id": "traceable_source_rate",
        "characteristic": "Fiabilidad",
        "subcharacteristic": "Tolerancia a fallos",
        "indicator": "Tasa de fuentes trazables",
        "formula": "fuentes verificadas con SHA-256 y hora de lectura / fuentes verificadas × 100",
        "unit": "%",
        "target": "100%",
        "source": "Evidencia de fuentes de la sesión",
        "frequency": "En cada sesión de la aplicación",
        "responsible": "Responsable de datos",
    },
    {
        "id": "data_load_validation_ms",
        "characteristic": "Eficiencia del desempeño",
        "subcharacteristic": "Comportamiento temporal",
        "indicator": "Tiempo de carga y validación de datos",
        "formula": "hora final − hora inicial de carga y validación de datos anuales",
        "unit": "ms",
        "target": "Primero establecer línea base; no declarar un umbral sin medición",
        "source": "Cronómetro de la sesión de la aplicación",
        "frequency": "En cada sesión de la aplicación",
        "responsible": "Equipo de desarrollo",
    },
    {
        "id": "filter_indicator_ms",
        "characteristic": "Eficiencia del desempeño",
        "subcharacteristic": "Comportamiento temporal",
        "indicator": "Tiempo de filtros y cálculo de indicadores",
        "formula": "hora final − hora inicial de filtros y cálculo de indicadores",
        "unit": "ms",
        "target": "Primero establecer línea base; no declarar un umbral sin medición",
        "source": "Cronómetro de la sesión de la aplicación",
        "frequency": "En cada sesión de la aplicación",
        "responsible": "Equipo de desarrollo",
    },
    {
        "id": "service_test_coverage",
        "characteristic": "Mantenibilidad",
        "subcharacteristic": "Capacidad de prueba",
        "indicator": "Cobertura de pruebas de servicios",
        "formula": "líneas de servicios ejecutadas / líneas de servicios medibles × 100",
        "unit": "%",
        "target": ">= 80%",
        "source": "coverage.json de GitHub Actions",
        "frequency": "En cada pull request y push",
        "responsible": "Equipo de desarrollo",
    },
    {
        "id": "critical_flake8_errors",
        "characteristic": "Mantenibilidad",
        "subcharacteristic": "Capacidad de modificación",
        "indicator": "Errores críticos de Flake8",
        "formula": "cantidad de hallazgos E9, F63, F7 y F82",
        "unit": "hallazgos",
        "target": "0",
        "source": "Salida de Flake8 en GitHub Actions",
        "frequency": "En cada pull request y push",
        "responsible": "Equipo de desarrollo",
    },
    {
        "id": "task_completion_rate",
        "characteristic": "Usabilidad",
        "subcharacteristic": "Eficacia",
        "indicator": "Tasa de finalización de tareas",
        "formula": "tareas de usabilidad completadas / tareas intentadas × 100",
        "unit": "%",
        "target": ">= 80%",
        "source": "CSV de prueba de usabilidad observada",
        "frequency": "Por cada ronda de pruebas de usabilidad",
        "responsible": "Evaluador de usabilidad",
    },
]

USABILITY_COLUMNS = (
    "id_participante", "id_tarea", "completada", "duracion_segundos", "claridad_1_a_5",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _metric(model_id: str, value: float | int | None, source: str, measured_at: str,
            notes: str = "") -> dict[str, Any]:
    definition = next(item for item in QUALITY_MODEL if item["id"] == model_id)
    status = "No medido"
    if value is not None:
        percentage_metrics = {
            "validation_compliance_rate", "traceable_source_rate",
            "service_test_coverage", "task_completion_rate",
        }
        if model_id in percentage_metrics:
            threshold = _percentage_target(model_id)
            status = "Cumple la meta" if value >= threshold else "No cumple la meta"
        elif model_id == "critical_flake8_errors":
            status = "Cumple la meta" if value == 0 else "No cumple la meta"
        else:
            status = "Medido — línea base pendiente"
    return {
        "id": model_id,
        "indicator": definition["indicator"],
        "characteristic": definition["characteristic"],
        "subcharacteristic": definition["subcharacteristic"],
        "value": value,
        "unit": definition["unit"],
        "target": definition["target"],
        "status": status,
        "source": source,
        "measured_at_utc": measured_at,
        "notes": notes,
    }


def _percentage_target(model_id: str) -> int:
    if model_id == "validation_compliance_rate":
        return 95
    if model_id in {"service_test_coverage", "task_completion_rate"}:
        return 80
    return 100


def metrics_from_evidence(records: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Calcula sólo tasas que pueden obtenerse de las evidencias de la sesión."""
    records = list(records)
    timestamp = utc_now()
    evaluated = [item for item in records if item.get("estado") in {"Verificado", "No válido"}]
    verified = [item for item in evaluated if item.get("estado") == "Verificado"]
    validation_rate = (100 * len(verified) / len(evaluated)) if evaluated else None
    traceable = [item for item in verified if item.get("sha256") and item.get("leido_utc")]
    traceability_rate = (100 * len(traceable) / len(verified)) if verified else None
    validation_note = (
        f"{len(verified)} contratos verificados de {len(evaluated)} contratos evaluados."
        if evaluated else "No se evaluó ningún contrato de validación en esta sesión."
    )
    traceability_note = (
        f"{len(traceable)} fuentes verificadas trazables de {len(verified)} fuentes verificadas."
        if verified else "No hay fuentes verificadas disponibles en esta sesión."
    )
    return [
        _metric(
            "validation_compliance_rate", validation_rate,
            "Evidencia de validación de datos de la sesión", timestamp, validation_note,
        ),
        _metric(
            "traceable_source_rate", traceability_rate,
            "Evidencia de fuentes de la sesión", timestamp, traceability_note,
        ),
    ]


def runtime_metrics(measurements_ms: Mapping[str, float] | None) -> list[dict[str, Any]]:
    measurements_ms = measurements_ms or {}
    timestamp = utc_now()
    return [
        _metric("data_load_validation_ms", _rounded(measurements_ms.get("data_load_validation_ms")),
                "Cronómetro de la sesión de la aplicación", timestamp),
        _metric("filter_indicator_ms", _rounded(measurements_ms.get("filter_indicator_ms")),
                "Cronómetro de la sesión de la aplicación", timestamp),
    ]


def _rounded(value: float | int | None) -> float | None:
    return round(float(value), 2) if value is not None else None


def load_ci_metrics(root: Path) -> list[dict[str, Any]]:
    """Loads local CI evidence when a deployment intentionally includes it.

    GitHub Actions también carga este JSON como artefacto del flujo. Si falta la
    evidencia, se marca como no medida en vez de reutilizar un resultado antiguo.
    """
    path = Path(root) / "quality-results" / "ci_quality_metrics.json"
    timestamp = utc_now()
    if not path.is_file():
        return [
            _metric("service_test_coverage", None, "Artefacto de CI de GitHub Actions", timestamp,
                    "Esta versión desplegada no incluye un archivo de evidencia de CI."),
            _metric("critical_flake8_errors", None, "Artefacto de CI de GitHub Actions", timestamp,
                    "Esta versión desplegada no incluye un archivo de evidencia de CI."),
        ]
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        raw = payload["metrics"]
        by_id = {item["id"]: item for item in raw}
        coverage = float(by_id["service_test_coverage"]["value"])
        flake8_errors = int(by_id["critical_flake8_errors"]["value"])
        measured_at = str(payload.get("generated_at_utc", timestamp))
        commit = payload.get("commit", "unknown commit")
        return [
            _metric("service_test_coverage", coverage, "Evidencia de CI de GitHub Actions", measured_at,
                    f"Commit de CI: {commit}."),
            _metric("critical_flake8_errors", flake8_errors, "Evidencia de CI de GitHub Actions", measured_at,
                    f"Commit de CI: {commit}."),
        ]
    except (OSError, ValueError, KeyError, TypeError):
        return [
            _metric("service_test_coverage", None, "Evidencia de CI de GitHub Actions", timestamp,
                    "El archivo local de evidencia de CI no es válido y no se utilizó."),
            _metric("critical_flake8_errors", None, "Evidencia de CI de GitHub Actions", timestamp,
                    "El archivo local de evidencia de CI no es válido y no se utilizó."),
        ]


def usability_template_csv() -> bytes:
    """Returns a blank, documented template without fictitious participants."""
    template = pd.DataFrame(columns=USABILITY_COLUMNS)
    return template.to_csv(index=False).encode("utf-8")


def usability_metrics(uploaded_bytes: bytes | None) -> list[dict[str, Any]]:
    timestamp = utc_now()
    missing = [
        _metric("task_completion_rate", None, "CSV de prueba de usabilidad observada", timestamp,
                "Carga un CSV de participantes observados para calcular este indicador."),
    ]
    if not uploaded_bytes:
        return missing
    try:
        frame = pd.read_csv(BytesIO(uploaded_bytes))
        absent = set(USABILITY_COLUMNS) - set(frame.columns)
        if absent or frame.empty:
            raise ValueError("Faltan columnas de usabilidad obligatorias o no hay observaciones.")
        completed = frame["completada"].astype("string").str.strip().str.lower()
        valid = completed.isin({"true", "false", "1", "0", "yes", "no", "si", "sí"})
        if not valid.all():
            raise ValueError("La columna completada debe usar true/false, yes/no, si/no o 1/0.")
        successful = completed.isin({"true", "1", "yes", "si", "sí"})
        value = 100 * int(successful.sum()) / len(frame)
        note = f"{int(successful.sum())} tareas completadas de {len(frame)} tareas intentadas."
        return [
            _metric(
                "task_completion_rate", round(value, 2),
                "CSV de prueba de usabilidad observada", timestamp, note,
            )
        ]
    except (OSError, UnicodeError, pd.errors.ParserError, ValueError):
        return [_metric("task_completion_rate", None, "CSV de prueba de usabilidad observada", timestamp,
                        "El CSV de usabilidad cargado no es válido; no se calculó ninguna métrica.")]


def quality_report(data_service: Any, model_service: Any, measurements_ms: Mapping[str, float] | None = None,
                   usability_csv: bytes | None = None) -> dict[str, Any]:
    records = [dict(record) for service in (data_service, model_service) for record in service.reader.evidence.values()]
    metrics = (
        metrics_from_evidence(records)
        + runtime_metrics(measurements_ms)
        + load_ci_metrics(data_service.root_dir)
        + usability_metrics(usability_csv)
    )
    return {
        "format_version": 1,
        "generated_at_utc": utc_now(),
        "scope": "Evidencia de medición de calidad ISO/IEC 25000; no constituye una certificación.",
        "quality_model": QUALITY_MODEL,
        "metrics": metrics,
    }


def quality_report_json(report: Mapping[str, Any]) -> bytes:
    return json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False).encode("utf-8")
