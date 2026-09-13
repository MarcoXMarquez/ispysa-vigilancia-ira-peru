"""Acceso a resultados predictivos con validación y procedencia explícita."""

from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

from src.services.quality import (
    ArtifactReader, ValidationError, dates_column, numeric_columns,
    require_columns, text_columns, unique_rows,
)


def validate_metrics(df):
    require_columns(df, ["model", "mae", "rmse", "r2"])
    text_columns(df, ["model"])
    unique_rows(df, ["model"])
    numeric_columns(df, ["mae", "rmse"])
    numeric_columns(df, ["r2"], nonnegative=False)
    if (df["r2"] > 1).any():
        raise ValidationError("R² no puede superar 1.")


def validate_predictions(df, historical=False):
    required = ["date", "model", "predicted"] + (["actual"] if historical else [])
    require_columns(df, required)
    text_columns(df, ["model"])
    dates_column(df)
    unique_rows(df, ["model", "date"])
    numeric_columns(df, ["predicted"] + (["actual"] if historical else []))
    if not historical:
        for _, predictions in df.groupby("model"):
            dates = predictions["date"].sort_values()
            if len(dates) != 52 or not dates.diff().dropna().eq(pd.Timedelta(days=7)).all():
                raise ValidationError("Cada modelo debe contener 52 pronósticos semanales consecutivos.")
    bounds = ["lower_ci", "upper_ci"]
    if any(column in df for column in bounds):
        require_columns(df, bounds)
        numeric_columns(df, bounds)
        if ((df["lower_ci"] > df["predicted"]) | (df["upper_ci"] < df["predicted"])).any():
            raise ValidationError("Las bandas deben contener el pronóstico y estar ordenadas.")


def validate_importance(df):
    require_columns(df, ["feature", "importance"])
    text_columns(df, ["feature"])
    unique_rows(df, ["feature"])
    numeric_columns(df, ["importance"])
    if df["importance"].sum() <= 0:
        raise ValidationError("La suma de importancias debe ser positiva.")


def validate_weekly(df):
    require_columns(df, ["date"])
    dates_column(df)
    unique_rows(df, ["date"])


class EpidemiologyModelService:
    def __init__(self, root_dir: Optional[Path] = None):
        self.root_dir = Path(root_dir) if root_dir is not None else Path(__file__).resolve().parents[2]
        self.outputs_dir = self.root_dir / "outputs"
        self.reader = ArtifactReader(self.root_dir)

    @staticmethod
    def _folder(group):
        if group not in ("men5", "60mas"):
            raise ValueError("Grupo poblacional desconocido.")
        return "national_children_cases_ml" if group == "men5" else "national_adults_cases_ml"

    def get_national_metrics(self, group="men5"):
        folder = self._folder(group)
        path = self.outputs_dir / folder / f"{folder}_metrics.csv"
        df = self.reader.read(path, validate_metrics, "Métricas finitas, modelos únicos y errores no negativos")
        if not df.empty:
            df["model_display"] = df["model"].replace({
                "random_forest": "Random Forest", "xgboost": "XGBoost", "lstm": "LSTM",
                "arima": "ARIMA", "naive": "Naïve Baseline",
            })
        return df

    def get_national_weekly_series(self, group="men5"):
        folder = self._folder(group)
        path = self.outputs_dir / folder / f"{folder.replace('_ml', '')}_weekly_series.csv"
        return self.reader.read(path, validate_weekly, "Fechas semanales válidas y únicas")

    def get_national_predictions(self, group="men5"):
        folder = self._folder(group)
        path = self.outputs_dir / folder / f"{folder}_predictions.csv"
        return self.reader.read(path, lambda df: validate_predictions(df, historical=True),
                                "Valores históricos y pronósticos válidos, sin fechas duplicadas por modelo")

    def get_national_future_predictions(self, group="men5"):
        folder = self._folder(group)
        path = self.outputs_dir / folder / f"{folder}_future_predictions.csv"
        df = self.reader.read(path, validate_predictions, "52 semanas consecutivas por modelo; valores y bandas válidos")
        if df.empty:
            return df
        if "lower_ci" in df:
            df.attrs["band_method"] = "Bandas incluidas en el archivo; metodología externa no documentada."
            return df

        metrics = self.get_national_metrics(group)
        # Sin RMSE medido se conserva la predicción puntual, pero no se inventa una banda.
        rmse = df["model"].map(metrics.set_index("model")["rmse"]) if not metrics.empty else pd.Series(
            np.nan, index=df.index, dtype=float,
        )
        df["lower_ci"] = (df["predicted"] - 1.96 * rmse).clip(lower=0)
        df["upper_ci"] = df["predicted"] + 1.96 * rmse
        df.attrs["band_method"] = "Bandas aproximadas: pronóstico ± 1.96 × RMSE; límite inferior en cero."
        df.attrs["missing_band_models"] = sorted(df.loc[rmse.isna(), "model"].unique().tolist())
        source = df.attrs["source"]
        self.reader.evidence[source]["transformacion"] = df.attrs["band_method"]
        self.reader.evidence[source]["dependencias"] = [f"outputs/{folder}/{folder}_metrics.csv"]
        self.reader.evidence[source]["modelos_sin_banda"] = df.attrs["missing_band_models"]
        return df

    def get_feature_importance_sources(self, group="men5"):
        self._folder(group)  # validar el grupo antes de construir la ruta
        folder = "children_feature_importance_ci" if group == "men5" else "adults_feature_importance_ci"
        return sorted(path.name for path in (self.outputs_dir / folder).glob("*_feature_importance.csv"))

    def get_feature_importance_summary(self, group="men5", source=None):
        sources = self.get_feature_importance_sources(group)
        if source is not None and source not in sources:
            raise ValueError("Selecciona uno de los archivos de importancia disponibles.")
        folder = "children_feature_importance_ci" if group == "men5" else "adults_feature_importance_ci"
        name = source or (sources[0] if sources else "feature_importance.csv")
        path = self.outputs_dir / folder / name
        df = self.reader.read(path, validate_importance, "Variables únicas e importancias finitas no negativas")
        if not df.empty:
            df = df.sort_values("importance", ascending=False).reset_index(drop=True)
        return df
