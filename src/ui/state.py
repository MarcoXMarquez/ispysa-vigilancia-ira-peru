"""Gestión de estado inmutable de filtros y contexto de visualización de la aplicación."""

from dataclasses import dataclass
from typing import Any, Optional
import pandas as pd

from src.app_indicators import previous_year_deltas


@dataclass(frozen=True)
class FilterState:
    """Estado inmutable de las selecciones de filtro del usuario."""
    group_key: str            # "men5" | "60mas"
    group_label: str          # "Menores de 5 años (men5)" | "Adultos de 60 años a más (60mas)"
    scope: str                # "Nacional" | nombre de departamento
    is_national: bool
    year_from: int
    year_to: int


@dataclass(frozen=True)
class ViewContext:
    """Contexto completo de datos procesados e indicadores para el renderizado de vistas."""
    filters: FilterState
    scope_title: str
    df_raw: pd.DataFrame      # serie histórica completa del ámbito
    df: pd.DataFrame          # serie filtrada por el rango de años
    latest_year: int
    kpis: dict
    cases_delta: Optional[float]
    rate_delta: Optional[float]
    data_service: Any
    model_service: Any


def build_filter_state(sidebar: Any, data_service: Any) -> FilterState:
    """
    Renderiza los controles interactivos en la barra lateral y extrae el FilterState.
    Elimina textos obsoletos de normas y cursos, enfocándose en la tarea analítica.
    """
    sidebar.markdown("### Filtros")
    sidebar.caption("Definen todos los indicadores de la página.")

    # 1. Filtro de población
    pop_options = [
        "Menores de 5 años",
        "Adultos de 60 años a más",
    ]
    selected_pop = sidebar.radio(
        "Población:",
        options=pop_options,
        index=0,
        help="Segmentación demográfica de riesgo conforme a directivas epidemiológicas nacionales.",
    )
    if "Menores" in selected_pop:
        group_key = "men5"
        group_label = "Menores de 5 años (men5)"
    else:
        group_key = "60mas"
        group_label = "Adultos de 60 años a más (60mas)"

    # 2. Filtro de ámbito territorial (departamentos en Title Case)
    raw_deptos = data_service.get_departments()
    depto_map = {d.title(): d for d in raw_deptos}
    scope_options = ["Nacional"] + list(depto_map.keys())

    selected_scope_display = sidebar.selectbox(
        "Ámbito territorial:",
        options=scope_options,
        index=0,
        help="Selección de consolidado nacional o desagregación por departamento.",
    )

    is_national = selected_scope_display == "Nacional"
    if is_national:
        scope = "Nacional"
    else:
        scope = depto_map.get(selected_scope_display, selected_scope_display.upper())

    # 3. Filtro de período temporal
    year_range = sidebar.slider(
        "Período de análisis:",
        min_value=2000,
        max_value=2023,
        value=(2000, 2023),
        step=1,
        help="Ventana temporal para el cómputo de indicadores retrospectivos.",
    )

    sidebar.divider()

    # Expander informativo sobrio
    info_exp = sidebar.expander("Acerca de estos datos")
    with info_exp:
        info_exp.markdown(
            "**Fuentes oficiales:**\n"
            "- **MINSA / CDC Perú:** Notificación epidemiológica semanal de IRA (2000–2023).\n"
            "- **INEI:** Censos 1993, 2007, 2017 e interpolación demográfica exponencial.\n\n"
            "**Cobertura y poblaciones:**\n"
            "- Serie 2000–2023: cohorte pediátrica (< 5 años).\n"
            "- Serie 2006–2023: cohorte geriátrica (≥ 60 años).\n"
            "- Consolidado nacional y 25 departamentos.\n\n"
            "**Estándares ISO aplicados:**\n"
            "- **ISO/IEC 25010 & 25040:** Calidad del producto y proceso GQM (cadena débil).\n"
            "- **ISO/IEC/IEEE 29119:** Pruebas unitarias (120 tests) y E2E Playwright deterministas.\n"
            "- **ISO 9241:** Ergonomía, accesibilidad WCAG 2.1 AA y paleta Okabe-Ito.\n\n"
            "**Versión de plataforma:**\n"
            "- ISPySA-Pneumonia v2.0.0 (Sistema de Información en Salud Pública)."
        )

    return FilterState(
        group_key=group_key,
        group_label=group_label,
        scope=scope,
        is_national=is_national,
        year_from=int(year_range[0]),
        year_to=int(year_range[1]),
    )


def build_view_context(
    filters: FilterState,
    data_service: Any,
    model_service: Any,
) -> Optional[ViewContext]:
    """
    Carga y computa los datos correspondientes a los filtros dados.
    Retorna ViewContext o None si no existen datos en el período/ámbito.
    """
    if filters.is_national:
        df_raw = data_service.get_national_summary()
        scope_title = "Nivel Nacional (Consolidado República del Perú)"
    else:
        df_raw = data_service.get_department_data(filters.scope)
        scope_title = f"Departamento de {filters.scope.title()}"

    if df_raw is None or df_raw.empty:
        return None

    # Filtrar por años
    df = df_raw[
        (df_raw["year"] >= filters.year_from) & (df_raw["year"] <= filters.year_to)
    ].copy()

    if df.empty:
        return None

    latest_year = int(df["year"].max())
    kpis = data_service.compute_kpis(df_raw, group=filters.group_key, year=latest_year)
    cases_delta, rate_delta = previous_year_deltas(df_raw, filters.group_key, latest_year)

    return ViewContext(
        filters=filters,
        scope_title=scope_title,
        df_raw=df_raw,
        df=df,
        latest_year=latest_year,
        kpis=kpis,
        cases_delta=cases_delta,
        rate_delta=rate_delta,
        data_service=data_service,
        model_service=model_service,
    )
