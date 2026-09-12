from pathlib import Path
import pandas as pd
import numpy as np

ROOT_DIR = Path(__file__).resolve().parents[2]
DATA_RAW = ROOT_DIR / "data" / "raw"
DATA_PROCESSED = ROOT_DIR / "data" / "processed"

file_path = DATA_PROCESSED / "dept_updated_census.xlsx"
df = pd.read_excel(file_path)

# identifying year columns
year_columns = [col for col in df.columns if str(col).isdigit()]

# ensuring the year columns are numeric
df[year_columns] = df[year_columns].apply(pd.to_numeric, errors='coerce')

# reshaping the dataset
df_long = df.melt(
    id_vars=["UBIGEO", "Department", "iddpto"],
    value_vars=year_columns,
    var_name="Year",
    value_name="Population"
)

df_long["Year"] = df_long["Year"].astype(int)

# full year grid from 1993-2023 so every department has every year
full_years = range(1993, 2024)

departments_info = df_long[["Department", "UBIGEO", "iddpto"]].drop_duplicates()

full_grid = pd.MultiIndex.from_product(
    [departments_info["Department"], full_years],
    names=["Department", "Year"]
).to_frame(index=False)

# merging ubigeo and iddpto
full_grid = full_grid.merge(departments_info, on="Department", how="left")

# merging population values
df_full = full_grid.merge(
    df_long[["Department", "Year", "Population"]],
    on=["Department", "Year"],
    how="left"
)

# interpolation
df_full = df_full.sort_values(["Department", "Year"])

df_full["Population"] = (
    df_full.groupby("Department")["Population"]
    .transform(lambda x: x.interpolate(method="linear"))
)

# keeping only 2000-2023 data
df_final = df_full[
    (df_full["Year"] >= 2000) &
    (df_full["Year"] <= 2023)
].copy()

df_final["Population"] = df_final["Population"].round(0)

# final columns to be printed
df_final = df_final[["UBIGEO", "iddpto", "Department", "Year", "Population"]]

print("Year range:", df_final["Year"].min(), "-", df_final["Year"].max())
print("Departments:", df_final["Department"].nunique())
print("Missing population values:", df_final["Population"].isna().sum())
print(df_final.groupby("Department")["Year"].count().unique())

# Save
output_path = DATA_PROCESSED / "deptPopulationInterpolated_2000_2023.csv"
output_path.parent.mkdir(parents=True, exist_ok=True)
df_final.to_csv(output_path, index=False)

print(f"Interpolation complete and saved to: {output_path}")
