"""Módulo de construcción de gráficos Plotly puros e independientes de Streamlit."""

from typing import Any, Dict, Optional
import numpy as np
import pandas as pd
import plotly.graph_objects as go

from src.ui.theme import PALETTE


def _empty_figure(annotation_text: str = "Sin datos disponibles", y_title: str = "") -> go.Figure:
    """Retorna una figura vacía con una anotación descriptiva centrada."""
    fig = go.Figure()
    fig.add_annotation(
        text=annotation_text,
        xref="paper",
        yref="paper",
        x=0.5,
        y=0.5,
        showarrow=False,
        font=dict(color=PALETTE["neutral"], size=14),
    )
    fig.update_layout(
        template="ispysa",
        height=400,
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False, title=y_title or "Valor"),
    )
    return fig


def build_trend_figure(
    df: Optional[pd.DataFrame],
    value_col: str,
    group_key: str = "men5",
    y_title: str = "Tasa de Incidencia x 100k hab.",
    year_range: Optional[tuple] = None,
) -> go.Figure:
    """Construye el gráfico de serie temporal anual."""
    if df is None or df.empty or value_col not in df.columns:
        return _empty_figure("Sin datos para el período seleccionado", y_title=y_title)

    filtered = df.dropna(subset=["year", value_col]).sort_values("year")
    if filtered.empty:
        return _empty_figure("Sin datos válidos", y_title=y_title)

    line_color = PALETTE.get(group_key, PALETTE["men5"])
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=filtered["year"],
            y=filtered[value_col],
            mode="lines+markers",
            name=y_title,
            line=dict(color=line_color, width=2.5),
            marker=dict(size=5, color=line_color),
            hovertemplate="%{x}: %{y:,.1f}<extra></extra>",
        )
    )

    fig.update_layout(
        template="ispysa",
        height=400,
        hovermode="x unified",
        xaxis=dict(
            title="Año Epidemiológico",
            tickmode="linear",
            dtick=2,
        ),
        yaxis=dict(
            title=y_title,
        ),
    )
    return fig


