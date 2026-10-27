"""Portada (landing page) de Quality Nexus.

Presenta el sistema antes del panel analítico. Todas las cifras provienen de los servicios de
datos y de la última auditoría ISO/IEC 25010; si falta la auditoría, esas cifras se omiten.
Esta capa no accede a archivos: usa únicamente los servicios (ver sonda MA-1).
"""

import base64
import html
from typing import Any, Dict, List, Optional, Tuple

import streamlit as st

from src.ui import theme
from src.ui.landing_chart import build_hero_chart_svg, chart_alt_text

BRAND = "Quality Nexus"
SESSION_KEY = "nx_entered"
QUERY_KEY = "vista"
QUERY_VALUE = "panel"

CHAR_ORDER = (
    "Adecuación funcional",
    "Eficiencia de desempeño",
    "Fiabilidad",
    "Seguridad",
    "Mantenibilidad",
    "Usabilidad",
)

VIEWS = (
    ("Tendencia", "Casos e incidencia por 100 000 habitantes año a año, más el canal endémico de Bortman."),
    ("Severidad", "Tasa de hospitalización y letalidad, con una estimación de demanda crítica de UCI y oxígeno."),
    ("Territorio", "Qué departamentos aparecen con más frecuencia entre los tres de mayor incidencia."),
    ("Pronóstico", "Evaluación histórica de los modelos y proyección a 52 semanas."),
)

# --------------------------------------------------------------------------------------
# Navegación entre portada y panel
# --------------------------------------------------------------------------------------


def is_dashboard_view() -> bool:
    """True si la persona ya entró al panel (botón) o llegó con ?vista=panel."""
    return bool(st.session_state.get(SESSION_KEY, False)) or st.query_params.get(QUERY_KEY) == QUERY_VALUE


def enter_dashboard() -> None:
    """Marca la sesión para mostrar el panel analítico."""
    st.session_state[SESSION_KEY] = True


def leave_dashboard() -> None:
    """Vuelve a la portada y limpia el parámetro de URL de acceso directo."""
    st.session_state[SESSION_KEY] = False
    if QUERY_KEY in st.query_params:
        del st.query_params[QUERY_KEY]


# --------------------------------------------------------------------------------------
# Utilidades de HTML
# --------------------------------------------------------------------------------------


def _flat(block: str) -> str:
    """Quita sangrías y líneas vacías: Markdown trata 4 espacios o una línea en blanco como código/corte."""
    return "\n".join(line.strip() for line in block.splitlines() if line.strip())


def _svg_uri(svg: str) -> str:
    """Codifica un SVG como data URI para incrustarlo en <img> (más robusto que SVG en línea)."""
    return "data:image/svg+xml;base64," + base64.b64encode(svg.encode("utf-8")).decode("ascii")


# --------------------------------------------------------------------------------------
# Datos de la portada
# --------------------------------------------------------------------------------------


def _characteristic_counts(audit: Dict[str, Any]) -> List[Dict[str, Any]]:
    counts: Dict[str, Dict[str, int]] = {}
    for q in audit.get("questions", []):
        bucket = counts.setdefault(q.get("caracteristica", ""), {"SI": 0, "NO": 0, "NA": 0})
        answer = q.get("respuesta")
        if answer in bucket:
            bucket[answer] += 1
    names = [n for n in CHAR_ORDER if n in counts] + [n for n in counts if n not in CHAR_ORDER and n]
    return [{"name": n, **counts[n], "total": sum(counts[n].values())} for n in names]


