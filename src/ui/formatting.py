"""Funciones de formateo numérico y textual para presentación clínica e indicadores."""

from math import isfinite
from typing import Optional, Tuple, Union


def fmt_int(n: Union[int, float, None]) -> str:
    """Formatea un entero con separador de miles con coma. Retorna 'N/D' si es inválido."""
    if n is None:
        return "N/D"
    try:
        val = float(n)
        if not isfinite(val):
            return "N/D"
        return f"{int(round(val)):,}"
    except (ValueError, TypeError):
        return "N/D"


def fmt_rate(r: Union[int, float, None], decimals: int = 1) -> str:
    """Formatea una tasa con punto decimal. Retorna 'N/D' si es inválido."""
    if r is None:
        return "N/D"
    try:
        val = float(r)
        if not isfinite(val):
            return "N/D"
        return f"{val:.{decimals}f}"
    except (ValueError, TypeError):
        return "N/D"


def fmt_pct(p: Union[int, float, None], decimals: int = 2) -> str:
    """Formatea un porcentaje con símbolo %. Retorna 'N/D' si es inválido."""
    if p is None:
        return "N/D"
    try:
        val = float(p)
        if not isfinite(val):
            return "N/D"
        return f"{val:.{decimals}f} %"
    except (ValueError, TypeError):
        return "N/D"


def fmt_delta(
    val: Optional[Union[int, float]],
    unit: str = "",
    is_pct: bool = False,
) -> Tuple[str, str]:
    """
    Formatea una variación anual retornando (texto_con_signo_y_flecha, clase_css).

    - val > 0: ('▲ +{val}{unit}', 'kpi-delta--up')
    - val < 0: ('▼ −{abs(val)}{unit}', 'kpi-delta--down')
    - val == 0: ('– 0.0{unit}', 'kpi-delta--flat')
    - None o NaN: ('Sin dato del año anterior', 'kpi-delta--flat')
    """
    if val is None:
        return "Sin dato del año anterior", "kpi-delta--flat"
    try:
        num = float(val)
        if not isfinite(num):
            return "Sin dato del año anterior", "kpi-delta--flat"
    except (ValueError, TypeError):
        return "Sin dato del año anterior", "kpi-delta--flat"

    if num > 0:
        val_str = f"{num:.1f}"
        return f"▲ +{val_str}{unit}", "kpi-delta--up"
    elif num < 0:
        val_str = f"{abs(num):.1f}"
        return f"▼ −{val_str}{unit}", "kpi-delta--down"
    else:
        return f"– 0.0{unit}", "kpi-delta--flat"
