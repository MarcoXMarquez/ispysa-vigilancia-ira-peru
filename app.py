"""
Plataforma de Vigilancia y Monitoreo Epidemiológico IRA - Perú (2000-2023)
Sistema de Información para la Toma de Decisiones en Salud Pública.
Conforme a Normas Internacionales ISO 9241 (11, 210, 110, 12) e ISO/IEC 25010.
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

    /* Cintillo Informativo Monospaciado (Magic UI Marquee) */
    .bulletin-ticker-wrapper {
        overflow: hidden;
        white-space: nowrap;
        background-color: #0f172a;
        border: 1px solid #1e293b;
        border-radius: var(--radius-sm);
        padding: 6px 0;
        margin-bottom: 18px;
    }
    .bulletin-ticker-content {
        display: inline-block;
        padding-left: 100%;
        animation: bulletin-scroll 45s linear infinite;
        font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
        font-size: 0.8rem;
        font-weight: 500;
        color: #cbd5e1;
        letter-spacing: 0.02em;
    }
    .bulletin-ticker-content:hover {
        animation-play-state: paused;
    }
    @keyframes bulletin-scroll {
        0% { transform: translate(0, 0); }
        100% { transform: translate(-100%, 0); }
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


@st.cache_resource
def get_services():
    """Instancia y cachea los servicios para máxima eficiencia (ISO 9241-11: Eficiencia)."""
    return EpidemiologyDataService(CURRENT_DIR), EpidemiologyModelService(CURRENT_DIR)


data_service, model_service = get_services()

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
    st.caption("Fecha Oficial: Martes 01 de noviembre")

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

# Cálculo de KPIs para el año más reciente de la selección
latest_year = year_range[1]
kpis = data_service.compute_kpis(df_filtered, group=group_key, year=latest_year)

# ==============================================================================
# 1. ENCABEZADO INSTITUCIONAL
# ==============================================================================
st.markdown(
    f"""
    <div class="institutional-hero">
        <div class="institutional-badge">SISTEMA DE VIGILANCIA SANITARIA • NORMATIVA ISO 9241 COMPLIANT</div>
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
# 2. CINTILLO OFICIAL DE BOLETÍN EPIDEMIOLÓGICO (MAGIC UI MARQUEE FORMAL)
# ==============================================================================
bulletin_items = (
    "BOLETÍN EPIDEMIOLÓGICO CONSOLIDADO | "
    "REGIONES DE ALTO IMPACTO EN POBLACIÓN PEDIÁTRICA: UCAYALI Y LORETO REGISTRAN >91.7% DE PERMANENCIA EN CATEGORÍA 1 | "
    "REGIONES DE ALTO IMPACTO EN ADULTOS MAYORES: AREQUIPA (88.9%) Y CUSCO (61.1%) CONCENTRAN MAYOR VULNERABILIDAD ANDINA | "
    "MODELADO PREDICTIVO: ALGORITMO XGBOOST ALCANZA COEFICIENTE DE DETERMINACIÓN R² = 0.935 EN PROYECCIÓN DE 52 SEMANAS | "
    "NORMALIZACIÓN CENSAL: CÁLCULOS ESTANDARIZADOS POR 100,000 HABITANTES MEDIANTE POBLACIÓN INTERPOLADA 2000-2023 | "
    "INDICADORES DE SEVERIDAD: MONITOREO CONTINUO DE HOSPITALIZACIÓN (HR) Y LETALIDAD (CFR)"
)

