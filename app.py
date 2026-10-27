"""Punto de entrada de la aplicación de vigilancia epidemiológica de IRA (Perú, 2000-2023)."""

from pathlib import Path
import sys
import streamlit as st

CURRENT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(CURRENT_DIR))

from src.services import EpidemiologyDataService, EpidemiologyModelService  # noqa: E402
from src.ui import components, landing, theme  # noqa: E402
from src.ui.state import build_filter_state, build_view_context  # noqa: E402
from src.ui.tabs import forecast, quality, severity, territory, trend  # noqa: E402

st.set_page_config(
    page_title="Quality Nexus | Vigilancia de IRA en Perú",
    layout="wide",
    initial_sidebar_state="expanded",
)
theme.apply()


@st.cache_resource
def get_services():
    """Inicializa y cachea los servicios de datos y modelos epidemiológicos."""
    return EpidemiologyDataService(CURRENT_DIR), EpidemiologyModelService(CURRENT_DIR)


data_service, model_service = get_services()

# Portada: se muestra hasta que la persona abre el panel (o llega con ?vista=panel).
if not landing.is_dashboard_view():
    landing.render(data_service)
    st.stop()

st.sidebar.button(f"‹ {landing.BRAND}: volver al inicio", on_click=landing.leave_dashboard, key="nx_back_home")
filters = build_filter_state(st.sidebar, data_service)
ctx = build_view_context(filters, data_service, model_service)

if ctx is None:
    st.info("No hay datos para este ámbito y período. Amplía el intervalo de años.")
    st.stop()

components.page_header(ctx)
components.bortman_banner(ctx)
components.kpi_row(ctx)

tabs = st.tabs(["Tendencia", "Severidad", "Territorio", "Pronóstico", "Calidad del producto"])
for tab, module in zip(tabs, (trend, severity, territory, forecast, quality)):
    with tab:
        module.render(ctx)

components.footer()