def build_bortman_figure(
    corridor: Optional[Dict[str, Any]],
    df: Optional[pd.DataFrame],
    value_col: str,
    current_value: Optional[float] = None,
) -> go.Figure:
    """Construye el canal endémico de Bortman con 4 bandas y etiquetas explícitas."""
    if df is None or df.empty or value_col not in df.columns or not corridor:
        return _empty_figure("Sin datos para el canal endémico", y_title="Tasa de Incidencia x 100k hab.")

    clean_df = df.dropna(subset=["year", value_col]).sort_values("year")
    if clean_df.empty:
        return _empty_figure("Sin registros anuales suficientes", y_title="Tasa de Incidencia x 100k hab.")

    years = clean_df["year"].tolist()
    x_bounds = [years[0], years[-1]] if len(years) > 1 else [years[0] - 0.5, years[0] + 0.5]

    q1 = float(corridor.get("q1", 0.0))
    q2 = float(corridor.get("q2", 0.0))
    q3 = float(corridor.get("q3", 0.0))

    max_observed = float(clean_df[value_col].max()) if not clean_df.empty else q3
    max_y = max(max_observed * 1.15, q3 * 1.35 if q3 > 0 else 10.0)

    fig = go.Figure()

    # 4 bandas de fondo (shapes)
    # 1. Éxito (0 a Q1)
    fig.add_shape(
        type="rect",
        x0=x_bounds[0],
        x1=x_bounds[1],
        y0=0,
        y1=q1,
        fillcolor=PALETTE["success_band"],
        line_width=0,
        layer="below",
    )
    # 2. Seguridad (Q1 a Q2)
    fig.add_shape(
        type="rect",
        x0=x_bounds[0],
        x1=x_bounds[1],
        y0=q1,
        y1=q2,
        fillcolor=PALETTE["safety_band"],
        line_width=0,
        layer="below",
    )
    # 3. Alarma (Q2 a Q3)
    fig.add_shape(
        type="rect",
        x0=x_bounds[0],
        x1=x_bounds[1],
        y0=q2,
        y1=q3,
        fillcolor=PALETTE["alarm_band"],
        line_width=0,
        layer="below",
    )
    # 4. Epidemia (Q3 a max_y)
    fig.add_shape(
        type="rect",
        x0=x_bounds[0],
        x1=x_bounds[1],
        y0=q3,
        y1=max_y,
        fillcolor=PALETTE["epidemic_band"],
        line_width=0,
        layer="below",
    )

    # Etiquetas textuales al borde derecho
    band_labels = [
        {"y": q1 / 2.0 if q1 > 0 else 0.5, "text": "Éxito"},
        {"y": (q1 + q2) / 2.0 if (q1 + q2) > 0 else 1.0, "text": "Seguridad"},
        {"y": (q2 + q3) / 2.0 if (q2 + q3) > 0 else 1.5, "text": "Alarma"},
        {"y": (q3 + max_y) / 2.0 if (q3 + max_y) > 0 else 2.0, "text": "Epidemia"},
    ]
    for lbl in band_labels:
        fig.add_annotation(
            x=x_bounds[1],
            y=lbl["y"],
            text=lbl["text"],
            showarrow=False,
            xanchor="right",
            font=dict(size=11, color=PALETTE["neutral"]),
            opacity=0.85,
        )

    # Líneas de umbrales con trazos distintos
    fig.add_trace(
        go.Scatter(
            x=x_bounds,
            y=[q3, q3],
            mode="lines",
            name=f"Q3 Umbral de Alarma ({q3:.1f})",
            line=dict(color="#A32018", width=1.5, dash="dash"),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=x_bounds,
            y=[q2, q2],
            mode="lines",
            name=f"Q2 Mediana ({q2:.1f})",
            line=dict(color="#D55E00", width=1.5, dash="dot"),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=x_bounds,
            y=[q1, q1],
            mode="lines",
            name=f"Q1 Límite de Éxito ({q1:.1f})",
            line=dict(color="#0072B2", width=1.5, dash="dashdot"),
        )
    )

    # Serie observada
    fig.add_trace(
        go.Scatter(
            x=clean_df["year"],
            y=clean_df[value_col],
            mode="lines+markers",
            name="Incidencia Observada",
            line=dict(color=PALETTE["text"], width=2.5),
            marker=dict(size=6, color=PALETTE["text"]),
            hovertemplate="%{x}: %{y:,.1f}<extra></extra>",
        )
    )

    # Punto actual resaltado
    if current_value is not None and not clean_df.empty:
        last_yr = clean_df["year"].iloc[-1]
        fig.add_trace(
            go.Scatter(
                x=[last_yr],
                y=[current_value],
                mode="markers",
                name=f"Estado Actual ({current_value:.1f})",
                marker=dict(size=11, color=PALETTE["text"], symbol="diamond"),
                hoverinfo="skip",
            )
        )

    fig.update_layout(
        template="ispysa",
        height=400,
        hovermode="x unified",
        xaxis=dict(title="Año Epidemiológico", tickmode="linear", dtick=2),
        yaxis=dict(title="Tasa de Incidencia x 100k hab.", range=[0, max_y]),
    )
    return fig


