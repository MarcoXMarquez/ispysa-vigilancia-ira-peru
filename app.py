"""
Plataforma de Vigilancia y Monitoreo Epidemiológico IRA - Perú (2000-2023)
Sistema de Información para la Toma de Decisiones en Salud Pública.
Prototipo académico con controles de calidad de datos y evidencias de validación.
"""

import sys
from pathlib import Path
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# Configuración del entorno de ejecución
CURRENT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(CURRENT_DIR))

from src.services.data_service import EpidemiologyDataService
from src.services.model_service import EpidemiologyModelService
from src.app_indicators import previous_year_deltas, top3_for_period
from src.quality_panel import evidence_report, export_with_evidence, render_quality_panel

# ==============================================================================
# CONFIGURACIÓN DE PÁGINA (ISO 9241-12: Densidad Visual y Ergonomía Espacial)
# ==============================================================================
st.set_page_config(
    page_title="Sistema de Vigilancia Epidemiológica IRA Perú | Calidad ISO 9241",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ==============================================================================
# HOJA DE ESTILOS INSTITUCIONAL (DESIGN TOKENS & CALIDAD ISO 9241)
# Paleta Clínica Normalizada, Tipografía Formal y Cero Emojis
# ==============================================================================
st.markdown(
    """
    <style>
    /* ==========================================================================
       DESIGN TOKENS - PALETA INSTITUCIONAL Y ERGONOMÍA VISUAL
       ========================================================================== */
    :root {
        --space-1: 4px;
        --space-2: 8px;
        --space-3: 12px;
        --space-4: 16px;
        --space-6: 24px;
        --space-8: 32px;

        --radius-sm: 4px;
        --radius-md: 8px;
        --radius-lg: 12px;

        --bg-surface: #ffffff;
        --bg-canvas: #f8fafc;
        --text-headline: #0f172a;
        --text-body: #334155;
        --text-subtle: #64748b;
        --border-subtle: #e2e8f0;
        --border-medium: #cbd5e1;

        --navy-primary: #0f172a;
        --blue-primary: #1e3a8a;
        --blue-accent: #0284c7;

        --alert-danger-bg: #fef2f2;
        --alert-danger-text: #991b1b;
        --alert-danger-border: #fecaca;

        --alert-warning-bg: #fffbeb;
        --alert-warning-text: #92400e;
        --alert-warning-border: #fde68a;

        --alert-normal-bg: #f0fdf4;
        --alert-normal-text: #166534;
        --alert-normal-border: #bbf7d0;

        --shadow-subtle: 0 1px 2px rgba(15, 23, 42, 0.04);
        --shadow-card: 0 2px 6px rgba(15, 23, 42, 0.04), 0 1px 2px rgba(15, 23, 42, 0.03);
    }

    /* Navegación y Scroll Suave (Lenis) */
    html {
        scroll-behavior: smooth;
    }
    @media (prefers-reduced-motion: reduce) {
        html { scroll-behavior: auto !important; }
        *, *::before, *::after {
            animation-duration: 0.001ms !important;
            animation-iteration-count: 1 !important;
            transition-duration: 0.001ms !important;
        }
    }

    /* Banner Institucional Superior */
    .institutional-hero {
        background-color: var(--navy-primary);
        border: 1px solid #1e293b;
        border-radius: var(--radius-md);
        padding: 24px 28px;
        margin-bottom: 16px;
        box-shadow: var(--shadow-card);
        color: #ffffff;
    }
    .institutional-badge {
        display: inline-block;
        font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: #93c5fd;
        background-color: rgba(30, 58, 138, 0.45);
        border: 1px solid rgba(147, 197, 253, 0.3);
        padding: 3px 10px;
        border-radius: var(--radius-sm);
        margin-bottom: 10px;
    }
    .institutional-title {
        font-size: 1.85rem;
        font-weight: 700;
        color: #f8fafc;
        margin: 0 0 6px 0;
        line-height: 1.25;
        letter-spacing: -0.01em;
    }
    .institutional-subtitle {
        font-size: 0.95rem;
        color: #94a3b8;
        margin: 0;
        font-weight: 400;
    }

    /* Panel Informativo de Situación Epidemiológica (Diseño Institucional SGC) */
    .executive-summary-panel {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 12px;
        background-color: #f8fafc;
        border: 1px solid #cbd5e1;
        border-left: 4px solid var(--blue-primary);
        border-radius: var(--radius-sm);
        padding: 10px 14px;
        margin-bottom: 18px;
    }
    .summary-item {
        font-size: 0.82rem;
        line-height: 1.4;
        color: #334155;
    }
    .summary-item-title {
        font-weight: 700;
        color: #0f172a;
        font-size: 0.78rem;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        margin-bottom: 2px;
    }

    /* Tarjetas de Indicadores Clave (KPIs) - shadcn / Design Tokens */
    .kpi-card {
        background-color: var(--bg-surface);
        border: 1px solid var(--border-subtle);
        border-radius: var(--radius-md);
        padding: 16px 20px;
        box-shadow: var(--shadow-card);
        transition: border-color 0.2s ease, box-shadow 0.2s ease;
    }
    .kpi-card:hover {
        border-color: var(--border-medium);
        box-shadow: 0 4px 10px rgba(15, 23, 42, 0.06);
    }
    .kpi-label {
        font-size: 0.78rem;
        font-weight: 600;
        color: var(--text-subtle);
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 4px;
    }
    .kpi-value {
        font-size: 1.95rem;
        font-weight: 700;
        color: var(--text-headline);
        margin: 2px 0 6px 0;
        line-height: 1.1;
        font-variant-numeric: tabular-nums;
    }
    .kpi-subtext {
        font-size: 0.8rem;
        color: var(--text-subtle);
    }

    /* Alerta Epidemiológica Sobria (ISO 9241-12) */
    .clinical-alert {
        border-radius: var(--radius-md);
        padding: 14px 18px;
        font-size: 0.92rem;
        line-height: 1.45;
        margin-bottom: 18px;
    }
    .clinical-alert-danger {
        background-color: var(--alert-danger-bg);
        border-left: 4px solid var(--alert-danger-text);
        border-top: 1px solid var(--alert-danger-border);
        border-right: 1px solid var(--alert-danger-border);
        border-bottom: 1px solid var(--alert-danger-border);
        color: var(--alert-danger-text);
    }
    .clinical-alert-warning {
        background-color: var(--alert-warning-bg);
        border-left: 4px solid var(--alert-warning-text);
        border-top: 1px solid var(--alert-warning-border);
        border-right: 1px solid var(--alert-warning-border);
        border-bottom: 1px solid var(--alert-warning-border);
        color: var(--alert-warning-text);
    }
    .clinical-alert-normal {
        background-color: var(--alert-normal-bg);
        border-left: 4px solid var(--alert-normal-text);
        border-top: 1px solid var(--alert-normal-border);
        border-right: 1px solid var(--alert-normal-border);
        border-bottom: 1px solid var(--alert-normal-border);
        color: var(--alert-normal-text);
    }

    /* Bento Grid Analítico */
    .analytical-box {
        background-color: var(--bg-surface);
        border: 1px solid var(--border-subtle);
        border-radius: var(--radius-md);
        padding: 18px 20px;
        box-shadow: var(--shadow-card);
        margin-bottom: 14px;
    }
    .analytical-box-title {
        font-size: 0.95rem;
        font-weight: 700;
        color: var(--text-headline);
        margin-bottom: 8px;
        text-transform: uppercase;
        letter-spacing: 0.03em;
    }

    /* Pestañas Ejecutivas */
    .stTabs [data-baseweb="tab-list"] {
        gap: 4px;
        border-bottom: 1px solid var(--border-subtle);
        padding-bottom: 2px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: var(--radius-sm);
        padding: 8px 16px;
        font-weight: 600;
        font-size: 0.88rem;
        color: var(--text-subtle);
    }
    .stTabs [aria-selected="true"] {
        background-color: #f1f5f9 !important;
        color: var(--navy-primary) !important;
        border-bottom: 2px solid var(--blue-primary) !important;
    }

    /* Panel de Notas Metodológicas (Vaul) */
    .methodology-panel {
        background-color: var(--bg-surface);
        border: 1px solid var(--border-subtle);
        border-radius: var(--radius-md);
        padding: 16px 20px;
        margin-top: 24px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def get_services():
    """Instancia servicios por ejecución para aislar evidencias y volver a validar archivos."""
    return EpidemiologyDataService(CURRENT_DIR), EpidemiologyModelService(CURRENT_DIR)


data_service, model_service = get_services()
annual_data = data_service.get_annual_measures()
if annual_data.empty:
    st.error("No es posible calcular indicadores: el archivo anual falta o no supera la validación.")
    st.info("Revisa los resultados de validación y restaura o corrige el archivo indicado. Después recarga la página.")
    render_quality_panel(data_service, model_service)
    st.stop()


# ==============================================================================
# BARRA LATERAL: PARÁMETROS DE VIGILANCIA (ISO 9241-110: Diálogo Ergonómico)
# ==============================================================================
with st.sidebar:
    st.markdown("### Parámetros de Vigilancia")
    st.caption("Configuración del contexto de análisis epidemiológico (ISO 9241-210)")

    # Filtro 1: Grupo Poblacional
    group_option = st.radio(
        "Grupo Poblacional Objetivo:",
        options=[
            "Población Pediátrica: Menores de 5 años (men5)",
            "Población Geriátrica: Adultos de 60 años a más (60mas)",
        ],
        index=0,
        help="Segmentación demográfica de riesgo conforme a directivas epidemiológicas nacionales.",
    )
    group_key = "men5" if "men5" in group_option else "60mas"
    group_label = "Menores de 5 años (men5)" if group_key == "men5" else "Adultos 60 años a más (60mas)"

    # Filtro 2: Ámbito Territorial
    departments = ["Nacional (Consolidado)"] + data_service.get_departments()
    selected_scope = st.selectbox(
        "Ámbito Territorial:",
        options=departments,
        index=0,
        help="Selección de consolidado nacional o desagregación por departamento.",
    )

    # Filtro 3: Período Temporal
    year_range = st.slider(
        "Período de Análisis (Años):",
        min_value=2000,
        max_value=2023,
        value=(2000, 2023),
        step=1,
        help="Ventana temporal para el cómputo de indicadores retrospectivos.",
    )

    st.markdown("---")
    st.markdown("#### Marco de Calidad del Software")
    st.caption("• ISO 9241-11: Medición de Usabilidad")
    st.caption("• ISO 9241-210: Diseño Centrado en el Humano")
    st.caption("• ISO 9241-110: Principios de Diálogo")
    st.caption("• ISO 9241-12: Representación Visual de Información")
    st.caption("• ISO/IEC 25010: Calidad del Producto Software")

    st.markdown("---")
    st.caption("Curso: Calidad de Software")
    st.caption("Modalidad: Equipo de 05 Integrantes")
    st.caption("Datos históricos disponibles: 2000–2023")

# ==============================================================================
# CARGA Y FILTRADO DE DATOS EPIDEMIOLÓGICOS
# ==============================================================================
is_national = selected_scope == "Nacional (Consolidado)"

if is_national:
    df_raw = data_service.get_national_summary()
    scope_title = "Nivel Nacional (Consolidado República del Perú)"
else:
    df_raw = data_service.get_department_data(selected_scope)
    scope_title = f"Departamento de {selected_scope}"

# Filtrado por rango de años
df_filtered = df_raw[(df_raw["year"] >= year_range[0]) & (df_raw["year"] <= year_range[1])].copy()
if df_filtered.empty:
    st.info("No hay datos para este ámbito y período. Selecciona otro intervalo de años.")
    st.stop()

# Cálculo de KPIs para el año más reciente de la selección
latest_year = int(df_filtered["year"].max())
kpis = data_service.compute_kpis(df_raw, group=group_key, year=latest_year)
cases_delta, rate_delta = previous_year_deltas(df_raw, group_key, latest_year)
hr_display = f"{kpis['hr']:.2f}%" if pd.notna(kpis["hr"]) else "No calculable"
cfr_display = f"{kpis['cfr']:.2f}%" if pd.notna(kpis["cfr"]) else "No calculable"
selection_context = {
    "ambito": selected_scope, "grupo": group_key, "periodo": list(year_range),
    "ano_indicadores": latest_year, "ambito_pronosticos": "Nacional",
    "formula_tasa": "Casos del grupo / población total × 100000",
}

# ==============================================================================
# 1. ENCABEZADO INSTITUCIONAL
# ==============================================================================
st.markdown(
    f"""
    <div class="institutional-hero">
        <div class="institutional-badge">ANÁLISIS HISTÓRICO DE SALUD PÚBLICA • PROTOTIPO ACADÉMICO</div>
        <div class="institutional-title">
            Plataforma de Monitoreo y Vigilancia Epidemiológica de Infecciones Respiratorias Agudas
        </div>
        <div class="institutional-subtitle">
            Ámbito: <strong>{scope_title}</strong> |
            Población: <strong>{group_label}</strong> |
            Período Evaluado: <strong>{year_range[0]} - {year_range[1]}</strong>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ==============================================================================
# 2. PANEL DE SÍNTESIS EPIDEMIOLÓGICA (GOBERNANZA CLÍNICA Y CONTROL SGC)
# ==============================================================================
st.markdown(
    f"""
    <div class="executive-summary-panel">
        <div class="summary-item">
            <div class="summary-item-title">Consulta seleccionada</div>
            <strong>{scope_title}</strong><br>{group_label}
        </div>
        <div class="summary-item">
            <div class="summary-item-title">Período histórico</div>
            Series de <strong>{year_range[0]} a {year_range[1]}</strong>.
            Las tarjetas muestran el último año disponible: <strong>{latest_year}</strong>.
        </div>
        <div class="summary-item">
            <div class="summary-item-title">Modelos nacionales</div>
            Evaluación a <strong>4 semanas</strong> y proyección a <strong>52 semanas</strong>.
            Resultados precalculados, independientes del filtro territorial y temporal.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ==============================================================================
# 3. EVALUACIÓN Y SEMÁFORO DE ALERTA SANITARIA (ISO 9241-12)
# ==============================================================================
inc_rate = kpis["cases_rate"]
if inc_rate > 350:
    alert_class, alert_code = "clinical-alert-danger", "TASA ANUAL MAYOR A 350"
elif inc_rate > 150:
    alert_class, alert_code = "clinical-alert-warning", "TASA ANUAL MAYOR A 150 Y HASTA 350"
else:
    alert_class, alert_code = "clinical-alert-normal", "TASA ANUAL HASTA 150"
alert_msg = (
    f"Valor observado en {latest_year}: {inc_rate:.1f} por 100,000 habitantes. "
    "Clasificación ilustrativa con cortes de 150 y 350; su validación epidemiológica está pendiente. "
    "Describe datos históricos y no determina el estado sanitario actual."
)

st.markdown(
    f"""
    <div class="clinical-alert {alert_class}">
        <strong>{alert_code}</strong> — {alert_msg}
    </div>
    """,
    unsafe_allow_html=True,
)

# ==============================================================================
# 4. TARJETAS DE INDICADORES CLAVE (KPIS)
# ==============================================================================
col_kpi1, col_kpi2, col_kpi3, col_kpi4 = st.columns(4)

with col_kpi1:
    delta_color = "#64748b" if cases_delta is None else "#991b1b" if cases_delta > 0 else "#166534"
    delta_text = (
        f"{cases_delta:+.1f}% vs. {latest_year - 1}" if cases_delta is not None
        else f"Sin comparación porcentual con {latest_year - 1}"
    )
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">Casos Diagnosticados ({int(kpis['year'])})</div>
            <div class="kpi-value">{int(kpis['cases']):,}</div>
            <div style="font-size: 0.82rem; font-weight: 600; color: {delta_color};">
                {delta_text}
            </div>
            <div class="kpi-subtext">Total anual registrado</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col_kpi2:
    delta_rate_color = "#64748b" if rate_delta is None else "#991b1b" if rate_delta > 0 else "#166534"
    delta_rate_text = (
        f"{rate_delta:+.1f} puntos vs. {latest_year - 1}" if rate_delta is not None
        else f"Sin comparación de tasa con {latest_year - 1}"
    )
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">Tasa Incidencia x 100k hab.</div>
            <div class="kpi-value" style="color: var(--blue-primary);">{kpis['cases_rate']:.1f}</div>
            <div style="font-size: 0.82rem; font-weight: 600; color: {delta_rate_color};">
                {delta_rate_text}
            </div>
            <div class="kpi-subtext">(Casos / Población) × 100,000</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col_kpi3:
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">Tasa de Hospitalización (HR)</div>
            <div class="kpi-value" style="color: #92400e;">{hr_display}</div>
            <div style="font-size: 0.82rem; font-weight: 600; color: var(--text-body);">
                {int(kpis['hospitalizations']):,} internamientos
            </div>
            <div class="kpi-subtext">(Hospitalizados / Casos) × 100</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col_kpi4:
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">Tasa de Letalidad (CFR)</div>
            <div class="kpi-value" style="color: #991b1b;">{cfr_display}</div>
            <div style="font-size: 0.82rem; font-weight: 600; color: var(--text-body);">
                {int(kpis['deaths']):,} defunciones
            </div>
            <div class="kpi-subtext">(Defunciones / Casos) × 100</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)
st.caption(
    "Las variaciones usan el año anterior del mismo ámbito y grupo, aunque esté fuera del intervalo visible. "
    "Sin datos previos no se calcula la variación; con cero casos previos no se calcula el porcentaje. "
    "HR y CFR no son calculables cuando no hay casos."
)

# ==============================================================================
# 5. PESTAÑAS PRINCIPALES (ORGANIZACIÓN EJECUTIVA CON NUMERACIÓN ROMANA)
# ==============================================================================
tab_trend, tab_severity, tab_regional, tab_prediction, tab_quality = st.tabs([
    "I. Vigilancia Temporal y Tendencias",
    "II. Severidad Clínica y Letalidad (HR / CFR)",
    "III. Estratificación Departamental y Carga Regional",
    "IV. Modelos Predictivos y Proyecciones (ML / DL)",
    "V. Calidad de Datos y Evidencias",
])

# ------------------------------------------------------------------------------
# PESTAÑA I: VIGILANCIA TEMPORAL Y TENDENCIAS
# ------------------------------------------------------------------------------
with tab_trend:
    st.markdown(f"#### Tendencia Histórica Anual — {scope_title}")

    col_opt_left, col_opt_right = st.columns([3, 1])
    with col_opt_right:
        metric_choice = st.selectbox(
            "Seleccionar Indicador:",
            options=["Tasa de Incidencia x 100k hab.", "Casos Totales", "Hospitalizaciones", "Defunciones"],
            index=0,
        )

    metric_map = {
        "Tasa de Incidencia x 100k hab.": f"cases_rate_{group_key}",
        "Casos Totales": f"cases_{group_key}",
        "Hospitalizaciones": f"hosp_{group_key}",
        "Defunciones": f"death_{group_key}",
    }
    selected_col = metric_map[metric_choice]

    fig_trend = px.line(
        df_filtered,
        x="year",
        y=selected_col,
        markers=True,
        title=f"Serie Temporal Retrospectiva: {metric_choice} ({year_range[0]} - {year_range[1]})",
        labels={"year": "Año Epidemiológico", selected_col: metric_choice},
        color_discrete_sequence=["#1e40af" if group_key == "men5" else "#0f766e"],
    )
    fig_trend.update_layout(
        hovermode="x unified",
        template="plotly_white",
        xaxis=dict(tickmode="linear", tick0=2000, dtick=2),
        margin=dict(l=20, r=20, t=40, b=20),
    )
    st.plotly_chart(fig_trend, use_container_width=True)

    with st.expander("Tabla de Datos Retrospectivos y Exportación"):
        display_cols = [
            "year",
            f"cases_{group_key}",
            f"cases_rate_{group_key}",
            f"hosp_{group_key}",
            f"death_{group_key}",
            f"hr_{group_key}",
            f"cfr_{group_key}",
        ]
        df_display = df_filtered[display_cols].rename(
            columns={
                "year": "Año",
                f"cases_{group_key}": "Casos",
                f"cases_rate_{group_key}": "Tasa x 100k",
                f"hosp_{group_key}": "Hospitalizados",
                f"death_{group_key}": "Defunciones",
                f"hr_{group_key}": "HR (%)",
                f"cfr_{group_key}": "CFR (%)",
            }
        )
        st.dataframe(df_display, use_container_width=True, hide_index=True)
        csv_data = df_display.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="Descargar Serie Consolidada (.CSV)",
            data=csv_data,
            file_name=f"reporte_epidemiologico_{group_key}_{scope_title.lower().replace(' ', '_')}.csv",
            mime="text/csv",
        )

    st.download_button(
        "Descargar consulta con fuentes (.ZIP)",
        export_with_evidence(df_display, evidence_report(data_service, model_service, selection_context)),
        file_name=f"consulta_{group_key}_{year_range[0]}_{year_range[1]}.zip", mime="application/zip",
    )

# ------------------------------------------------------------------------------
# PESTAÑA II: SEVERIDAD CLÍNICA Y LETALIDAD
# ------------------------------------------------------------------------------
with tab_severity:
    st.markdown("#### Dinámica de Severidad Clínica: Demanda Hospitalaria y Tasa de Letalidad")
    st.markdown(
        """
        * **Tasa de Hospitalización (HR):** Proporción de casos atendidos que requirieron internamiento formal 
          ($HR = \text{Hospitalizaciones} / \text{Casos} \times 100$). Representa el índice de presión hospitalaria.
        * **Tasa de Letalidad (CFR):** Proporción de casos que concluyeron en defunción confirmada 
          ($CFR = \text{Defunciones} / \text{Casos} \times 100$). Representa la gravedad biológica y letalidad intrínseca.
        """
    )

    col_sev_a, col_sev_b = st.columns(2)

    with col_sev_a:
        fig_sev = go.Figure()
        fig_sev.add_trace(
            go.Scatter(
                x=df_filtered["year"],
                y=df_filtered[f"hr_{group_key}"],
                name="Tasa de Hospitalización (HR %)",
                line=dict(color="#d97706", width=2.5),
                mode="lines+markers",
            )
        )
        fig_sev.add_trace(
            go.Scatter(
                x=df_filtered["year"],
                y=df_filtered[f"cfr_{group_key}"],
                name="Tasa de Letalidad (CFR %)",
                line=dict(color="#b91c1c", width=2.5, dash="dot"),
                mode="lines+markers",
            )
        )
        fig_sev.update_layout(
            title="Evolución Comparativa: Hospitalización vs Letalidad",
            xaxis_title="Año",
            yaxis_title="Porcentaje (%)",
            template="plotly_white",
            hovermode="x unified",
        )
        st.plotly_chart(fig_sev, use_container_width=True)

    with col_sev_b:
        scatter_data = df_filtered.dropna(subset=[f"hr_{group_key}", f"cfr_{group_key}"])
        fig_scatter = px.scatter(
            scatter_data,
            x=f"hr_{group_key}",
            y=f"cfr_{group_key}",
            text="year",
            size=f"cases_{group_key}",
            title="Cuadrante de Correlación: Presión Hospitalaria (HR) vs Letalidad (CFR)",
            labels={
                f"hr_{group_key}": "Tasa de Hospitalización (HR %)",
                f"cfr_{group_key}": "Tasa de Letalidad (CFR %)",
            },
            color=f"cases_rate_{group_key}",
            color_continuous_scale="Blues",
        )
        fig_scatter.update_traces(textposition="top center")
        fig_scatter.update_layout(template="plotly_white")
        st.plotly_chart(fig_scatter, use_container_width=True)

# ------------------------------------------------------------------------------
# PESTAÑA III: ESTRATIFICACIÓN DEPARTAMENTAL Y CARGA REGIONAL
# ------------------------------------------------------------------------------
with tab_regional:
    st.markdown(f"#### Persistencia en el Top 3 por tasa de incidencia — {group_label}")
    st.caption(
        "Comparación entre todos los departamentos para el período seleccionado. "
        "El filtro territorial se aplica a las tendencias y tarjetas; aquí se conserva la comparación nacional."
    )
    rank_grid = data_service.get_rank_grid(group=group_key)
    top3_df, ranking_years = top3_for_period(rank_grid, year_range)
    if top3_df.empty:
        st.info(
            "No hay rankings disponibles para el período elegido. "
            "Los rankings de menores de 5 años comienzan en 2000 y los de adultos de 60 años a más, en 2006."
        )
    else:
        st.caption(
            f"Años incluidos: {', '.join(map(str, ranking_years))}. "
            "Los porcentajes usan los años con ranking disponible de cada departamento."
        )
        col_reg_left, col_reg_right = st.columns([7, 5])
        with col_reg_left:
            fig_top3 = px.bar(
                top3_df.head(10),
                x="region",
                y="top3_appearances",
                text="percent_years_in_top3",
                hover_data=["observed_years"],
                title=f"Frecuencia en los puestos 1 a 3 ({ranking_years[0]}–{ranking_years[-1]})",
                labels={
                    "region": "Departamento", "top3_appearances": "Años en el Top 3",
                    "percent_years_in_top3": "% de años en el Top 3", "observed_years": "Años con ranking",
                },
                color="top3_appearances",
                color_continuous_scale="Reds",
            )
            fig_top3.update_traces(texttemplate="%{text:.1f}%", textposition="outside", cliponaxis=False)
            fig_top3.update_layout(template="plotly_white", xaxis_tickangle=-45)
            st.plotly_chart(fig_top3, use_container_width=True)
        with col_reg_right:
            st.markdown("##### Departamentos con mayor frecuencia")
            st.dataframe(
                top3_df.head(3).rename(columns={
                    "region": "Departamento", "top3_appearances": "Años Top 3",
                    "observed_years": "Años con ranking", "percent_years_in_top3": "% Top 3",
                }),
                use_container_width=True, hide_index=True,
            )
            st.markdown(
                "**Cómo leerlo:** Top 3 significa puestos 1, 2 o 3 por tasa anual de incidencia. "
                "Se conservan los empates del ranking original, por lo que puede haber más de tres "
                "departamentos en esos puestos durante un año."
            )
            st.caption(
                "La Categoría 1 del análisis original comprende los puestos 1 a 5; "
                "es una agrupación distinta del Top 3 mostrado aquí."
            )
        st.download_button(
            "Descargar ranking del período (.CSV)",
            data=top3_df.to_csv(index=False).encode("utf-8-sig"),
            file_name=f"ranking_top3_{group_key}_{year_range[0]}_{year_range[1]}.csv",
            mime="text/csv",
        )

# ------------------------------------------------------------------------------
# PESTAÑA IV: MODELOS PREDICTIVOS Y PROYECCIONES
# ------------------------------------------------------------------------------
with tab_prediction:
    st.markdown(f"#### Modelos nacionales — {group_label}")
    st.info(
        "Esta pestaña muestra resultados nacionales precalculados para el grupo poblacional elegido. "
        "La selección de departamento y de años no modifica estos modelos ni vuelve a entrenarlos."
    )

    metrics_df = model_service.get_national_metrics(group=group_key)
    if metrics_df.empty:
        st.info("Métricas no disponibles o archivo no válido. Revisa el detalle en Calidad de Datos y Evidencias.")
    else:
        col_ml_1, col_ml_2 = st.columns([2, 1])

        with col_ml_1:
            st.markdown("##### Evaluación histórica: horizonte de 4 semanas")
            st.caption(
                "Backtesting con ventanas de entrenamiento de 5 años y avance de 4 semanas. "
                "Estas métricas no corresponden a la proyección de 52 semanas."
            )
            st.dataframe(
                metrics_df[["model_display", "mae", "rmse", "r2"]].rename(
                    columns={"model_display": "Modelo Evaluado", "mae": "MAE", "rmse": "RMSE", "r2": "Coeficiente R²"}
                ),
                use_container_width=True,
                hide_index=True,
            )

        with col_ml_2:
            best_model = metrics_df.sort_values("r2", ascending=False).iloc[0]
            st.markdown(
                f"""
                <div class="analytical-box" style="border-left: 4px solid #15803d;">
                    <div class="analytical-box-title" style="color: #15803d;">Modelo con Desempeño Óptimo</div>
                    <div style="font-size: 1.35rem; font-weight: 700; color: var(--text-headline); margin: 4px 0;">{best_model['model_display']}</div>
                    <div style="font-size: 0.9rem; color: var(--text-body); line-height: 1.5;">
                        • Coeficiente R²: <strong>{best_model['r2']:.3f}</strong><br>
                        • Error Absoluto Medio (MAE): <strong>{best_model['mae']:.3f}</strong><br>
                        • Raíz de Error Cuadrático (RMSE): <strong>{best_model['rmse']:.3f}</strong>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("##### Proyección nacional a 52 semanas con bandas aproximadas")
    future_df = model_service.get_national_future_predictions(group=group_key)

    if not future_df.empty:
        st.caption(future_df.attrs.get("band_method", "Metodología de las bandas no documentada."))
        st.caption("La cobertura predictiva del 95 % a 52 semanas no ha sido verificada.")
        missing_bands = future_df.attrs.get("missing_band_models", [])
        if missing_bands:
            st.info("Sin RMSE válido para: " + ", ".join(missing_bands) + ". Se muestra solo el pronóstico puntual.")
        st.caption(
            f"Fechas del archivo de proyección: {future_df['date'].min():%d/%m/%Y} "
            f"a {future_df['date'].max():%d/%m/%Y}."
        )
        fig_pred = go.Figure()
        models_in_pred = future_df["model"].unique()
        colors = {"xgboost": "#1e3a8a", "random_forest": "#15803d", "lstm": "#4338ca"}

        for mod in models_in_pred:
            sub = future_df[future_df["model"] == mod].sort_values("date")
            color = colors.get(mod, "#0284c7")
            name = "XGBoost" if mod == "xgboost" else "Random Forest" if mod == "random_forest" else mod.upper()

            fig_pred.add_trace(
                go.Scatter(
                    x=sub["date"],
                    y=sub["predicted"],
                    mode="lines",
                    name=f"Pronóstico {name}",
                    line=dict(color=color, width=2.5),
                )
            )

            if sub[["lower_ci", "upper_ci"]].notna().all().all():
                fig_pred.add_trace(
                    go.Scatter(
                        x=pd.concat([sub["date"], sub["date"][::-1]]),
                        y=pd.concat([sub["upper_ci"], sub["lower_ci"][::-1]]),
                        fill="toself",
                        fillcolor="rgba(203, 213, 225, 0.25)",
                        line=dict(color="rgba(255,255,255,0)"),
                        hoverinfo="skip",
                        showlegend=True,
                        name=f"Banda aproximada ({name})",
                    )
                )

        fig_pred.update_layout(
            title=f"Proyección nacional de incidencia semanal — {group_label}",
            xaxis_title="Semana Epidemiológica Futura",
            yaxis_title="Tasa de Incidencia Predicha",
            template="plotly_white",
            hovermode="x unified",
        )
        st.plotly_chart(fig_pred, use_container_width=True)
    else:
        st.info("No hay un archivo de proyecciones disponible para este grupo poblacional.")

    st.markdown("##### Importancia de variables: archivo regional de referencia")
    importance_sources = model_service.get_feature_importance_sources(group_key)
    selected_importance = st.selectbox(
        "Resultado regional (departamento y modelo indicados en el nombre):",
        importance_sources,
    ) if importance_sources else None
    feat_df = model_service.get_feature_importance_summary(group_key, source=selected_importance)
    if feat_df.empty:
        st.info("Importancias no disponibles o archivo no válido. No se utilizan valores ilustrativos.")
    else:
        st.caption("Fuente: " + feat_df.attrs["source"])
        fig_feat = px.bar(
            feat_df.sort_values("importance", ascending=True), x="importance", y="feature",
            orientation="h", title=f"Importancia de variables — {selected_importance}",
            labels={"importance": "Importancia reportada", "feature": "Variable"},
            color="importance", color_continuous_scale="Blues",
        )
        fig_feat.update_layout(template="plotly_white")
        st.plotly_chart(fig_feat, use_container_width=True)

# ------------------------------------------------------------------------------
# PESTAÑA V: AUDITORÍA DE CALIDAD Y ESTÁNDARES ISO 9241
# ------------------------------------------------------------------------------
with tab_quality:
    render_quality_panel(data_service, model_service, selection_context)

# ==============================================================================
# 6. PANEL INFERIOR: ESPECIFICACIONES METODOLÓGICAS Y GLOSARIO OFICIAL
# ==============================================================================
st.markdown(
    """
    <div class="methodology-panel">
        <div style="font-size: 0.88rem; font-weight: 700; color: var(--navy-primary); margin-bottom: 8px; text-transform: uppercase; letter-spacing: 0.05em; border-bottom: 1px solid var(--border-subtle); padding-bottom: 6px;">
            Ficha técnica y alcance de los indicadores
        </div>
        <div style="font-size: 0.85rem; color: var(--text-body); line-height: 1.6;">
            • <strong>Tasa de casos por población total:</strong> <code>(Casos / Población) × 100,000 hab.</code> (Población total interpolada; no es una tasa específica por población del grupo etario).<br>
            • <strong>Tasa de Hospitalización (HR):</strong> <code>(Hospitalizaciones / Casos) × 100</code> (Índice de demanda y presión hospitalaria).<br>
            • <strong>Tasa de Letalidad (CFR):</strong> <code>(Defunciones / Casos) × 100</code> (Proporción de mortalidad en casos diagnosticados).<br>
            • <strong>Bandas Aproximadas de Incertidumbre:</strong> <code>Pronóstico ± 1.96 × RMSE</code> (Límite inferior en cero; cobertura a 52 semanas no verificada).
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
st.caption("Plataforma de análisis epidemiológico © 2026 — Evaluaciones de calidad documentadas en la pestaña V")
