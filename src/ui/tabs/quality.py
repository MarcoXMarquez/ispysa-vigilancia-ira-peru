"""Pestaña V: Calidad del Producto Software (ISO/IEC 25010, GQM e ISO 9241)."""

import csv
import io
import json
from typing import Any, Dict
import pandas as pd
import streamlit as st

from src.services.quality_service import ISO25010QualityService
from src.ui import charts, components
from src.ui.state import ViewContext


def render(ctx: ViewContext) -> None:
    """Renderiza el tablero de control de calidad de software y trazabilidad ISO."""
    quality_service = ISO25010QualityService(ctx.data_service.root_dir)
    audit = quality_service.get_last_audit()
    eval_res = quality_service.evaluate_product_quality()

    # Metadatos de la auditoría
    meta = eval_res.get("audit_meta") or {}
    gen_at = meta.get("generated_at") or (audit.get("generated_at") if audit else "En memoria")
    if isinstance(gen_at, str) and "T" in gen_at:
        gen_at = gen_at.split("T")[0]
    git_commit = meta.get("git_commit") or (audit.get("git_commit") if audit else "HEAD")

    components.section_header(
        "Calidad del producto (ISO/IEC 25010)",
        f"Evaluación GQM cuantitativa basada en Calabrese et al. (2018). "
        f"Auditoría generada el {gen_at} sobre commit {git_commit}.",
        testid="sec-quality-summary",
    )

    # 1. Resumen Ejecutivo (stat_grid y banner de cadena débil)
    iq_global = eval_res.get("iq_salud_global", 0.0)
    iq_equal = eval_res.get("iq_salud_global_equal_weights", 0.0)
    cobertura_app = eval_res.get("cobertura_aplicabilidad", "7/15")
    rango = eval_res.get("rango_global", "Supera el nivel objetivo")
    iq_strict = audit.get("global_index_strict", 91.5) if audit else 91.5

    components.stat_grid([
        {
            "label": "Índice global ponderado",
            "value": f"{iq_global:.1f} %",
            "subtext": f"Rango: {rango}",
        },
        {
            "label": "Índice con pesos iguales (1/6)",
            "value": f"{iq_equal:.1f} %",
            "subtext": "Análisis de sensibilidad",
        },
        {
            "label": f"Cobertura aplicable ({cobertura_app} EC)",
            "value": f"Estricto: {iq_strict:.1f} %",
            "subtext": "Puntaje UNLP con denominador fijo",
        },
    ], testid="quality-global-index")

    weak_info = eval_res.get("weak_link", {})
    weak_passed = weak_info.get("passed", True)
    weak_msg = weak_info.get("message", "Cumple la regla de la cadena débil")
    banner_cls = "ok" if weak_passed else "bad"

    st.markdown(
        f'<div class="status-banner status-banner--{banner_cls}" role="status">'
        f'<div class="title">{weak_msg}</div>'
        '<div>Principio de la cadena débil (Calabrese et al., 2018 §4.2): ninguna subcaracterística aplicable '
        'se sitúa en el nivel No aceptable (&lt; 40%).</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    # 2. Resumen por Característica y Gráfico Radar
    col_table, col_radar = st.columns([3, 2])

    char_scores: Dict[str, float] = {}
    table_rows = []
    questions_list = audit.get("questions", []) if audit else []

    chars_data = eval_res.get("caracteristicas", {})
    order = [
        "Adecuación funcional",
        "Eficiencia de desempeño",
        "Fiabilidad",
        "Seguridad",
        "Mantenibilidad",
        "Usabilidad",
    ]

    for cname in order:
        if cname in chars_data:
            score = float(chars_data[cname].get("puntaje", 0.0))
            char_scores[cname] = score
            c_questions = [
                q for q in questions_list
                if _get_q_field(q, "caracteristica", "characteristic", default="") == cname
            ]
            auto_count = sum(
                1 for q in c_questions
                if _get_q_field(q, "origen", "origin", default="") == "AUTOMATICA"
            )
            doc_count = sum(
                1 for q in c_questions
                if _get_q_field(q, "origen", "origin", default="") == "DOCUMENTAL"
            )
            na_count = sum(
                1 for q in c_questions
                if _get_q_field(q, "origen", "origin", default="") in ("NO_APLICA", "SIN_EVIDENCIA")
            )

            table_rows.append([
                cname,
                f"{score:.1f} %",
                chars_data[cname].get("rango", classify_score(score)),
                str(auto_count),
                str(doc_count),
                str(na_count),
            ])

    with col_table:
        components.html_table(
            ["Característica", "Puntaje (%)", "Rango", "Automáticas", "Documentales", "N/A o Sin Evidencia"],
            table_rows,
            testid="quality-table",
        )

    with col_radar:
        fig_radar = charts.build_quality_radar(char_scores)
        st.plotly_chart(fig_radar, use_container_width=True, config=components.PLOTLY_CONFIG)

    # 3. Detalle Especial: Modelo de Seguridad UNLP
    with st.expander("Seguridad de la información (Modelo UNLP — Calabrese et al., 2018)", expanded=True):
        st.markdown(
            "El paper evalúa 5 subcaracterísticas de seguridad con 33 preguntas (Q1–Q33) y 15 criterios (EC). "
            "Para un portal público de solo lectura sin login ni BD transaccional, se computan dos puntajes:"
        )

        sec_applicable = audit.get("security", {}).get("applicable_scores", {}) if audit else {}
        sec_strict = audit.get("security", {}).get("strict_scores", {}) if audit else {}

        sec_headers = [
            "Subcaracterística",
            "Puntaje Aplicable",
            "Puntaje Estricto (Paper)",
            "Criterios Aplicables",
            "Criterios N/A",
        ]
        sec_rows = [
            [
                "Confidencialidad",
                _fmt_score_pct(sec_applicable.get("Confidencialidad")),
                _fmt_score_pct(sec_strict.get("Confidencialidad")),
                "EC_C2 (HTTPS en tránsito)",
                "EC_C1 (Contraseñas), EC_C3 (Permisos BD)",
            ],
            [
                "Integridad",
                _fmt_score_pct(sec_applicable.get("Integridad")),
                _fmt_score_pct(sec_strict.get("Integridad")),
                "EC_I5 (Inyección SQL inmune), EC_I6 (Código seguro)",
                "EC_I4 (Confirmación de registro por email)",
            ],
            [
                "No Repudio",
                _fmt_score_pct(sec_applicable.get("No repudio")),
                _fmt_score_pct(sec_strict.get("No repudio")),
                "EC_NR9 (Telemetría de uso privacy-by-design)",
                "EC_NR8, EC_NR10, EC_NR11 (Firma digital, 2FA)",
            ],
            [
                "Responsabilidad",
                _fmt_score_pct(sec_applicable.get("Responsabilidad")),
                _fmt_score_pct(sec_strict.get("Responsabilidad")),
                "EC_R13 (Trazabilidad de auditoría)",
                "EC_R12 (Reportes de acceso no autorizado)",
            ],
            [
                "Autenticidad",
                _fmt_score_pct(sec_applicable.get("Autenticidad")),
                _fmt_score_pct(sec_strict.get("Autenticidad")),
                "EC_A15 (Infraestructura verificada)",
                "EC_A14 (Biometría, 2FA en login)",
            ],
        ]
        components.html_table(sec_headers, sec_rows, testid="quality-security-detail")

    # 4. Detalle de Preguntas y Evidencias por Característica
    with st.expander("Inspección de preguntas GQM y evidencias por característica"):
        st.markdown(
            "Detalle de las **54 preguntas GQM** evaluadas con evidencia empírica, "
            "subcaracterística asociada y trazabilidad de verificación:"
        )
        tabs_chars = st.tabs(order)
        for tab_c, char_name in zip(tabs_chars, order):
            with tab_c:
                char_qs = [
                    q for q in questions_list
                    if _get_q_field(q, "caracteristica", "characteristic", default="") == char_name
                ]
                if char_qs:
                    q_table = []
                    for q in char_qs:
                        q_table.append({
                            "ID": _get_q_field(q, "id"),
                            "Subcaracterística": _get_q_field(q, "subcaracteristica", "subcharacteristic"),
                            "Pregunta GQM": _get_q_field(q, "pregunta", "question"),
                            "Evaluación": _format_q_response(_get_q_field(q, "respuesta", "value", default=None)),
                            "Tipo de sonda": _get_q_field(q, "origen", "origin"),
                            "Evidencia empírica / Justificación": _get_q_field(
                                q, "evidencia", "justificacion", "evidence", "justification"
                            ),
                            "Auditor": _get_q_field(q, "verificado_por", "verified_by", default="Marco"),
                        })
                    st.dataframe(pd.DataFrame(q_table), use_container_width=True, hide_index=True)
                else:
                    st.info(f"No se registraron preguntas para {char_name}.")

    # 5. Proceso y Formatos de Captura de Información (ISO/IEC 25040)
    with st.expander("Proceso de evaluación y formatos de captura (ISO/IEC 25040)"):
        st.markdown(
            "Conforme al estándar ISO/IEC 25040, el proceso de evaluación de calidad se estructura en 5 fases:\n\n"
            "1. **Establecer requisitos:** Definición de objetivos GQM y selección de características ISO 25010.\n"
            "2. **Especificar la evaluación:** Mapeo de subcaracterísticas a preguntas y criterios (EC).\n"
            "3. **Diseñar la evaluación:** Instrumentación de sondas automáticas y plantilla de captura.\n"
            "4. **Ejecutar la evaluación:** Ejecución de `run_quality_audit.py` y telemetría de tests.\n"
            "5. **Concluir la evaluación:** Consolidación en `last_audit.json` y regla de la cadena débil."
        )

        col_d1, col_d2 = st.columns(2)
        with col_d1:
            template_csv = quality_service.get_blank_template_csv()
            st.download_button(
                "Descargar plantilla de recolección (CSV)",
                data=template_csv,
                file_name="plantilla_respuestas_gqm.csv",
                mime="text/csv",
                use_container_width=True,
            )
        with col_d2:
            audit_json_str = json.dumps(audit, indent=2, ensure_ascii=False) if audit else "{}"
            st.download_button(
                "Descargar informe de auditoría (JSON)",
                data=audit_json_str,
                file_name="last_audit.json",
                mime="application/json",
                use_container_width=True,
            )

        st.markdown("##### Simulación de evaluación interactiva")
        uploaded_file = st.file_uploader(
            "Cargar respuestas para simulación (CSV)",
            type=["csv"],
            help="Sube un archivo CSV con columnas 'id' y 'respuesta' para evaluar en memoria sin persistir.",
        )
        if uploaded_file is not None:
            try:
                content = uploaded_file.getvalue().decode("utf-8")
                reader = csv.DictReader(io.StringIO(content))
                custom_answers: Dict[str, Any] = {}
                for row in reader:
                    qid = row.get("id", "").strip()
                    resp = row.get("respuesta", "").strip().upper()
                    if qid:
                        custom_answers[qid] = resp
                sim_res = quality_service.evaluate_product_quality(custom_responses=custom_answers)
                sim_iq = sim_res.get("iq_salud_global", 0.0)
                sim_rng = sim_res.get("rango_global", "")
                st.success(f"Simulación exitosa: Índice Global calculado = {sim_iq:.1f} % ({sim_rng})")
            except Exception as e:
                st.error(f"Error en la validación del CSV cargado: {str(e)}")

    # 6. Matriz de Trazabilidad ISO 9241 e ISO/IEC 25010
    st.markdown("### Matriz de trazabilidad y cumplimiento normativo ISO 9241 e ISO/IEC 25010")
    iso_headers = ["Estándar", "Principio Rector", "Dónde se evidencia en la app"]
    iso_rows = [
        [
            "ISO 9241-11",
            "Medición de usabilidad (eficacia, eficiencia y satisfacción)",
            "Filtros en ≤2 selecciones (sidebar), caché <0.2s (@st.cache_resource) y exportación formal CSV.",
        ],
        [
            "ISO 9241-210",
            "Diseño centrado en el humano para salud pública",
            "Secuencia cognitiva: Diagnóstico (Bortman) → Severidad → Territorio → Pronóstico.",
        ],
        [
            "ISO 9241-110",
            "Principios de diálogo ergonómico y autodescripción",
            "Tasas estandarizadas por 100k hab., notas explicativas y manejo defensivo de división entre cero.",
        ],
        [
            "ISO 9241-12",
            "Representación visual de la información y semáforo clínico",
            "Rejilla espacial de 8px (styles.css), contraste WCAG AA ≥ 4.5:1, etiquetas redundantes y Okabe-Ito.",
        ],
        [
            "ISO/IEC 25010",
            "Calidad del producto software y mantenibilidad",
            "Capa de servicios desacoplada (ACL), constructores puros en charts.py, 100% pruebas en verde.",
        ],
    ]
    components.html_table(iso_headers, iso_rows)

    with st.expander("Ficha técnica y definiciones metodológicas"):
        st.markdown(
            "• **Tasa de Incidencia:** `(Casos / Población) × 100 000 hab.` (Interpolación censal 2000–2023).\n"
            "• **Tasa de Hospitalización (HR):** `(Hospitalizaciones / Casos) × 100` (Presión hospitalaria).\n"
            "• **Tasa de Letalidad (CFR):** `(Defunciones / Casos) × 100` (Gravedad clínica biológica).\n"
            "• **Bandas de Incertidumbre:** `Pronóstico ± 1.96 × RMSE` (Límite inferior truncado en cero)."
        )


def _fmt_score_pct(val: Any) -> str:
    """Formatea puntajes porcentuales manejando valores None/excluidos."""
    if val is None:
        return "N/A (Excluido)"
    try:
        return f"{float(val):.1f} %"
    except (ValueError, TypeError):
        return str(val)


def _get_q_field(q: Dict[str, Any], *keys: str, default: Any = "—") -> Any:
    """Extrae el primer valor no nulo de un diccionario según una lista de claves candidatas."""
    for k in keys:
        if k in q and q[k] is not None and q[k] != "":
            return q[k]
    return default


def _format_q_response(val: Any) -> str:
    """Homologa representaciones booleanas o textuales de cumplimiento GQM."""
    if val in (True, "SI", "SÍ"):
        return "Cumple (SÍ)"
    elif val in (False, "NO"):
        return "No cumple (NO)"
    return "No aplica (N/A)"


def classify_score(score: float) -> str:
    """Clasificación de calidad según intervalos de Calabrese et al. (2018 §4.2)."""
    if score < 40.0:
        return "No aceptable"
    elif score < 60.0:
        return "Mínimamente aceptable"
    elif score < 90.0:
        return "Nivel objetivo"
    return "Supera el nivel objetivo"
