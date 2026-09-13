"""Evidencias de la sesión y exportación con contexto reproducible."""

from datetime import datetime, timezone
from io import BytesIO
import json
from zipfile import ZIP_DEFLATED, ZipFile


def evidence_report(data_service, model_service, selection=None):
    artifacts = [dict(record) for service in (data_service, model_service)
                 for record in service.reader.evidence.values()]
    return {
        "version_formato": 1,
        "informe_generado_utc": datetime.now(timezone.utc).isoformat(),
        "seleccion": selection or {},
        "archivos": artifacts,
        "alcance": "Validación estructural y numérica de los archivos leídos en esta sesión; no certificación ISO.",
        "procedencia_externa": "El origen institucional debe contrastarse con la documentación del dataset original.",
        "fechas": "La fecha de lectura no es la fecha de generación del modelo ni de actualización del dataset.",
        "evaluaciones_pendientes": [
            "Validación de los umbrales epidemiológicos por especialistas.",
            "Pruebas de usabilidad con usuarios representativos (ISO 9241-11 y 9241-210).",
            "Medición de rendimiento en un entorno documentado.",
            "Evaluación de accesibilidad por teclado, zoom, contraste y tecnologías de apoyo.",
            "Verificación de cobertura predictiva de las bandas a 52 semanas.",
        ],
    }


def report_json(report):
    return json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False).encode("utf-8")


def export_with_evidence(frame, report):
    buffer = BytesIO()
    with ZipFile(buffer, "w", ZIP_DEFLATED) as archive:
        archive.writestr("datos.csv", frame.to_csv(index=False).encode("utf-8-sig"))
        archive.writestr("fuentes_y_validaciones.json", report_json(report))
    return buffer.getvalue()


def render_quality_panel(data_service, model_service, selection=None):
    import pandas as pd
    import streamlit as st

    report = evidence_report(data_service, model_service, selection)
    records = report["archivos"]
    st.markdown("#### Calidad de datos y evidencias de la sesión")
    st.caption(report["alcance"])
    if records:
        summary = pd.DataFrame(records)
        st.dataframe(
            summary[["archivo", "estado", "contrato", "detalle", "filas"]].rename(columns={
                "archivo": "Archivo", "estado": "Estado", "contrato": "Control ejecutado",
                "detalle": "Resultado", "filas": "Registros válidos",
            }), use_container_width=True, hide_index=True,
        )
        with st.expander("Fuentes, versiones de archivo y fechas"):
            st.caption("SHA-256 identifica los bytes utilizados y permite comparar versiones del mismo archivo.")
            st.dataframe(
                summary[["archivo", "sha256", "leido_utc", "generado_utc"]].rename(columns={
                    "archivo": "Archivo fuente", "sha256": "SHA-256",
                    "leido_utc": "Lectura UTC", "generado_utc": "Generación original (no documentada)",
                }), use_container_width=True, hide_index=True,
            )
            st.caption(report["fechas"])
            st.caption(report["procedencia_externa"])

    st.markdown("##### Relación con los objetivos de calidad")
    st.markdown(
        "**ISO 9000:2015:** documentar entradas, controles, resultados y pendientes apoya el enfoque "
        "a procesos, la toma de decisiones basada en evidencia y la mejora. "
        "**ISO/IEC 25010:** los controles y el manejo de resultados ausentes apoyan la corrección funcional "
        "y la fiabilidad. Estas asociaciones no equivalen a una evaluación completa de conformidad."
    )
    st.markdown("##### Evaluaciones pendientes")
    st.dataframe(pd.DataFrame({"Evaluación": report["evaluaciones_pendientes"], "Estado": "Pendiente"}),
                 use_container_width=True, hide_index=True)
    st.download_button("Descargar evidencias (.JSON)", report_json(report),
                       file_name="evidencias_calidad.json", mime="application/json")