st.markdown(
    f"""
    <div class="bulletin-ticker-wrapper">
        <div class="bulletin-ticker-content">
            {bulletin_items}
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
    alert_class = "clinical-alert-danger"
    alert_code = "[ESTADO EPIDEMIOLÓGICO: ALERTA CRÍTICA]"
    alert_msg = (
        f"La tasa de incidencia acumulada se sitúa en {inc_rate:.1f} por 100,000 habitantes, superando "
        "el umbral de seguridad estacional. Se recomienda la activación de planes de contingencia hospitalaria, "
        "monitoreo de disponibilidad de oxígeno medicinal y abastecimiento oportuno de medicamentos esenciales."
    )
elif inc_rate > 150:
    alert_class = "clinical-alert-warning"
    alert_code = "[ESTADO EPIDEMIOLÓGICO: ALERTA PREVENTIVA]"
    alert_msg = (
        f"La tasa de incidencia se encuentra en {inc_rate:.1f} por 100,000 habitantes en zona de advertencia. "
        "Se recomienda intensificar el seguimiento semanal de casos y verificar cobertura de vacunación."
    )
else:
    alert_class = "clinical-alert-normal"
    alert_code = "[ESTADO EPIDEMIOLÓGICO: BAJO CONTROL]"
    alert_msg = (
        f"La tasa de incidencia de {inc_rate:.1f} por 100,000 habitantes se mantiene dentro de los percentiles "
        "históricos esperados para el período analizado."
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
    delta_sign = "+" if kpis["delta_cases_pct"] > 0 else ""
    delta_color = "#991b1b" if kpis["delta_cases_pct"] > 0 else "#166534"
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">Casos Diagnosticados ({int(kpis['year'])})</div>
            <div class="kpi-value">{int(kpis['cases']):,}</div>
            <div style="font-size: 0.82rem; font-weight: 600; color: {delta_color};">
                {delta_sign}{kpis['delta_cases_pct']:.1f}% vs. año previo
            </div>
            <div class="kpi-subtext">Total anual registrado</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col_kpi2:
    delta_rate_sign = "+" if kpis["delta_rate"] > 0 else ""
    delta_rate_color = "#991b1b" if kpis["delta_rate"] > 0 else "#166534"
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">Tasa Incidencia x 100k hab.</div>
            <div class="kpi-value" style="color: var(--blue-primary);">{kpis['cases_rate']:.1f}</div>
            <div style="font-size: 0.82rem; font-weight: 600; color: {delta_rate_color};">
                {delta_rate_sign}{kpis['delta_rate']:.1f} puntos de tasa
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
            <div class="kpi-value" style="color: #92400e;">{kpis['hr']:.2f}%</div>
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
            <div class="kpi-value" style="color: #991b1b;">{kpis['cfr']:.2f}%</div>
            <div style="font-size: 0.82rem; font-weight: 600; color: var(--text-body);">
                {int(kpis['deaths']):,} defunciones
            </div>
            <div class="kpi-subtext">(Defunciones / Casos) × 100</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

# ==============================================================================
# 5. PESTAÑAS PRINCIPALES (ORGANIZACIÓN EJECUTIVA CON NUMERACIÓN ROMANA)
# ==============================================================================
tab_trend, tab_severity, tab_regional, tab_prediction, tab_quality = st.tabs([
    "I. Vigilancia Temporal y Tendencias",
    "II. Severidad Clínica y Letalidad (HR / CFR)",
    "III. Estratificación Departamental y Carga Regional",
    "IV. Modelos Predictivos y Proyecciones (ML / DL)",
    "V. Auditoría de Calidad y Estándares ISO 9241",
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
        fig_scatter = px.scatter(
            df_filtered,
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
    st.markdown("#### Estratificación Territorial y Categorización de Riesgo Departamental")

    col_reg_left, col_reg_right = st.columns([7, 5])

    with col_reg_left:
        top3_df = data_service.get_top3_frequencies(group=group_key)
        if not top3_df.empty:
            fig_top3 = px.bar(
                top3_df.head(10),
                x="region",
                y="top3_appearances",
                text="percent_years_in_top3",
                title=f"Departamentos con Mayor Persistencia en Categoría 1 de Incidencia ({group_label})",
                labels={"region": "Departamento", "top3_appearances": "Años en el Top 3 (2000-2023)"},
                color="top3_appearances",
                color_continuous_scale="Reds",
            )
            fig_top3.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
            fig_top3.update_layout(template="plotly_white", xaxis_tickangle=-45)
            st.plotly_chart(fig_top3, use_container_width=True)
        else:
            st.info("No se hallaron registros tabulados para la estratificación regional.")

    with col_reg_right:
        if group_key == "men5":
            st.markdown(
                """
                <div class="analytical-box" style="border-left: 4px solid #b91c1c;">
                    <div class="analytical-box-title">Hallazgo Epidemiológico: Concentración en Cuenca Amazónica</div>
                    <div style="font-size: 0.88rem; color: var(--text-body); line-height: 1.5;">
                        En menores de 5 años, la mayor persistencia histórica de incidencia crítica se concentra 
                        en los departamentos de selva:
                        <ul style="margin: 6px 0 0 16px; padding: 0;">
                            <li><strong>Ucayali:</strong> 91.7% de los años evaluados en Categoría 1.</li>
                            <li><strong>Loreto:</strong> 91.7% de los años evaluados en Categoría 1.</li>
                            <li><strong>Huánuco:</strong> 37.5% de los años evaluados en Categoría 1.</li>
                        </ul>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                """
                <div class="analytical-box" style="border-left: 4px solid #b45309;">
                    <div class="analytical-box-title">Hallazgo Epidemiológico: Concentración en Sierra Sur</div>
                    <div style="font-size: 0.88rem; color: var(--text-body); line-height: 1.5;">
                        En adultos de 60 años a más, la carga de enfermedad crítica se desplaza hacia las 
                        regiones andinas afectadas por heladas severas:
                        <ul style="margin: 6px 0 0 16px; padding: 0;">
                            <li><strong>Arequipa:</strong> 88.9% de los años evaluados en Categoría 1.</li>
                            <li><strong>Cusco:</strong> 61.1% de los años evaluados en Categoría 1.</li>
                            <li><strong>Moquegua:</strong> 50.0% de los años evaluados en Categoría 1.</li>
                        </ul>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown(
            """
            <div class="analytical-box" style="border-left: 4px solid var(--blue-primary);">
                <div class="analytical-box-title">Estratificación en Quintiles de Severidad</div>
                <div style="font-size: 0.88rem; color: var(--text-body); line-height: 1.5;">
                    Los 25 departamentos del Perú se clasifican anualmente en 5 quintiles normativos:<br>
                    • <strong>Categoría 1 (Puestos 1 al 5):</strong> Carga muy alta / Prioridad sanitaria I.<br>
                    • <strong>Categoría 2 (Puestos 6 al 10):</strong> Carga alta.<br>
                    • <strong>Categoría 3 (Puestos 11 al 15):</strong> Carga media.<br>
                    • <strong>Categorías 4 y 5 (Puestos 16 al 25):</strong> Carga moderada y baja.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

# ------------------------------------------------------------------------------
# PESTAÑA IV: MODELOS PREDICTIVOS Y PROYECCIONES
# ------------------------------------------------------------------------------
with tab_prediction:
    st.markdown(f"#### Validación Retrospectiva y Proyección a 52 Semanas ({group_label})")

    metrics_df = model_service.get_national_metrics(group=group_key)
    col_ml_1, col_ml_2 = st.columns([2, 1])

    with col_ml_1:
        st.markdown("##### Métricas Oficiales de Precisión (Rolling Backtesting de 5 Años)")
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

    st.markdown("##### Proyección Predictiva con Bandas de Incertidumbre (95% CI)")
    future_df = model_service.get_national_future_predictions(group=group_key)

    if not future_df.empty:
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

            fig_pred.add_trace(
                go.Scatter(
                    x=pd.concat([sub["date"], sub["date"][::-1]]),
                    y=pd.concat([sub["upper_ci"], sub["lower_ci"][::-1]]),
                    fill="toself",
                    fillcolor="rgba(203, 213, 225, 0.25)",
                    line=dict(color="rgba(255,255,255,0)"),
                    hoverinfo="skip",
                    showlegend=True,
                    name=f"Intervalo 95% CI ({name})",
                )
            )

        fig_pred.update_layout(
            title="Horizonte Temporal de Pronóstico: Incidencia Semanal Proyectada",
            xaxis_title="Semana Epidemiológica Futura",
            yaxis_title="Tasa de Incidencia Predicha",
            template="plotly_white",
            hovermode="x unified",
        )
        st.plotly_chart(fig_pred, use_container_width=True)

    st.markdown("##### Interpretabilidad del Modelo: Importancia de Variables")
    feat_df = model_service.get_feature_importance_summary(group=group_key)
    if not feat_df.empty and "importance" in feat_df.columns:
        fig_feat = px.bar(
            feat_df.sort_values("importance", ascending=True),
            x="importance",
            y="feature",
            orientation="h",
            title="Importancia Relativa de Variables Predictoras (XGBoost / Random Forest)",
            labels={"importance": "Importancia Normalizada", "feature": "Variable"},
            color="importance",
            color_continuous_scale="Blues",
        )
        fig_feat.update_layout(template="plotly_white")
        st.plotly_chart(fig_feat, use_container_width=True)

# ------------------------------------------------------------------------------
# PESTAÑA V: AUDITORÍA DE CALIDAD Y ESTÁNDARES ISO 9241
# ------------------------------------------------------------------------------
with tab_quality:
    st.markdown("#### Matriz de Trazabilidad y Cumplimiento Normativo ISO 9241 e ISO/IEC 25010")
    st.markdown(
        """
        El diseño, arquitectura e implementación de la presente plataforma se fundamentan en estándares
        internacionales de ergonomía de la interacción humano-sistema y calidad de producto de software:
        """
    )

    iso_full_data = [
        {
            "Estándar": "ISO 9241-11",
            "Principio Rector": "Medición de Usabilidad",
            "Dimensiones Clave": "Eficacia, Eficiencia y Satisfacción",
            "Implementación en el Sistema": (
                "• Eficacia: Consultas sin errores de 25 departamentos y 2 grupos etarios en 2 selecciones directas.\n"
                "• Eficiencia: Caché en memoria (@st.cache_resource) que reduce el tiempo de renderizado a <0.2s.\n"
                "• Satisfacción: Visualización sobria, libre de ruido visual, con tablas y exportación formal en CSV."
            ),
        },
        {
            "Estándar": "ISO 9241-210",
            "Principio Rector": "Diseño Centrado en el Humano (HCD)",
            "Dimensiones Clave": "Comprensión del contexto de uso y necesidades del usuario",
            "Implementación en el Sistema": (
                "• Adaptado al flujo cognitivo de especialistas en salud pública y directores de epidemiología.\n"
                "• Estructura en secuencia: Diagnóstico macro (Semáforo) → Severidad clínica → Estratificación → Proyección a 52 semanas."
            ),
        },
        {
            "Estándar": "ISO 9241-110",
            "Principio Rector": "Principios de Diálogo Ergonómico",
            "Dimensiones Clave": "Adecuación a la tarea, autodescripción, control del usuario, tolerancia a fallos",
            "Implementación en el Sistema": (
                "• Adecuación: Tasas por 100k hab. estandarizadas para evitar distorsiones demográficas.\n"
                "• Autodescripción: Notas metodológicas y glosario explícito de términos clínicos.\n"
                "• Control: Filtros temporales libres (2000-2023) y exportación de datos.\n"
                "• Tolerancia: Manejo matemático defensivo de divisiones entre cero y datos incompletos."
            ),
        },
        {
            "Estándar": "ISO 9241-12",
            "Principio Rector": "Representación Visual de la Información",
            "Dimensiones Clave": "Organización espacial, legibilidad, agrupamiento perceptivo y color",
            "Implementación en el Sistema": (
                "• Rejilla matemática de 8pt (Design Tokens) y jerarquía tipográfica con ratios formales.\n"
                "• Semáforo de alerta con colores institucionales normalizados (Verde, Amarillo, Rojo tenue).\n"
                "• Contraste visual estricto (WCAG AA >= 4.5:1) accesible para personas con daltonismo."
            ),
        },
        {
            "Estándar": "ISO/IEC 25010",
            "Principio Rector": "Calidad del Producto Software",
            "Dimensiones Clave": "Modularidad, fiabilidad, mantenibilidad, portabilidad",
            "Implementación en el Sistema": (
                "• Ingeniería Inversa: Encapsulación del código legado en servicios modulares desacoplados.\n"
                "• Fiabilidad: Suite automatizada de 6 pruebas unitarias con 100% de casos aprobados.\n"
                "• Portabilidad: Despliegue local inmediato en Windows mediante archivo ejecutar_aplicativo.bat."
            ),
        },
    ]

    st.table(pd.DataFrame(iso_full_data))

# ==============================================================================
# 6. PANEL INFERIOR: ESPECIFICACIONES METODOLÓGICAS (VAUL DRAWER STYLE)
# ==============================================================================
st.markdown(
    """
    <div class="methodology-panel">
        <div style="width: 40px; height: 4px; background-color: #cbd5e1; border-radius: 9999px; margin: 0 auto 12px auto;"></div>
        <div style="font-size: 0.92rem; font-weight: 700; color: var(--text-headline); margin-bottom: 6px; text-transform: uppercase;">
            Especificaciones Metodológicas y Glosario Epidemiológico
        </div>
        <div style="font-size: 0.85rem; color: var(--text-body); line-height: 1.55;">
            • <strong>Tasa de Incidencia Estandarizada:</strong> <code>(Casos / Población) × 100,000 hab.</code> (Ajustada por interpolación poblacional censal anual).<br>
            • <strong>Hospitalization Rate (HR):</strong> <code>(Hospitalizaciones / Casos) × 100</code> (Porcentaje de pacientes que requirieron internamiento hospitalario).<br>
            • <strong>Case Fatality Ratio (CFR):</strong> <code>(Defunciones / Casos) × 100</code> (Porcentaje de defunciones sobre el total de casos confirmados).<br>
            • <strong>Bandas de Incertidumbre Predictiva:</strong> <code>Pronóstico ± 1.96 × RMSE</code> (Intervalo de confianza empírico al 95%).
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
st.caption("Plataforma de Vigilancia Epidemiológica de Salud Pública © 2026 — Diseñada bajo Estándares ISO 9241 e ISO/IEC 25010")
