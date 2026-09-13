"""Cálculos de presentación para los filtros del dashboard."""

from math import isfinite

import pandas as pd


def previous_year_deltas(history, group, year):
    """Compara con el año anterior real, aunque quede fuera del filtro visual.

    None indica que no puede calcularse la comparación, no un cambio de cero.
    """
    current = history.loc[history["year"] == year]
    previous = history.loc[history["year"] == year - 1]
    if current.empty or previous.empty:
        return None, None

    cases = current[f"cases_{group}"].sum(min_count=1)
    previous_cases = previous[f"cases_{group}"].sum(min_count=1)
    rate = current[f"cases_rate_{group}"].mean()
    previous_rate = previous[f"cases_rate_{group}"].mean()

    cases_delta = None
    if isfinite(cases) and isfinite(previous_cases) and previous_cases > 0:
        cases_delta = (cases - previous_cases) / previous_cases * 100
    rate_delta = rate - previous_rate if isfinite(rate) and isfinite(previous_rate) else None
    return cases_delta, rate_delta


def top3_for_period(rank_grid, year_range):
    """Resume los rankings existentes sin ampliar los años de cobertura.

    Conserva empates (puesto <= 3), igual que el proceso de ranking original.
    Los porcentajes usan los años con ranking disponible de cada departamento.
    """
    columns = ["region", "top3_appearances", "observed_years", "percent_years_in_top3"]
    years = sorted(
        int(column) for column in rank_grid.columns
        if str(column).isdigit() and year_range[0] <= int(column) <= year_range[1]
    )
    if rank_grid.empty or "region" not in rank_grid or not years:
        return pd.DataFrame(columns=columns), []

    grid = rank_grid.rename(columns=str)
    ranks = grid[[str(year) for year in years]].apply(pd.to_numeric, errors="coerce")
    valid = ranks.ge(1) & ranks.lt(float("inf"))
    observed = valid.sum(axis=1)
    appearances = (valid & ranks.le(3)).sum(axis=1)
    result = pd.DataFrame({
        "region": grid["region"],
        "top3_appearances": appearances,
        "observed_years": observed,
        "percent_years_in_top3": (appearances / observed.where(observed > 0) * 100).round(1),
    })
    result = result.loc[result["observed_years"] > 0]
    return result.sort_values(
        ["top3_appearances", "region"], ascending=[False, True]
    ).reset_index(drop=True), years
