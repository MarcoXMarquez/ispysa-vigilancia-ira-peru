"""Figura principal de la portada: incidencia anual de neumonía en Perú (SVG con datos reales)."""

import html
import math
from typing import Any, Dict, List, Tuple

# Okabe-Ito (igual que src/ui/theme.py); los textos usan variantes más oscuras para cumplir WCAG AA.
SERIES_STYLE = {
    "men5": {"label": "Menores de 5 años", "line": "#0072B2", "text": "#005A8C"},
    "60mas": {"label": "60 años a más", "line": "#D55E00", "text": "#A34700"},
}


def _fmt(value: float, decimals: int = 1) -> str:
    return f"{value:.{decimals}f}"


CHART_W, CHART_H = 520, 400
M_L, M_R, M_T, M_B = 40, 164, 36, 40
LABEL_GAP = 38


def _spread_labels(ys: List[float], gap: float) -> List[float]:
    """Separa verticalmente etiquetas que se solapan, conservando su orden."""
    order = sorted(range(len(ys)), key=lambda i: ys[i])
    out = list(ys)
    for prev, cur in zip(order, order[1:]):
        if out[cur] - out[prev] < gap:
            shift = (gap - (out[cur] - out[prev])) / 2
            out[prev] -= shift
            out[cur] += shift
    return out


def _series_points(nat: Any, key: str) -> List[Tuple[int, float]]:
    """Pares (año, tasa) del grupo; omite años sin casos registrados (60+ empieza en 2006)."""
    cases, rate = nat[f"cases_{key}"], nat[f"cases_rate_{key}"]
    return [(int(y), float(r)) for y, c, r in zip(nat["year"], cases, rate) if c > 0]


def _chart_geometry(nat: Any, series: Dict[str, List[Tuple[int, float]]]) -> Dict[str, Any]:
    y0, y1 = int(nat["year"].min()), int(nat["year"].max())
    top = max((v for pts in series.values() for _, v in pts), default=100.0)
    ymax = max(100, int(math.ceil(top / 100.0) * 100))

    def px(year: float) -> float:
        return M_L + (year - y0) * (CHART_W - M_L - M_R) / max(1, y1 - y0)

    def py(val: float) -> float:
        return CHART_H - M_B - val * (CHART_H - M_T - M_B) / ymax

    return {"y0": y0, "y1": y1, "ymax": ymax, "px": px, "py": py}


def _grid_svg(geo: Dict[str, Any]) -> str:
    parts = [f'<text x="{M_L}" y="18" class="ax">casos por 100 000 hab.</text>']
    for tick in range(0, geo["ymax"] + 1, 100):
        y = geo["py"](tick)
        parts.append(f'<line x1="{M_L}" x2="{CHART_W - M_R}" y1="{y:.1f}" y2="{y:.1f}" class="gr"/>')
        parts.append(f'<text x="{M_L - 8}" y="{y + 4:.1f}" text-anchor="end" class="ax">{tick}</text>')
    ticks = list(range(geo["y0"], geo["y1"] + 1, 5))
    if geo["y1"] not in ticks and geo["y1"] - ticks[-1] >= 3:
        ticks.append(geo["y1"])
    for year in ticks:
        x = geo["px"](year)
        parts.append(f'<text x="{x:.1f}" y="{CHART_H - 14}" text-anchor="middle" class="ax">{year}</text>')
    return "".join(parts)


