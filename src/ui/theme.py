"""Sistema de temas, paleta visual y plantillas Plotly para la interfaz ISPySA."""

from pathlib import Path
import plotly.graph_objects as go
import plotly.io as pio

PALETTE = {
    "men5": "#0072B2",
    "60mas": "#D55E00",
    "neutral": "#5B6675",
    "grid": "#E3E6EB",
    "text": "#1B2430",
    "success_band": "rgba(31,78,121,0.10)",
    "safety_band": "rgba(30,107,58,0.10)",
    "alarm_band": "rgba(138,83,0,0.12)",
    "epidemic_band": "rgba(163,32,24,0.10)",
}

FONT = "Inter, Segoe UI, system-ui, sans-serif"


def register_plotly_template() -> None:
    """Registra y activa la plantilla 'ispysa' en Plotly."""
    pio.templates["ispysa"] = go.layout.Template(
        layout=go.Layout(
            font=dict(family=FONT, size=13, color=PALETTE["text"]),
            paper_bgcolor="white",
            plot_bgcolor="white",
            colorway=[
                "#0072B2",
                "#D55E00",
                "#009E73",
                "#CC79A7",
                "#E69F00",
                "#56B4E9",
                "#F0E442",
                "#000000",
            ],
            xaxis=dict(
                showgrid=False,
                linecolor="#C9CFD8",
                ticks="outside",
                tickcolor="#C9CFD8",
                title_standoff=8,
            ),
            yaxis=dict(
                gridcolor=PALETTE["grid"],
                zeroline=False,
                ticks="",
                title_standoff=8,
            ),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="left",
                x=0,
                title=None,
            ),
            margin=dict(l=56, r=24, t=48, b=48),
            hoverlabel=dict(
                font_family=FONT,
                bgcolor="white",
                bordercolor="#C9CFD8",
            ),
            title=dict(text=None),
        )
    )
    pio.templates.default = "ispysa"


def get_css_path() -> Path:
    """Retorna la ruta absoluta al archivo assets/styles.css."""
    return Path(__file__).resolve().parents[2] / "assets" / "styles.css"


def load_css() -> None:
    """Carga e inyecta la hoja de estilos assets/styles.css en Streamlit."""
    css_path = get_css_path()
    if css_path.exists():
        css_text = css_path.read_text(encoding="utf-8")
        from src.ui.components import inject_css
        inject_css(css_text)


def apply() -> None:
    """Aplica la configuración global de diseño (CSS y plantilla Plotly)."""
    register_plotly_template()
    load_css()


def load_landing_css() -> None:
    """Inyecta assets/landing.css (solo la portada Quality Nexus lo necesita)."""
    css_path = get_css_path().with_name("landing.css")
    if css_path.exists():
        from src.ui.components import inject_css
        inject_css(css_path.read_text(encoding="utf-8"))
