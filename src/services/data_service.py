"""
Módulo de Servicio de Datos Epidemiológicos
Encapsula la carga, transformación y cálculo de indicadores epidemiológicos
para el sistema de vigilancia y monitoreo de IRA en el Perú.
"""

from pathlib import Path
from typing import Dict, List, Optional
import pandas as pd
import numpy as np


class EpidemiologyDataService:
    """
    Servicio encargado de la gestión y provisión de datos epidemiológicos
    para la interfaz de vigilancia sanitaria.
    """

    def __init__(self, root_dir: Optional[Path] = None):
        if root_dir is None:
            self.root_dir = Path(__file__).resolve().parents[2]
        else:
            self.root_dir = Path(root_dir)

        self.data_processed = self.root_dir / "data" / "processed"
        self.outputs_tables = self.root_dir / "outputs" / "tables"
        self.outputs_figures = self.root_dir / "outputs" / "figures"

        self._annual_measures_df: Optional[pd.DataFrame] = None

    def get_annual_measures(self) -> pd.DataFrame:
        """Retorna el DataFrame consolidado de medidas anuales por departamento (2000-2023)."""
        if self._annual_measures_df is None:
            path = self.data_processed / "annual_disease_measures_dept_2000_2023.csv"
            if not path.exists():
                path = self.outputs_tables / "annual_disease_measures_dept_2000_2023.csv"

            df = pd.read_csv(path)
            df["department"] = df["department"].astype(str).str.upper().str.strip()
            df["iddpto"] = df["iddpto"].astype(str).str.zfill(2)
            df["year"] = df["year"].astype(int)
            self._annual_measures_df = df
        return self._annual_measures_df.copy()

    def get_departments(self) -> List[str]:
        """Lista ordenada de todos los departamentos disponibles."""
        df = self.get_annual_measures()
        deptos = sorted(df["department"].unique().tolist())
        return deptos

    def get_national_summary(self) -> pd.DataFrame:
        """
        Calcula y retorna el consolidado nacional de casos, hospitalizaciones,
        defunciones, población y tasas por 100k hab.
        """
        df = self.get_annual_measures()
        nat = (
            df.groupby("year", as_index=False)[
                [
                    "population",
                    "cases_men5",
                    "cases_60mas",
                    "hosp_men5",
                    "hosp_60mas",
                    "death_men5",
                    "death_60mas",
                ]
            ]
            .sum()
            .sort_values("year")
            .reset_index(drop=True)
        )

        for group in ["men5", "60mas"]:
            nat[f"cases_rate_{group}"] = ((nat[f"cases_{group}"] / nat["population"]) * 100000).round(2)
            nat[f"hosp_rate_{group}"] = ((nat[f"hosp_{group}"] / nat["population"]) * 100000).round(2)
            nat[f"death_rate_{group}"] = ((nat[f"death_{group}"] / nat["population"]) * 100000).round(2)

            nat[f"hr_{group}"] = np.where(
                nat[f"cases_{group}"] > 0,
                (nat[f"hosp_{group}"] / nat[f"cases_{group}"]) * 100,
                0.0,
            ).round(2)
            nat[f"cfr_{group}"] = np.where(
                nat[f"cases_{group}"] > 0,
                (nat[f"death_{group}"] / nat[f"cases_{group}"]) * 100,
                0.0,
            ).round(2)

        return nat

    def get_department_data(self, department: str) -> pd.DataFrame:
        """Obtiene la serie temporal completa de un departamento específico."""
        df = self.get_annual_measures()
        filtered = (
            df[df["department"] == department.upper().strip()]
            .sort_values("year")
            .reset_index(drop=True)
        )

        for group in ["men5", "60mas"]:
            filtered[f"hr_{group}"] = np.where(
                filtered[f"cases_{group}"] > 0,
                (filtered[f"hosp_{group}"] / filtered[f"cases_{group}"]) * 100,
                0.0,
            ).round(2)
            filtered[f"cfr_{group}"] = np.where(
                filtered[f"death_{group}"] > 0,
                (filtered[f"death_{group}"] / filtered[f"cases_{group}"]) * 100,
                0.0,
            ).round(2)

        return filtered

    def get_rank_grid(self, group: str = "men5") -> pd.DataFrame:
        """
        Retorna la matriz de rankings anuales por departamento.
        group: 'men5' o '60mas'
        """
        prefix = "children" if group == "men5" else "older"
        path = self.outputs_tables / f"rank_grid_{prefix}_cases_rate.csv"
        if path.exists():
            return pd.read_csv(path)
        return pd.DataFrame()

    def get_top3_frequencies(self, group: str = "men5") -> pd.DataFrame:
        """
        Retorna la tabla de frecuencia en el Top 3 de mayor incidencia.
        group: 'men5' o '60mas'
        """
        prefix = "children" if group == "men5" else "older"
        path = self.outputs_tables / f"top3_frequency_{prefix}_cases_rate.csv"
        if path.exists():
            df = pd.read_csv(path)
            return df.sort_values("top3_appearances", ascending=False).reset_index(drop=True)
        return pd.DataFrame()

    def get_severity_annual_series(self, group: str = "men5") -> pd.DataFrame:
        """Retorna las tasas históricas anuales de severidad (HR y CFR) a nivel nacional."""
        group_str = "children" if group == "men5" else "adults"
        path = self.outputs_tables / f"national_{group_str}_annual_HR_CFR.csv"
        if path.exists():
            return pd.read_csv(path)

        nat = self.get_national_summary()
        cols = ["year", f"hr_{group}", f"cfr_{group}", f"cases_{group}", f"hosp_{group}", f"death_{group}"]
        return nat[cols].rename(columns={f"hr_{group}": "HR", f"cfr_{group}": "CFR"})

    def compute_kpis(
        self, df_scope: pd.DataFrame, group: str = "men5", year: Optional[int] = None
    ) -> Dict[str, float]:
        """
        Calcula KPIs clave para tarjetas informativas (Cumplimiento ISO 9241-12).
        """
        if year is None:
            year = int(df_scope["year"].max())

        row_curr = df_scope[df_scope["year"] == year]
        row_prev = df_scope[df_scope["year"] == (year - 1)]

        cases_col = f"cases_{group}"
        rate_col = f"cases_rate_{group}"
        hosp_col = f"hosp_{group}"
        death_col = f"death_{group}"

        curr_cases = float(row_curr[cases_col].sum()) if not row_curr.empty else 0.0
        curr_rate = float(row_curr[rate_col].mean()) if not row_curr.empty else 0.0
        curr_hosp = float(row_curr[hosp_col].sum()) if not row_curr.empty else 0.0
        curr_death = float(row_curr[death_col].sum()) if not row_curr.empty else 0.0

        prev_cases = float(row_prev[cases_col].sum()) if not row_prev.empty else curr_cases
        prev_rate = float(row_prev[rate_col].mean()) if not row_prev.empty else curr_rate

        delta_cases_pct = (
            ((curr_cases - prev_cases) / prev_cases * 100.0) if prev_cases > 0 else 0.0
        )
        delta_rate = curr_rate - prev_rate

        hr = (curr_hosp / curr_cases * 100.0) if curr_cases > 0 else 0.0
        cfr = (curr_death / curr_cases * 100.0) if curr_cases > 0 else 0.0

        return {
            "year": float(year),
            "cases": curr_cases,
            "cases_rate": curr_rate,
            "hospitalizations": curr_hosp,
            "deaths": curr_death,
            "delta_cases_pct": delta_cases_pct,
            "delta_rate": delta_rate,
            "hr": hr,
            "cfr": cfr,
        }
