from pathlib import Path
import pandas as pd
import numpy as np

ROOT_DIR = Path(__file__).resolve().parents[2]

POP_PATH = ROOT_DIR / "data" / "processed" / "deptPopulationInterpolated_2000_2023.csv"
IRA_PATH = ROOT_DIR / "data" / "raw" / "iras_updated.csv"
OUT_PATH = ROOT_DIR / "outputs" / "tables" / "annual_disease_measures_dept_2000_2023.csv"

RATE_SCALE = 100000

def safe_rate(numer, denom, scale=RATE_SCALE):
    """Compute rate = numer/denom*scale """
    denom = denom.replace(0, np.nan)
    return (numer / denom) * scale

#loading data
pop = pd.read_csv(POP_PATH)
ira = pd.read_csv(IRA_PATH)

pop.columns = pop.columns.str.lower().str.strip()
ira.columns = ira.columns.str.lower().str.strip()

pop["iddpto"] = pop["iddpto"].astype(str).str.zfill(2)
ira["iddpto"] = ira["iddpto"].astype(str).str.zfill(2)

#"ano" is year
ira["ano"] = pd.to_numeric(ira["ano"], errors="coerce").astype("Int64")

#aggregatating weekly -> annual totals per department
annual = (
    ira.groupby(["iddpto", "ano"], as_index=False)
       .agg(
           #cases
           cases_men5=("neumonias_men5", "sum"),
           cases_60mas=("neumonias_60mas", "sum"),

           #hospitalizations
           hosp_men5=("hospitalizados_men5", "sum"),
           hosp_60mas=("hospitalizados_60mas", "sum"),

           #deaths
           death_men5=("defunciones_men5", "sum"),
           death_60mas=("defunciones_60mas", "sum"),
       )
       .rename(columns={"ano": "year"})
)

annual["year"] = annual["year"].astype(int)

#merging annual totals with population
df = annual.merge(
    pop[["iddpto", "year", "department", "ubigeo", "population"]],
    on=["iddpto", "year"],
    how="inner"
)

#computing rates per 100k
df["cases_rate_men5"] = safe_rate(df["cases_men5"], df["population"]).round(2)
df["cases_rate_60mas"] = safe_rate(df["cases_60mas"], df["population"]).round(2)

df["hosp_rate_men5"] = safe_rate(df["hosp_men5"], df["population"]).round(2)
df["hosp_rate_60mas"] = safe_rate(df["hosp_60mas"], df["population"]).round(2)

df["death_rate_men5"] = safe_rate(df["death_men5"], df["population"]).round(2)
df["death_rate_60mas"] = safe_rate(df["death_60mas"], df["population"]).round(2)

df["inc_rate_men5"] = df["cases_rate_men5"]
df["inc_rate_60mas"] = df["cases_rate_60mas"]

#reordering columns
df = df[[
    "department", "year", "ubigeo", "iddpto", "population",

    #counts
    "cases_men5", "cases_60mas",
    "hosp_men5", "hosp_60mas",
    "death_men5", "death_60mas",

    #rates per 100k
    "cases_rate_men5", "cases_rate_60mas",
    "hosp_rate_men5", "hosp_rate_60mas",
    "death_rate_men5", "death_rate_60mas",

    "inc_rate_men5", "inc_rate_60mas",
]]

#checking
print("Years:", df["year"].min(), "-", df["year"].max())
print("Departments:", df["iddpto"].nunique())
print("Missing population:", df["population"].isna().sum())
print("Any population <= 0:", (df["population"] <= 0).sum())

#saving outputs
df.to_csv(OUT_PATH, index=False)
print("Saved:", OUT_PATH)
print(df.head())
