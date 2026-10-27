"""Componentes visuales y contenedores estructurados para Streamlit (HTML institucional)."""

import html
from typing import Any, Dict, List, Optional
import streamlit as st

from src.epidemiology_analytics import compute_bortman_corridor
from src.ui.formatting import fmt_delta, fmt_int, fmt_pct, fmt_rate

PLOTLY_CONFIG = {
    "displaylogo": False,
    "modeBarButtonsToRemove": ["lasso2d", "select2d"],
    "responsive": True,
}


def inject_css(css: str) -> None:
    """Inyecta CSS global en la sesión Streamlit."""
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


def page_header(ctx: Any) -> None:
    """
    Renderiza la cabecera institucional estandarizada.
    Mantiene data-testid='hero-banner' y elimina texto superfluo de certificaciones.
    """
    scope_title = html.escape(str(ctx.scope_title))
    group_label = html.escape(str(ctx.filters.group_label))
    year_from = html.escape(str(ctx.filters.year_from))
    year_to = html.escape(str(ctx.filters.year_to))

    header_html = f"""
<header class="page-header" data-testid="hero-banner">
  <h1>Vigilancia epidemiológica de infecciones respiratorias agudas · Perú</h1>
  <div class="context">
    <span>{scope_title}</span> · <span>{group_label}</span> · <span>{year_from}–{year_to}</span>
  </div>
</header>
"""
    st.markdown(header_html, unsafe_allow_html=True)


def bortman_banner(ctx: Any) -> None:
    """
    Renderiza el banner de alerta epidemiológica basado en el Canal Endémico de Bortman.
    Mantiene data-testid='bortman-alert' con codificación redundante (clase + texto).
    """
    inc_rate = float(ctx.kpis.get("cases_rate", 0.0))
    rate_col = f"cases_rate_{ctx.filters.group_key}"
    corridor = compute_bortman_corridor(ctx.df, rate_col, target_value=inc_rate)

    zone_code = corridor.get("zone_code", "SEGURIDAD")
    level_map = {
        "EPIDEMIA": ("bad", "Zona epidémica"),
        "ALARMA": ("warn", "Zona de alarma"),
        "SEGURIDAD": ("ok", "Zona de seguridad"),
        "EXITO": ("info", "Zona de éxito"),
    }
    level, zona_text = level_map.get(zone_code, ("ok", "Zona de seguridad"))

    q2 = corridor.get("q2", 0.0)
    q3 = corridor.get("q3", 0.0)
    recommendation = html.escape(str(corridor.get("recommendation", "")))
    zona_escaped = html.escape(zona_text)

    banner_html = f"""
<div class="status-banner status-banner--{level}" data-testid="bortman-alert" role="status">
  <div class="title">Canal endémico (Bortman): {zona_escaped}</div>
  <div>Tasa actual {inc_rate:.1f} por 100 000 hab. · Mediana (Q2) {q2:.1f} · Umbral de alarma (Q3) {q3:.1f}</div>
  <div class="caption">Recomendación OPS/MINSA: {recommendation}</div>
</div>
"""
    st.markdown(banner_html, unsafe_allow_html=True)


