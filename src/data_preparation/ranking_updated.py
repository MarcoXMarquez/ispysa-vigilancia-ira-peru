from pathlib import Path
import pandas as pd

ROOT_DIR = Path(__file__).resolve().parents[2]
DATA_PROCESSED = ROOT_DIR / "data" / "processed"
OUTPUT_TABLES = ROOT_DIR / "outputs" / "tables"

INPUT_PATH = DATA_PROCESSED / "annual_disease_measures_dept_2000_2023.csv"
TOP_K = 3

# Year filters
CHILD_START_YEAR = 2000
OLDER_START_YEAR = 2006


def add_rank_each_year(data: pd.DataFrame, value_col: str) -> pd.DataFrame:
    """
    Rank regions within each year (1 = highest rate).
    method='min' gives tied values the same best rank.
    """
    out = data.copy()
    out["rank"] = out.groupby("year")[value_col].rank(ascending=False, method="min")
    out["rank"] = out["rank"].astype(int)
    return out


def make_rank_grid(ranked: pd.DataFrame) -> pd.DataFrame:
    grid = ranked.pivot(index="region", columns="year", values="rank")
    return grid.sort_index()


def count_topk_years(ranked: pd.DataFrame, k: int) -> pd.DataFrame:
    total_years = ranked["year"].nunique()

    freq = (
        ranked.assign(in_topk=(ranked["rank"] <= k))
              .groupby(["iddpto", "region"], as_index=False)["in_topk"]
              .sum()
              .rename(columns={"in_topk": f"top{k}_appearances"})
              .sort_values(f"top{k}_appearances", ascending=False)
    )
    freq[f"percent_years_in_top{k}"] = (freq[f"top{k}_appearances"] / total_years * 100).round(1)
    return freq


# Load
df = pd.read_csv(INPUT_PATH)
df.columns = df.columns.str.lower().str.strip()

df["iddpto"] = df["iddpto"].astype(str).str.zfill(2)
df["year"] = pd.to_numeric(df["year"], errors="coerce").fillna(0).astype(int)

# Region name
if "department" in df.columns:
    df["region"] = df["department"].astype(str).str.strip()
elif "departamento" in df.columns:
    df["region"] = df["departamento"].astype(str).str.strip()
else:
    df["region"] = df["iddpto"]

# Ranking by rates/100k
requested_measures = {
    "children_cases_rate": "cases_rate_men5",
    "children_hosp_rate": "hosp_rate_men5",
    "children_death_rate": "death_rate_men5",
    "older_cases_rate": "cases_rate_60mas",
    "older_hosp_rate": "hosp_rate_60mas",
    "older_death_rate": "death_rate_60mas",
}

# Keep only measures that exist
measures = {label: col for label, col in requested_measures.items() if col in df.columns}

print("\nMeasures that will be ranked (rates per 100k):")
for label, col in measures.items():
    print(f"  - {label}: {col}")

missing_needed = [c for c in requested_measures.values() if c not in df.columns]
if missing_needed:
    print("\nWARNING: Some expected rate columns are missing:")
    for c in missing_needed:
        print("  -", c)
    print("Fix: Run the incidence script first to create these rate columns.\n")

if not measures:
    raise ValueError("No rate columns found to rank. Run the incidence script first.")

# Make sure output folder exists
OUTPUT_TABLES.mkdir(parents=True, exist_ok=True)

# Run ranking for each measure
for label, col in measures.items():

    # choose year filter based on measure
    if label.startswith("older_"):
        df_use = df[df["year"] >= OLDER_START_YEAR].copy()
    else:
        df_use = df[df["year"] >= CHILD_START_YEAR].copy()

    small = df_use[["iddpto", "region", "year", col]].dropna().copy()

    ranked = add_rank_each_year(small, col)
    grid = make_rank_grid(ranked)
    freq = count_topk_years(ranked, TOP_K)

    grid_file = OUTPUT_TABLES / f"rank_grid_{label}.csv"
    freq_file = OUTPUT_TABLES / f"top{TOP_K}_frequency_{label}.csv"

    grid.to_csv(grid_file)
    freq.to_csv(freq_file, index=False)

    print(f"\nSaved: {grid_file}")
    print(f"Saved: {freq_file}")
    print(freq.head(5))

print("\nRanking grids and Top-K frequency files created for all rate measures.")
print(f"Adults 60+ rankings restricted to years {OLDER_START_YEAR}–2023.")
