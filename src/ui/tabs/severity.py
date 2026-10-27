"""Pestaña II: Severidad Clínica, Demanda Hospitalaria y Triaje Manchester."""

import streamlit as st

from src.epidemiology_analytics import compute_manchester_and_resources
from src.ui import charts, components
from src.ui.state import ViewContext


def render(ctx: ViewContext) -> None:
    """Renderiza la pestaña de severidad clínica y triaje Manchester."""
    components.section_header(
        "Hospitalización y letalidad",
        "Evolución comparativa de la tasa de hospitalización (presión en servicios) y letalidad (gravedad biológica).",
        testid="sec-severity",
    )

    col_sev_a, col_sev_b = st.columns(2)
    with col_sev_a:
        with st.container(border=True):
            fig_sev = charts.build_severity_figure(ctx.df, group_key=ctx.filters.group_key)
            st.plotly_chart(fig_sev, use_container_width=True, config=components.PLOTLY_CONFIG)

    with col_sev_b:
        with st.container(border=True):
            fig_quadrant = charts.build_quadrant_figure(ctx.df, group_key=ctx.filters.group_key)
            st.plotly_chart(fig_quadrant, use_container_width=True, config=components.PLOTLY_CONFIG)

    # Triaje Manchester y Demanda Crítica
    components.section_header(
        "Demanda crítica estimada: UCI y oxígeno (triaje Manchester)",
        "Estimación a partir de HR y supuestos clínicos del triaje Manchester; no sustituye el censo hospitalario.",
        testid="sec-manchester",
    )

    manchester_data = compute_manchester_and_resources(
        ctx.kpis.get("hospitalizations", 0),
        ctx.kpis.get("cases", 0),
        group=ctx.filters.group_key,
    )

    stats_m = [
        {
            "label": "Demanda proyectada camas UCI",
            "value": f"{manchester_data['icu_beds_estimated']} camas",
            "subtext": f"Basado en {int(ctx.kpis.get('hospitalizations', 0)):,} internamientos anuales.",
        },
        {
            "label": "Consumo diario oxígeno medicinal",
            "value": f"{manchester_data['oxygen_demand_m3_day']} m³/día",
            "subtext": f"Equivalente a {manchester_data['oxygen_cylinders_10m3_day']} balones de 10 m³.",
        },
        {
            "label": "Oxigenoterapia en hospitalización",
            "value": f"{manchester_data['ward_oxygen_patients']} pacientes",
            "subtext": "Soporte de bajo y medio flujo (cánula nasal y máscara Venturi).",
        },
    ]
    components.stat_grid(stats_m)

    col_triage_chart, col_triage_table = st.columns([7, 5])
    with col_triage_chart:
        with st.container(border=True):
            fig_triage = charts.build_triage_figure(manchester_data["triage_df"])
            st.plotly_chart(fig_triage, use_container_width=True, config=components.PLOTLY_CONFIG)

    with col_triage_table:
        st.markdown("##### Prioridades de atención clínica")
        st.dataframe(manchester_data["triage_df"], use_container_width=True, hide_index=True)

    with st.expander("Ficha técnica y definiciones de severidad"):
        st.markdown(
            "• **Tasa de Hospitalización (HR):** `(Hospitalizaciones / Casos) × 100`.\n"
            "• **Tasa de Letalidad (CFR):** `(Defunciones / Casos) × 100`.\n"
            "• **Supuestos de soporte vital:** 10% de hospitalizados a UCI en niños, 16% en adultos 60+. "
            "Estimaciones calculadas con fines de planificación logística preliminar."
        )

    st.caption(
        "Tiempos objetivo MTS: Nivel 1 Resucitación (Inmediato), Nivel 2 Emergencia (10 min), "
        "Nivel 3 Urgencia (60 min), Nivel 4 Menor (120 min), Nivel 5 No Urgente (240 min)."
    )