def build_severity_figure(df: Optional[pd.DataFrame], group_key: str = "men5") -> go.Figure:
    """Construye la evolución comparativa de HR y CFR con trazos diferenciados."""
    hr_col = f"hr_{group_key}"
    cfr_col = f"cfr_{group_key}"

    if df is None or df.empty or hr_col not in df.columns or cfr_col not in df.columns:
        return _empty_figure("Sin datos de severidad", y_title="Porcentaje (%)")

    clean = df.dropna(subset=["year", hr_col, cfr_col]).sort_values("year")
    if clean.empty:
        return _empty_figure("Sin registros de severidad válidos", y_title="Porcentaje (%)")

    fig = go.Figure()
    # HR: Trazo sólido (#E69F00)
    fig.add_trace(
        go.Scatter(
            x=clean["year"],
            y=clean[hr_col],
            name="Tasa de hospitalización (HR %)",
            mode="lines+markers",
            line=dict(color="#E69F00", width=2.5),
            marker=dict(size=5, color="#E69F00"),
            hovertemplate="%{x}: %{y:.2f}%<extra></extra>",
        )
    )
    # CFR: Trazo punteado (#000000)
    fig.add_trace(
        go.Scatter(
            x=clean["year"],
            y=clean[cfr_col],
            name="Letalidad (CFR %)",
            mode="lines+markers",
            line=dict(color="#000000", width=2.0, dash="dot"),
            marker=dict(size=5, color="#000000"),
            hovertemplate="%{x}: %{y:.2f}%<extra></extra>",
        )
    )

    fig.update_layout(
        template="ispysa",
        height=400,
        hovermode="x unified",
        xaxis=dict(title="Año", tickmode="linear", dtick=2),
        yaxis=dict(title="Porcentaje (%)"),
    )
    return fig


def build_quadrant_figure(df: Optional[pd.DataFrame], group_key: str = "men5") -> go.Figure:
    """Construye el cuadrante de dispersión Presión Hospitalaria vs Letalidad."""
    hr_col = f"hr_{group_key}"
    cfr_col = f"cfr_{group_key}"

    if df is None or df.empty or hr_col not in df.columns or cfr_col not in df.columns:
        return _empty_figure("Sin datos para cuadrante", y_title="Letalidad (CFR %)")

    clean = df.dropna(subset=["year", hr_col, cfr_col]).sort_values("year")
    if clean.empty:
        return _empty_figure("Sin datos para cuadrante", y_title="Letalidad (CFR %)")

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=clean[hr_col],
            y=clean[cfr_col],
            mode="markers+text",
            text=clean["year"].astype(str),
            textposition="top center",
            marker=dict(
                size=10,
                color=clean["year"],
                colorscale="Blues",
                showscale=False,
                line=dict(color=PALETTE["neutral"], width=1),
            ),
            hovertemplate="Año %{text}<br>HR: %{x:.2f}%<br>CFR: %{y:.2f}%<extra></extra>",
        )
    )

    # Líneas de referencia guía en las medianas
    med_hr = float(clean[hr_col].median())
    med_cfr = float(clean[cfr_col].median())

    fig.add_vline(x=med_hr, line_dash="dash", line_color=PALETTE["grid"], line_width=1.5)
    fig.add_hline(y=med_cfr, line_dash="dash", line_color=PALETTE["grid"], line_width=1.5)

    fig.update_layout(
        template="ispysa",
        height=400,
        xaxis=dict(title="Tasa de hospitalización (HR %)"),
        yaxis=dict(title="Letalidad (CFR %)"),
    )
    return fig


def build_triage_figure(triage_df: Optional[pd.DataFrame]) -> go.Figure:
    """Construye el gráfico de distribución por Triaje Manchester con etiqueta 'pacientes'."""
    if triage_df is None or triage_df.empty:
        return _empty_figure("Sin datos de triaje", y_title="Nivel de Triaje")

    sorted_df = triage_df.sort_values("Porcentaje", ascending=True)

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            y=sorted_df["Nivel de Triaje"],
            x=sorted_df["Porcentaje"],
            orientation="h",
            text=sorted_df["Pacientes Estimados"],
            texttemplate="%{text:,} pacientes",
            textposition="outside",
            cliponaxis=False,
            marker=dict(color=PALETTE["men5"]),
            hovertemplate="%{y}<br>Proporción: %{x:.1f}%<br>Estimados: %{text:,} pacientes<extra></extra>",
        )
    )

    fig.update_layout(
        template="ispysa",
        height=320,
        xaxis=dict(title="Proporción de Pacientes (%)"),
        yaxis=dict(title="Nivel de Triaje"),
        margin=dict(r=90),
    )
    return fig