def _lines_svg(series: Dict[str, List[Tuple[int, float]]], geo: Dict[str, Any]) -> str:
    parts, ends = [], {}
    for idx, (key, pts) in enumerate(series.items()):
        if not pts:
            continue
        style = SERIES_STYLE[key]
        d = " ".join(f"{'M' if i == 0 else 'L'}{geo['px'](y):.1f},{geo['py'](v):.1f}" for i, (y, v) in enumerate(pts))
        parts.append(
            f'<path d="{d}" pathLength="1" class="ln d{idx}" stroke="{style["line"]}"/>'
        )
        ends[key] = (geo["px"](pts[-1][0]), geo["py"](pts[-1][1]), pts[-1][1])
    ys = _spread_labels([e[1] for e in ends.values()], LABEL_GAP)
    for (key, (x, _, val)), y in zip(ends.items(), ys):
        style = SERIES_STYLE[key]
        parts.append(
            f'<g class="lb"><text x="{x + 10:.1f}" y="{y - 2:.1f}" class="nm" fill="{style["text"]}">'
            f'{html.escape(style["label"])}</text>'
            f'<text x="{x + 10:.1f}" y="{y + 14:.1f}" class="vl" fill="{style["text"]}">{_fmt(val)}</text></g>'
        )
    return "".join(parts)


def _minimum_marker(series: Dict[str, List[Tuple[int, float]]], geo: Dict[str, Any]) -> str:
    pts = series.get("men5") or []
    if not pts:
        return ""
    year, val = min(pts, key=lambda p: p[1])
    x, y = geo["px"](year), geo["py"](val)
    color = SERIES_STYLE["men5"]
    return (
        f'<g class="lb"><circle cx="{x:.1f}" cy="{y:.1f}" r="4.5" fill="#fff" '
        f'stroke="{color["line"]}" stroke-width="2.2"/>'
        f'<text x="{x - 10:.1f}" y="{y + 4:.1f}" text-anchor="end" class="vl" fill="{color["text"]}">'
        f"{year}: {_fmt(val)}</text></g>"
    )


_CHART_CSS = (
    "text{font-family:'Segoe UI',system-ui,-apple-system,Arial,sans-serif;font-variant-numeric:tabular-nums}"
    ".ax{font-size:13px;fill:#5B6675}.gr{stroke:#E3E6EB;stroke-width:1}"
    ".nm{font-size:14px;font-weight:600}.vl{font-size:14px;font-weight:600}"
    ".ln{fill:none;stroke-width:2.6;stroke-linejoin:round;stroke-linecap:round;stroke-dasharray:1;"
    "animation:draw 1.8s cubic-bezier(.3,.6,.2,1) .2s backwards}.d1{animation-delay:.55s}"
    ".lb{animation:fade .6s ease 1.8s backwards}"
    "@keyframes draw{from{stroke-dashoffset:1}to{stroke-dashoffset:0}}"
    "@keyframes fade{from{opacity:0}to{opacity:1}}"
    "@media (prefers-reduced-motion:reduce){.ln,.lb{animation:none}}"
)


def build_hero_chart_svg(nat: Any) -> str:
    """Devuelve el SVG de incidencia anual nacional (menores de 5 años y adultos de 60 años a más)."""
    series = {key: _series_points(nat, key) for key in SERIES_STYLE}
    geo = _chart_geometry(nat, series)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {CHART_W} {CHART_H}" width="{CHART_W}" '
        f'height="{CHART_H}"><style>{_CHART_CSS}</style>'
        f'<rect width="{CHART_W}" height="{CHART_H}" fill="#fff"/>'
        f"{_grid_svg(geo)}{_lines_svg(series, geo)}{_minimum_marker(series, geo)}</svg>"
    )


def chart_alt_text(nat: Any) -> str:
    """Descripción textual del gráfico para lectores de pantalla."""
    pts = _series_points(nat, "men5")
    if not pts:
        return "Gráfico de incidencia anual de neumonía en Perú."
    (ya, va), (yb, vb) = pts[0], pts[-1]
    ym, vm = min(pts, key=lambda p: p[1])
    return (
        f"Gráfico de líneas: la incidencia de neumonía en menores de 5 años pasó de {_fmt(va)} por 100 000 "
        f"habitantes en {ya} a {_fmt(vb)} en {yb}, con un mínimo de {_fmt(vm)} en {ym}. "
        "También se muestra la serie de adultos de 60 años a más."
    )