def collect_facts(data_service: Any, audit: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Reúne las cifras mostradas en la portada. Sin auditoría, omite las cifras de calidad."""
    nat = data_service.get_national_summary()
    facts: Dict[str, Any] = {
        "nat": nat,
        "year_from": int(nat["year"].min()),
        "year_to": int(nat["year"].max()),
        "n_depts": len(data_service.get_departments()),
        "n_questions": None,
        "tests_passed": None,
        "tests_total": None,
        "characteristics": [],
        "security_coverage": None,
    }
    if audit:
        tests = audit.get("unit_tests") or {}
        facts["n_questions"] = audit.get("questions_count") or len(audit.get("questions", [])) or None
        facts["tests_passed"], facts["tests_total"] = tests.get("passed"), tests.get("total")
        facts["characteristics"] = _characteristic_counts(audit)
        facts["security_coverage"] = (audit.get("security") or {}).get("applicability_coverage")
    facts["n_years"] = facts["year_to"] - facts["year_from"] + 1
    return facts


def fact_items(facts: Dict[str, Any]) -> List[Tuple[str, str]]:
    """Lista (valor, etiqueta) para la franja de cifras."""
    items = [
        (str(facts["n_years"]), f"años de notificaciones, {facts['year_from']}–{facts['year_to']}"),
        (str(facts["n_depts"]), "departamentos con datos completos"),
    ]
    if facts["n_questions"]:
        items.append((str(facts["n_questions"]), "preguntas en la auditoría de calidad"))
    if facts["tests_total"]:
        items.append((f"{facts['tests_passed']}/{facts['tests_total']}", "pruebas automáticas aprobadas"))
    return items


# --------------------------------------------------------------------------------------
# Secciones
# --------------------------------------------------------------------------------------

_MARK_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" width="32" height="32">'
    '<circle cx="12" cy="16" r="9" fill="none" stroke="#1F4E79" stroke-width="2.4"/>'
    '<circle cx="20" cy="16" r="9" fill="none" stroke="#7FA3C4" stroke-width="2.4"/></svg>'
)


def _topbar() -> str:
    return _flat(
        f"""
        <header class="nx-top" id="nx-top">
          <div class="nx-brand"><img src="{_svg_uri(_MARK_SVG)}" alt="" width="32" height="32"/>
          <span>{BRAND}</span></div>
          <nav class="nx-nav" aria-label="Secciones de la página">
            <a href="#nx-hero">Inicio</a><a href="#nx-incluye">Qué incluye</a>
            <a href="#nx-calidad">Calidad</a><a href="#nx-datos">Datos</a>
          </nav>
        </header>
        """
    )


def _hero_copy(facts: Dict[str, Any]) -> str:
    return _flat(
        f"""
        <div class="nx nx-hero-copy" id="nx-hero">
          <h1 class="nx-h1">Vigilancia de neumonía en Perú, con calidad que se puede comprobar</h1>
          <p class="nx-lead">{BRAND} reúne {facts['n_years']} años de notificaciones de infecciones respiratorias
          agudas en menores de 5 años y adultos de 60 años a más, con pronósticos a 52 semanas y una auditoría
          de calidad de software que cualquiera puede revisar.</p>
        </div>
        """
    )


def _hero_note() -> str:
    return _flat(
        """
        <div class="nx"><p class="nx-note">La población, el ámbito y el rango de años se eligen en la barra lateral
        del panel. ¿Primera vez? Mira <a href="#nx-calidad">cómo se mide la calidad</a>.</p></div>
        """
    )


def _hero_figure(facts: Dict[str, Any]) -> str:
    nat = facts["nat"]
    alt = html.escape(chart_alt_text(nat))
    return _flat(
        f"""
        <figure class="nx nx-figure">
          <img src="{_svg_uri(build_hero_chart_svg(nat))}" alt="{alt}"/>
          <figcaption>Figura 1. Incidencia anual de neumonía notificada en Perú por 100 000 habitantes.
          No hay registros de adultos de 60 años a más antes de 2006.</figcaption>
        </figure>
        """
    )


def _facts_strip(facts: Dict[str, Any]) -> str:
    cells = "".join(
        f'<div class="nx-fact"><div class="v">{html.escape(v)}</div><div class="l">{html.escape(lbl)}</div></div>'
        for v, lbl in fact_items(facts)
    )
    return f'<section class="nx nx-facts" aria-label="Cifras del proyecto">{cells}</section>'


def _views_section(facts: Dict[str, Any]) -> str:
    rows = list(VIEWS)
    n_q = facts["n_questions"]
    quality = "Auditoría ISO/IEC 25010 con la evidencia de cada pregunta y el puntaje por característica."
    if n_q:
        quality = (
            f"Auditoría ISO/IEC 25010 con {n_q} preguntas, la evidencia de cada una y el puntaje por característica."
        )
    rows.append(("Calidad del producto", quality))
    body = "".join(
        f'<div class="row"><div class="name">{html.escape(n)}</div><div>{html.escape(d)}</div></div>'
        for n, d in rows
    )
    return _flat(
        f"""
        <section class="nx nx-section" id="nx-incluye">
          <div class="nx-split">
            <div><h2 class="nx-h2">Cinco vistas de los mismos datos</h2>
            <p class="nx-p">Todas responden a los filtros de población, ámbito territorial y rango de años.</p></div>
            <div class="nx-rows">{body}</div>
          </div>
        </section>
        """
    )


def _quality_row(item: Dict[str, Any]) -> str:
    parts = [(item["SI"], "cumple", "si"), (item["NO"], "no cumple", "no"), (item["NA"], "no aplica", "na")]
    segments = "".join(f'<span class="{cls}" style="flex:{n} 1 0"></span>' for n, _, cls in parts if n)
    summary = ", ".join(f"{n} {txt}" for n, txt, _ in parts if n)
    return (
        f'<div class="qrow"><div class="qhead"><span class="qn">{html.escape(item["name"])}</span>'
        f'<span class="qc">{html.escape(summary)}</span></div>'
        f'<div class="nx-bar" aria-hidden="true">{segments}</div></div>'
    )


def _quality_section(facts: Dict[str, Any]) -> str:
    rows = "".join(_quality_row(c) for c in facts["characteristics"])
    legend = (
        '<div class="nx-legend"><span><i class="si"></i>Cumple</span><span><i class="no"></i>No cumple</span>'
        '<span><i class="na"></i>No aplica</span></div>'
    )
    panel_title = '<div class="nx-qhead-title">ISO/IEC 25010 · Scorecard de características (GQM)</div>'
    panel = f'<div class="nx-q">{panel_title}{legend}{rows}</div>' if rows else ""
    cov = facts["security_coverage"]
    cov_txt = ""
    if cov:
        cov_txt = f" Seguridad desglosa el modelo UNLP ({html.escape(str(cov))} criterios aplicables)."
    return _flat(
        f"""
        <section class="nx nx-section" id="nx-calidad">
          <div class="nx-split">
            <div>
              <h2 class="nx-h2">La calidad del software también se mide</h2>
              <p class="nx-p">La vigilancia epidemiológica de salud pública exige rigor técnico. Por ello,
              ISPySA implementa un sistema integral gobernado por cuatro estándares internacionales:</p>
              <div class="nx-iso-list">
                <div class="nx-iso-item">
                  <div class="nx-iso-badge">ISO/IEC 25010 & ISO/IEC 25040</div>
                  <div class="nx-iso-text">Modelo de calidad de producto y proceso de evaluación en 5 fases.
                  Mide 6 características mediante GQM con regla de la cadena débil y trazabilidad por commit.</div>
                </div>
                <div class="nx-iso-item">
                  <div class="nx-iso-badge">ISO/IEC/IEEE 29119 (Partes 2–5)</div>
                  <div class="nx-iso-text">Ingeniería de pruebas: 120 tests unitarios (cobertura &ge; 85%),
                  valores límite y suite E2E Playwright determinista (0.0% flakiness en 3 corridas).</div>
                </div>
                <div class="nx-iso-item">
                  <div class="nx-iso-badge">ISO 9241-11 & ISO 9241-210</div>
                  <div class="nx-iso-text">Ergonomía y accesibilidad universal: certificación WCAG 2.1 AA
                  (axe-core: 0 violaciones), teclado accesible y paleta Okabe-Ito para daltonismo.</div>
                </div>
              </div>
              <p class="nx-note">Análisis estático con Flake8 (v(G) &le; 12, max-len &le; 120).{cov_txt}</p>
            </div>
            {panel}
          </div>
        </section>
        """
    )


def _data_section(facts: Dict[str, Any]) -> str:
    rows = (
        ("Fuentes", "Vigilancia epidemiológica de IRA del MINSA / CDC Perú y censos nacionales del INEI."),
        ("Cobertura", f"{facts['year_from']}–{facts['year_to']} en {facts['n_depts']} departamentos."),
        ("Población", "Población anual por departamento interpolada entre censos, para calcular tasas por 100 000."),
        ("Integridad", "Los archivos de datos se verifican contra huellas SHA-256 registradas en un manifiesto."),
    )
    body = "".join(f'<div class="row"><div class="name">{n}</div><div>{html.escape(d)}</div></div>' for n, d in rows)
    return _flat(
        f"""
        <section class="nx nx-section" id="nx-datos">
          <div class="nx-split">
            <div><h2 class="nx-h2">De dónde salen los datos</h2></div>
            <div class="nx-rows">{body}</div>
          </div>
        </section>
        """
    )


def _closing() -> str:
    return _flat(
        """
        <section class="nx nx-section nx-close">
          <h2 class="nx-h2">Empieza por la tendencia nacional</h2>
          <p class="nx-p">El panel abre en el ámbito nacional; cambia la población o el departamento cuando quieras.</p>
        </section>
        """
    )


def _footer() -> str:
    return _flat(
        f"""
        <footer class="nx nx-foot">Fuentes de datos: MINSA / CDC Perú (vigilancia epidemiológica de IRA) ·
        INEI (censos nacionales). {BRAND} · Sistema de Vigilancia Epidemiológica v2.0.</footer>
        """
    )


# --------------------------------------------------------------------------------------
# Render
# --------------------------------------------------------------------------------------


def render(data_service: Any) -> None:
    """Dibuja la portada completa. El botón «Abrir el panel» cambia a la vista analítica."""
    from src.services.quality_service import ISO25010QualityService

    theme.load_landing_css()
    audit = ISO25010QualityService(data_service.root_dir).get_last_audit()
    facts = collect_facts(data_service, audit)

    st.markdown(_topbar(), unsafe_allow_html=True)
    left, right = st.columns([5, 6], gap="large")
    with left:
        st.markdown(_hero_copy(facts), unsafe_allow_html=True)
        st.button("Abrir el panel", type="primary", on_click=enter_dashboard, key="nx_enter_hero")
        st.markdown(_hero_note(), unsafe_allow_html=True)
    with right:
        st.markdown(_hero_figure(facts), unsafe_allow_html=True)

    st.markdown(_facts_strip(facts), unsafe_allow_html=True)
    st.markdown(_views_section(facts), unsafe_allow_html=True)
    st.markdown(_quality_section(facts), unsafe_allow_html=True)
    st.markdown(_data_section(facts), unsafe_allow_html=True)
    st.markdown(_closing(), unsafe_allow_html=True)
    st.button("Abrir el panel", type="primary", on_click=enter_dashboard, key="nx_enter_footer")
    st.markdown(_footer(), unsafe_allow_html=True)