def kpi_row(ctx: Any) -> None:
    """
    Renderiza la fila de 4 tarjetas de indicadores clave (Casos, Tasa, HR, CFR).
    Conserva los selectores data-testid='kpi-card-*' y la clase .kpi-value.
    """
    col1, col2, col3, col4 = st.columns(4)

    # 1. Casos notificados
    cases_val = fmt_int(ctx.kpis.get("cases", 0))
    cases_delta_txt, cases_delta_cls = fmt_delta(ctx.cases_delta, unit="%")
    with col1:
        st.markdown(
            f"""
<div class="kpi-card" data-testid="kpi-card-cases">
  <div class="kpi-label">Casos notificados ({ctx.latest_year})</div>
  <div class="kpi-value">{cases_val}</div>
  <div class="kpi-delta {cases_delta_cls}">{html.escape(cases_delta_txt)}</div>
  <div class="kpi-subtext">Total anual</div>
</div>
""",
            unsafe_allow_html=True,
        )

    # 2. Tasa de Incidencia
    rate_val = fmt_rate(ctx.kpis.get("cases_rate", 0.0))
    rate_delta_txt, rate_delta_cls = fmt_delta(ctx.rate_delta, unit=" pts")
    with col2:
        st.markdown(
            f"""
<div class="kpi-card" data-testid="kpi-card-rate">
  <div class="kpi-label">Incidencia por 100 000 hab.</div>
  <div class="kpi-value">{rate_val}</div>
  <div class="kpi-delta {rate_delta_cls}">{html.escape(rate_delta_txt)}</div>
  <div class="kpi-subtext">(casos / población) × 100 000</div>
</div>
""",
            unsafe_allow_html=True,
        )

    # 3. Tasa de Hospitalización (HR)
    hr_val = fmt_pct(ctx.kpis.get("hr", 0.0))
    hosp_count = fmt_int(ctx.kpis.get("hospitalizations", 0))
    with col3:
        st.markdown(
            f"""
<div class="kpi-card" data-testid="kpi-card-hr">
  <div class="kpi-label">Tasa de hospitalización</div>
  <div class="kpi-value">{hr_val}</div>
  <div class="kpi-delta kpi-delta--flat">{hosp_count} internamientos</div>
  <div class="kpi-subtext">hospitalizados / casos</div>
</div>
""",
            unsafe_allow_html=True,
        )

    # 4. Letalidad (CFR)
    cfr_val = fmt_pct(ctx.kpis.get("cfr", 0.0))
    death_count = fmt_int(ctx.kpis.get("deaths", 0))
    with col4:
        st.markdown(
            f"""
<div class="kpi-card" data-testid="kpi-card-cfr">
  <div class="kpi-label">Letalidad</div>
  <div class="kpi-value">{cfr_val}</div>
  <div class="kpi-delta kpi-delta--flat">{death_count} defunciones</div>
  <div class="kpi-subtext">defunciones / casos</div>
</div>
""",
            unsafe_allow_html=True,
        )

    st.caption(
        f"Valores del último año del período seleccionado ({ctx.latest_year}). "
        "Las variaciones comparan con el año anterior del mismo ámbito y grupo."
    )


def section_header(
    title: str,
    subtitle: Optional[str] = None,
    testid: Optional[str] = None,
) -> None:
    """Emite un encabezado de sección h2 semántico con data-testid."""
    testid_attr = f' data-testid="{html.escape(testid)}"' if testid else ""
    title_escaped = html.escape(title)
    code = f'<h2{testid_attr}>{title_escaped}</h2>'
    if subtitle:
        code += f'<p class="caption">{html.escape(subtitle)}</p>'
    st.markdown(code, unsafe_allow_html=True)


def stat_grid(
    stats: List[Dict[str, Any]],
    testid: Optional[str] = None,
) -> None:
    """Renderiza una rejilla de estadísticas (.stat-grid con elementos .stat)."""
    items_html = []
    for item in stats:
        label = html.escape(str(item.get("label", "")))
        val = html.escape(str(item.get("value", "")))
        sub = item.get("subtext")
        sub_html = f'<div class="caption">{html.escape(str(sub))}</div>' if sub else ""
        items_html.append(
            f'<div class="stat"><div class="label">{label}</div><div class="value">{val}</div>{sub_html}</div>'
        )
    testid_attr = f' data-testid="{html.escape(testid)}"' if testid else ""
    grid_html = f'<div class="stat-grid"{testid_attr}>{"".join(items_html)}</div>'
    st.markdown(grid_html, unsafe_allow_html=True)


def html_table(
    headers: List[str],
    rows: List[List[str]],
    testid: Optional[str] = None,
) -> None:
    """Renderiza una tabla HTML semántica y accesible con estilos institucionales."""
    testid_attr = f' data-testid="{html.escape(testid)}"' if testid else ""
    th_style = 'style="text-align: left; padding: 8px 12px; border-bottom: 2px solid var(--c-border);"'
    th_html = "".join(f"<th {th_style}>{html.escape(h)}</th>" for h in headers)
    td_style = 'style="padding: 8px 12px; border-bottom: 1px solid var(--c-border);"'
    tr_html = []
    for row in rows:
        td_html = "".join(f"<td {td_style}>{html.escape(str(cell))}</td>" for cell in row)
        tr_html.append(f"<tr>{td_html}</tr>")
    table_code = (
        f'<div class="table-container"{testid_attr} tabindex="0" role="region" '
        f'aria-label="Tabla de datos" style="overflow-x: auto; margin-bottom: 16px;">'
        f'<table style="width: 100%; border-collapse: collapse; font-size: 14px; text-align: left;">'
        f'<thead><tr>{th_html}</tr></thead>'
        f'<tbody>{"".join(tr_html)}</tbody></table></div>'
    )
    st.markdown(table_code, unsafe_allow_html=True)


def footer() -> None:
    """Renderiza el pie de página institucional sobrio."""
    st.caption(
        "Fuentes de datos: MINSA / CDC Perú (vigilancia epidemiológica de IRA) · "
        "INEI (censos nacionales). Sistema de Vigilancia Epidemiológica v2.0."
    )