def build_top3_figure(top3_df: Optional[pd.DataFrame]) -> go.Figure:
    """Construye el gráfico de barras horizontales de persistencia en el Top 3."""
    if top3_df is None or top3_df.empty:
        return _empty_figure("Sin datos de ranking", y_title="Departamento")

    top10 = top3_df.head(10).sort_values("top3_appearances", ascending=True)

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            y=top10["region"],
            x=top10["top3_appearances"],
            orientation="h",
            text=top10["percent_years_in_top3"],
            texttemplate="%{text:.1f}%",
            textposition="outside",
            cliponaxis=False,
            marker=dict(color=PALETTE["men5"]),
            hovertemplate="%{y}: %{x} años en Top 3 (%{text:.1f}%)<extra></extra>",
        )
    )

    fig.update_layout(
        template="ispysa",
        height=400,
        xaxis=dict(title="Años en el Top 3"),
        yaxis=dict(title="Departamento"),
        margin=dict(r=60),
    )
    return fig


def build_bioclimatic_figure(bio_df: Optional[pd.DataFrame], top_n: int = 10) -> go.Figure:
    """Construye el gráfico de barras horizontales de riesgo bioclimático."""
    if bio_df is None or bio_df.empty:
        return _empty_figure("Sin datos bioclimáticos", y_title="Departamento")

    subset = bio_df.head(top_n).sort_values("composite_risk_score", ascending=True)

    color_map = {
        "Heladas Altoandinas (>3000 msnm)": PALETTE["60mas"],
        "Friaje Amazónico (Selva Baja/Alta)": PALETTE["men5"],
        "Costa y Valles Interandinos": "#009E73",
    }
    bar_colors = [color_map.get(zone, PALETTE["men5"]) for zone in subset["climate_zone"]]

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            y=subset["department"],
            x=subset["composite_risk_score"],
            orientation="h",
            marker=dict(color=bar_colors),
            text=subset["composite_risk_score"],
            texttemplate="%{x:.1f}",
            textposition="outside",
            cliponaxis=False,
            customdata=np.stack((subset["climate_zone"], subset["incidence_rate"]), axis=-1),
            hovertemplate=(
                "<b>%{y}</b><br>Riesgo: %{x:.1f}<br>Zona: %{customdata[0]}<br>Tasa: %{customdata[1]:.1f}<extra></extra>"
            ),
        )
    )

    fig.update_layout(
        template="ispysa",
        height=400,
        xaxis=dict(title="Índice de Riesgo Compuesto"),
        yaxis=dict(title="Departamento"),
        margin=dict(r=50),
    )
    return fig


