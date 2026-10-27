"""Pestaña IV: Modelos Predictivos, Evaluación Histórica y Proyecciones a 52 Semanas."""

import streamlit as st

from src.ui import charts, components
from src.ui.state import ViewContext


def render(ctx: ViewContext) -> None:
    """Renderiza la pestaña de modelos predictivos y pronósticos de series de tiempo."""
    components.section_header(
        "Pronóstico nacional",
        f"Evaluación histórica y proyección a 52 semanas para {ctx.filters.group_label}.",
        testid="sec-forecast",
    )

    st.info(
        "Esta pestaña muestra resultados nacionales precalculados para el grupo poblacional elegido. "
        "La selección de departamento y de años no modifica estos modelos ni vuelve a entrenarlos."
    )

    metrics_df = ctx.model_service.get_national_metrics(group=ctx.filters.group_key)
    col_ml_1, col_ml_2 = st.columns([2, 1])

    with col_ml_1:
        st.markdown("##### Evaluación histórica: horizonte de 4 semanas")
        st.caption(
            "Backtesting con ventanas de entrenamiento de 5 años y avance de 4 semanas. "
            "Estas métricas no corresponden a la proyección de 52 semanas."
        )
        st.dataframe(
            metrics_df[["model_display", "mae", "rmse", "r2"]].rename(
                columns={
                    "model_display": "Modelo Evaluado",
                    "mae": "MAE",
                    "rmse": "RMSE",
                    "r2": "Coeficiente R²",
                }
            ),
            use_container_width=True,
            hide_index=True,
        )

    with col_ml_2:
        best_model = metrics_df.sort_values("r2", ascending=False).iloc[0]
        stats_best = [
            {
                "label": "Modelo Óptimo (Mayor R²)",
                "value": str(best_model["model_display"]),
                "subtext": (
                    f"R²: {best_model['r2']:.3f} · RMSE: {best_model['rmse']:.3f} · MAE: {best_model['mae']:.3f}"
                ),
            }
        ]
        components.stat_grid(stats_best)

    # Proyección a 52 semanas
    st.markdown("##### Proyección nacional a 52 semanas con bandas aproximadas")
    st.caption(
        "Las bandas se construyen como pronóstico ± 1.96 × RMSE, con límite inferior en cero. "
        "Esta aproximación no demuestra por sí sola una cobertura del 95 % a 52 semanas."
    )

    future_df = ctx.model_service.get_national_future_predictions(group=ctx.filters.group_key)
    history_df = ctx.model_service.get_national_weekly_series(group=ctx.filters.group_key)

    if not future_df.empty:
        with st.container(border=True):
            fig_pred = charts.build_forecast_figure(
                history_df,
                future_df,
                model_name=str(best_model["model_display"]),
                group_key=ctx.filters.group_key,
            )
            st.plotly_chart(fig_pred, use_container_width=True, config=components.PLOTLY_CONFIG)
    else:
        st.info("No hay un archivo de proyecciones disponible para este grupo poblacional.")

    # Interpretabilidad de variables
    st.markdown("##### Interpretabilidad del modelo: importancia de variables")
    st.caption(
        "Referencia de los análisis regionales disponibles. "
        "Este gráfico no cambia con el departamento ni el período seleccionado."
    )

    feat_df = ctx.model_service.get_feature_importance_summary(group=ctx.filters.group_key)
    if not feat_df.empty and "importance" in feat_df.columns:
        with st.container(border=True):
            fig_feat = charts.build_feature_importance_figure(feat_df)
            st.plotly_chart(fig_feat, use_container_width=True, config=components.PLOTLY_CONFIG)
