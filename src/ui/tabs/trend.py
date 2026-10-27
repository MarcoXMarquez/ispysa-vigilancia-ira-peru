"""Pestaña I: Vigilancia Temporal y Tendencias Históricas."""

import streamlit as st

from src.epidemiology_analytics import compute_bortman_corridor
from src.ui import charts, components
from src.ui.state import ViewContext


def render(ctx: ViewContext) -> None:
    """Renderiza la pestaña de tendencias temporales y canal endémico de Bortman."""
    # 1. Serie Temporal Anual
    components.section_header(
        "Tendencia histórica anual",
        f"Evolución temporal de indicadores para {ctx.scope_title} ({ctx.filters.year_from}–{ctx.filters.year_to}).",
        testid="sec-trend-series",
    )

    col_opt_left, col_opt_right = st.columns([3, 1])
    with col_opt_right:
        metric_choice = st.selectbox(
            "Seleccionar Indicador:",
            options=["Tasa de Incidencia x 100k hab.", "Casos Notificados", "Hospitalizaciones", "Defunciones"],
            index=0,
        )

    metric_map = {
        "Tasa de Incidencia x 100k hab.": f"cases_rate_{ctx.filters.group_key}",
        "Casos Notificados": f"cases_{ctx.filters.group_key}",
        "Hospitalizaciones": f"hosp_{ctx.filters.group_key}",
        "Defunciones": f"death_{ctx.filters.group_key}",
    }
    selected_col = metric_map[metric_choice]

    with st.container(border=True):
        fig_trend = charts.build_trend_figure(
            ctx.df,
            selected_col,
            group_key=ctx.filters.group_key,
            y_title=metric_choice,
            year_range=(ctx.filters.year_from, ctx.filters.year_to),
        )
        st.plotly_chart(fig_trend, use_container_width=True, config=components.PLOTLY_CONFIG)

    # Expander de datos y descarga CSV
    with st.expander("Tabla de datos retrospectivos y exportación"):
        display_cols = [
            "year",
            f"cases_{ctx.filters.group_key}",
            f"cases_rate_{ctx.filters.group_key}",
            f"hosp_{ctx.filters.group_key}",
            f"death_{ctx.filters.group_key}",
            f"hr_{ctx.filters.group_key}",
            f"cfr_{ctx.filters.group_key}",
        ]
        available_cols = [c for c in display_cols if c in ctx.df.columns]
        df_display = ctx.df[available_cols].rename(
            columns={
                "year": "Año",
                f"cases_{ctx.filters.group_key}": "Casos",
                f"cases_rate_{ctx.filters.group_key}": "Tasa x 100k",
                f"hosp_{ctx.filters.group_key}": "Hospitalizados",
                f"death_{ctx.filters.group_key}": "Defunciones",
                f"hr_{ctx.filters.group_key}": "HR (%)",
                f"cfr_{ctx.filters.group_key}": "CFR (%)",
            }
        )
        st.dataframe(df_display, use_container_width=True, hide_index=True)
        csv_data = df_display.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="Descargar Serie Consolidada (.CSV)",
            data=csv_data,
            file_name=f"reporte_epidemiologico_{ctx.filters.group_key}_{ctx.scope_title.lower().replace(' ', '_')}.csv",
            mime="text/csv",
        )

    # 2. Canal Endémico de Bortman
    components.section_header(
        "Canal endémico de Bortman",
        "Zonas de comportamiento: Éxito (<Q1), Seguridad (Q1–Q2), Alarma (Q2–Q3) y Epidemia (≥Q3).",
        testid="sec-bortman",
    )

    inc_rate = float(ctx.kpis.get("cases_rate", 0.0))
    corridor = compute_bortman_corridor(ctx.df, f"cases_rate_{ctx.filters.group_key}", target_value=inc_rate)

    with st.container(border=True):
        fig_bortman = charts.build_bortman_figure(
            corridor,
            ctx.df,
            f"cases_rate_{ctx.filters.group_key}",
            current_value=inc_rate,
        )
        st.plotly_chart(fig_bortman, use_container_width=True, config=components.PLOTLY_CONFIG)

    # Resumen cuantitativo de cuartiles en stat_grid
    stats = [
        {"label": "Cuartil 1 (Éxito)", "value": f"{corridor['q1']:.1f}", "subtext": "Incidencia mínima esperada"},
        {"label": "Cuartil 2 (Mediana)", "value": f"{corridor['q2']:.1f}", "subtext": "Límite zona seguridad"},
        {"label": "Cuartil 3 (Alarma)", "value": f"{corridor['q3']:.1f}", "subtext": "Umbral de alarma"},
        {
            "label": f"Estado ({ctx.latest_year})",
            "value": corridor["zone_name"],
            "subtext": f"{inc_rate:.1f} x 100k hab.",
        },
    ]
    components.stat_grid(stats)

    st.caption(
        "Nota metodológica: El canal endémico de Bortman delimita los cuartiles según la serie histórica (OPS/MINSA)."
    )