def build_forecast_figure(
    history_df: Optional[pd.DataFrame],
    forecast_df: Optional[pd.DataFrame],
    model_name: str = "XGBoost",
    group_key: str = "men5",
) -> go.Figure:
    """Construye el gráfico de proyección con bandas aproximadas de incertidumbre."""
    if forecast_df is None or forecast_df.empty:
        return _empty_figure("Sin proyecciones disponibles", y_title="Tasa de Incidencia Predicha")

    fig = go.Figure()

    # Histórico reciente si está disponible
    if history_df is not None and not history_df.empty and "date" in history_df.columns:
        candidates = ["incidence_smooth", "incidence_raw", "cases_rate"]
        rate_col = next((c for c in candidates if c in history_df.columns), None)
        if rate_col:
            hist_clean = history_df.dropna(subset=["date", rate_col]).sort_values("date").tail(52)
            if not hist_clean.empty:
                fig.add_trace(
                    go.Scatter(
                        x=hist_clean["date"],
                        y=hist_clean[rate_col],
                        mode="lines",
                        name="Histórico Observado",
                        line=dict(color=PALETTE["text"], width=2),
                    )
                )

    # Proyección por modelo
    models = forecast_df["model"].unique() if "model" in forecast_df.columns else ["modelo"]
    colors = {"xgboost": PALETTE["men5"], "random_forest": PALETTE["60mas"], "lstm": "#009E73"}

    for mod in models:
        if "model" in forecast_df.columns:
            sub = forecast_df[forecast_df["model"] == mod].sort_values("date")
        else:
            sub = forecast_df.sort_values("date")
        line_color = colors.get(str(mod).lower(), PALETTE["men5"])
        mod_label = "XGBoost" if mod == "xgboost" else "Random Forest" if mod == "random_forest" else str(mod).upper()

        fig.add_trace(
            go.Scatter(
                x=sub["date"],
                y=sub["predicted"],
                mode="lines",
                name=f"Pronóstico {mod_label}",
                line=dict(color=line_color, width=2.5, dash="dash"),
            )
        )

        if "upper_ci" in sub.columns and "lower_ci" in sub.columns:
            fig.add_trace(
                go.Scatter(
                    x=pd.concat([sub["date"], sub["date"][::-1]]),
                    y=pd.concat([sub["upper_ci"], sub["lower_ci"][::-1]]),
                    fill="toself",
                    fillcolor="rgba(203, 213, 225, 0.3)",
                    line=dict(color="rgba(255,255,255,0)"),
                    hoverinfo="skip",
                    showlegend=True,
                    name=f"Banda aproximada ±1.96·RMSE ({mod_label})",
                )
            )

    fig.update_layout(
        template="ispysa",
        height=400,
        hovermode="x unified",
        xaxis=dict(title="Semana Epidemiológica Futura"),
        yaxis=dict(title="Tasa de Incidencia Predicha"),
    )
    return fig


def build_feature_importance_figure(fi_df: Optional[pd.DataFrame]) -> go.Figure:
    """Construye el gráfico de importancia relativa de variables predictoras."""
    if fi_df is None or fi_df.empty or "importance" not in fi_df.columns or "feature" not in fi_df.columns:
        return _empty_figure("Sin datos de interpretabilidad", y_title="Variable")

    sorted_df = fi_df.sort_values("importance", ascending=True)

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            y=sorted_df["feature"],
            x=sorted_df["importance"],
            orientation="h",
            marker=dict(color=PALETTE["men5"]),
            text=sorted_df["importance"],
            texttemplate="%{x:.1%}",
            textposition="outside",
            cliponaxis=False,
            hovertemplate="<b>%{y}</b>: %{x:.2%}<extra></extra>",
        )
    )

    fig.update_layout(
        template="ispysa",
        height=320,
        xaxis=dict(title="Importancia Normalizada"),
        yaxis=dict(title="Variable"),
        margin=dict(r=60),
    )
    return fig


def build_quality_radar(scores: Optional[Dict[str, float]]) -> go.Figure:
    """Construye un gráfico polar/radar de dimensiones de calidad con bandas guía (40, 60, 90)."""
    if not scores:
        return _empty_figure("Sin puntuaciones de calidad", y_title="Puntaje")

    categories = list(scores.keys())
    values = list(scores.values())

    # Cerrar el lazo
    r_vals = values + [values[0]]
    theta_vals = categories + [categories[0]]

    fig = go.Figure()

    # Trazado de datos
    fig.add_trace(
        go.Scatterpolar(
            r=r_vals,
            theta=theta_vals,
            fill="toself",
            fillcolor="rgba(0, 114, 178, 0.15)",
            line=dict(color=PALETTE["men5"], width=2),
            marker=dict(size=6, color=PALETTE["men5"]),
            name="Índice de Calidad",
            hovertemplate="%{theta}: %{r:.1f} pts<extra></extra>",
        )
    )

    fig.update_layout(
        template="ispysa",
        height=400,
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                tickvals=[40, 60, 90],
                ticktext=["40 (Básico)", "60 (Aceptable)", "90 (Excelente)"],
                linecolor=PALETTE["grid"],
                gridcolor=PALETTE["grid"],
            ),
            angularaxis=dict(
                linecolor=PALETTE["grid"],
                gridcolor=PALETTE["grid"],
            ),
        ),
        showlegend=False,
    )
    return fig
