"""Lectura verificable de CSV y contratos de datos de la aplicación."""

from datetime import datetime, timezone
from hashlib import sha256
from io import BytesIO
from pathlib import Path

import numpy as np
import pandas as pd


class ValidationError(ValueError):
    """El archivo existe, pero incumple un contrato de datos."""


def require_columns(df, columns):
    missing = sorted(set(columns) - set(df.columns))
    if missing:
        raise ValidationError("Faltan columnas: " + ", ".join(missing))
    if df.empty:
        raise ValidationError("El archivo no contiene registros.")


def numeric_columns(df, columns, nonnegative=True, integer=False):
    for column in columns:
        values = pd.to_numeric(df[column], errors="coerce")
        invalid = ~np.isfinite(values)
        if nonnegative:
            invalid |= values < 0
        if integer:
            invalid |= values % 1 != 0
        if invalid.any():
            raise ValidationError(f"{column}: {int(invalid.sum())} valores ausentes o inválidos.")
        df[column] = values


def unique_rows(df, columns):
    if df.duplicated(columns).any():
        raise ValidationError("Registros duplicados por " + "/".join(columns) + ".")


def text_columns(df, columns):
    for column in columns:
        text = df[column].astype("string").str.strip()
        if (text.isna() | text.eq("")).any():
            raise ValidationError(f"{column}: identificadores ausentes.")
        df[column] = text


def dates_column(df):
    dates = pd.to_datetime(df["date"], errors="coerce")
    if dates.isna().any():
        raise ValidationError("Hay fechas ausentes o inválidas.")
    df["date"] = dates


def validate_annual(df):
    counts = [f"{kind}_{group}" for group in ("men5", "60mas") for kind in ("cases", "hosp", "death")]
    rates = [f"{kind}_rate_{group}" for group in ("men5", "60mas") for kind in ("cases", "hosp", "death")]
    require_columns(df, ["department", "iddpto", "year", "population"] + counts + rates)
    text_columns(df, ["department"])
    df["department"] = df["department"].str.upper()
    numeric_columns(df, ["iddpto", "year"] + counts, integer=True)
    numeric_columns(df, ["population"] + rates)
    if (df["population"] <= 0).any():
        raise ValidationError("La población debe ser mayor que cero.")
    if not df["year"].between(2000, 2023).all():
        raise ValidationError("El año queda fuera del período histórico 2000–2023 de esta aplicación.")
    if not df["iddpto"].between(1, 25).all():
        raise ValidationError("Código de departamento fuera del catálogo 01–25.")
    unique_rows(df, ["department", "year"])
    unique_rows(df, ["iddpto", "year"])
    if (df.groupby("iddpto")["department"].nunique() > 1).any():
        raise ValidationError("Un código de departamento tiene varios nombres.")
    if (df.groupby("department")["iddpto"].nunique() > 1).any():
        raise ValidationError("Un departamento tiene varios códigos.")
    # El consolidado nacional no debe presentar una suma parcial como total del país.
    if not df.groupby("year")["iddpto"].nunique().eq(25).all():
        raise ValidationError("Cada año debe contener los 25 departamentos para calcular el consolidado nacional.")
    for group in ("men5", "60mas"):
        if ((df[f"cases_{group}"] == 0) &
                ((df[f"hosp_{group}"] > 0) | (df[f"death_{group}"] > 0))).any():
            raise ValidationError(f"{group}: hay hospitalizaciones o defunciones con cero casos.")
        for kind in ("cases", "hosp", "death"):
            expected = df[f"{kind}_{group}"] / df["population"] * 100000
            if not np.isclose(df[f"{kind}_rate_{group}"], expected, atol=0.011, rtol=0).all():
                raise ValidationError(f"{kind}_rate_{group}: tasas inconsistentes con casos y población.")
    df["iddpto"] = df["iddpto"].astype(int).astype(str).str.zfill(2)
    df["year"] = df["year"].astype(int)


def validate_rank_grid(df):
    require_columns(df, ["region"])
    text_columns(df, ["region"])
    unique_rows(df, ["region"])
    years = [column for column in df if str(column).isdigit()]
    if not years:
        raise ValidationError("El ranking no tiene columnas de años.")
    numeric_columns(df, years, integer=True)
    if not df[years].ge(1).all().all() or not df[years].le(25).all().all():
        raise ValidationError("Los puestos del ranking deben estar entre 1 y 25.")


class ArtifactReader:
    """Conserva evidencia de los bytes usados, sin sustituir archivos fallidos."""

    def __init__(self, root):
        self.root = Path(root)
        self.evidence = {}
        self._frames = {}

    def read(self, path, validator, contract):
        path = Path(path)
        relative = path.relative_to(self.root).as_posix()
        # Cada ejecución de la app utiliza una sola versión de cada archivo.
        if relative in self._frames:
            return self._frames[relative].copy()
        record = {
            "archivo": relative,
            "estado": "No disponible",
            "contrato": contract,
            "detalle": "",
            "sha256": None,
            "filas": 0,
            "leido_utc": datetime.now(timezone.utc).isoformat(),
            "generado_utc": None,
        }
        try:
            contents = path.read_bytes()
            record["sha256"] = sha256(contents).hexdigest()
            record["bytes"] = len(contents)
            df = pd.read_csv(BytesIO(contents))
            validator(df)
            record.update(estado="Verificado", filas=len(df), detalle="Contrato de datos satisfecho.")
            if "year" in df:
                record["periodo"] = [int(df["year"].min()), int(df["year"].max())]
            elif "date" in df:
                record["periodo"] = [str(df["date"].min()), str(df["date"].max())]
            df.attrs["source"] = relative
        except FileNotFoundError:
            record["detalle"] = "No se encontró el archivo; no se generan valores de reemplazo."
            df = pd.DataFrame()
        except (OSError, UnicodeError, pd.errors.ParserError, pd.errors.EmptyDataError, ValueError) as error:
            record.update(estado="No válido", detalle=str(error))
            df = pd.DataFrame()
        self.evidence[relative] = record
        self._frames[relative] = df.copy()
        return df
