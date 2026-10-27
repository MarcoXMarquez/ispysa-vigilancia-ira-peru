"""Pestaña III: Estratificación Territorial, Ranking Top 3 y Vulnerabilidad Bioclimática."""

import streamlit as st

from src.app_indicators import top3_for_period
from src.epidemiology_analytics import compute_bioclimatic_vulnerability
from src.ui import charts, components
from src.ui.state import ViewContext


def render(ctx: ViewContext) -> None:
    """Renderiza la pestaña de distribución territorial y vulnerabilidad regional."""
    # 1. Ranking Departamental Top 3
    components.section_header(
        "Persistencia en el Top 3 por incidencia",
        f"Frecuencia en puestos 1 a 3 por tasa de incidencia ({ctx.filters.group_label}).",
        testid="sec-top3",
    )

    rank_grid = ctx.data_service.get_rank_grid(group=ctx.filters.group_key)
    year_range = (ctx.filters.year_from, ctx.filters.year_to)
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
            with st.container(border=True):
                fig_top3 = charts.build_top3_figure(top3_df)
                st.plotly_chart(fig_top3, use_container_width=True, config=components.PLOTLY_CONFIG)

        with col_reg_right:
            st.markdown("##### Departamentos con mayor frecuencia")
            st.dataframe(
                top3_df.head(5).rename(
                    columns={
                        "region": "Departamento",
                        "top3_appearances": "Años Top 3",
                        "observed_years": "Años con ranking",
                        "percent_years_in_top3": "% Top 3",
                    }
                ),
                use_container_width=True,
                hide_index=True,
            )
            st.markdown(
                "**Cómo leerlo:** Top 3 significa puestos 1, 2 o 3 por tasa anual de incidencia. "
                "Se conservan los empates del ranking original."
            )

        csv_top3 = top3_df.to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            "Descargar ranking del período (.CSV)",
            data=csv_top3,
            file_name=f"ranking_top3_{ctx.filters.group_key}_{year_range[0]}_{year_range[1]}.csv",
            mime="text/csv",
        )

    # 2. Vulnerabilidad Bioclimática
    components.section_header(
        "Vulnerabilidad bioclimática",
        "Estratificación regional combinando la tasa de incidencia con la exposición climática extrema.",
        testid="sec-bioclimatic",
    )

    df_bioclim = compute_bioclimatic_vulnerability(
        ctx.data_service.get_annual_measures(),
        year=ctx.latest_year,
        group=ctx.filters.group_key,
    )

    col_bio_chart, col_bio_info = st.columns([7, 5])
    with col_bio_chart:
        with st.container(border=True):
            fig_bio = charts.build_bioclimatic_figure(df_bioclim, top_n=10)
            st.plotly_chart(fig_bio, use_container_width=True, config=components.PLOTLY_CONFIG)

    with col_bio_info:
        st.markdown("##### Top 5 departamentos en riesgo bioclimático crítico")
        st.dataframe(
            df_bioclim.head(5)[
                ["department", "climate_zone", "incidence_rate", "composite_risk_score", "risk_tier"]
            ].rename(
                columns={
                    "department": "Departamento",
                    "climate_zone": "Zona Climática",
                    "incidence_rate": "Tasa x 100k",
                    "composite_risk_score": "Score Riesgo",
                    "risk_tier": "Nivel de Alerta",
                }
            ),
            use_container_width=True,
            hide_index=True,
        )
        st.markdown(
            "- **Heladas altoandinas (factor 1.35x):** Estrés térmico severo en zonas > 3 000 msnm.\n"
            "- **Friaje amazónico (factor 1.25x):** Descenso brusco térmico por vientos subantárticos."
        )

    st.caption(
        "Factores de ponderación: 1.35× (heladas altoandinas) y 1.25× (friaje amazónico). "
        "Supuesto metodológico para priorización preventiva regional."
    )
