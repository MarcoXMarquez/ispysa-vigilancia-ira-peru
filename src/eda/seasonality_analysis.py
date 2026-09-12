from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from statsmodels.tsa.seasonal import STL

sns.set_style("whitegrid")


ROOT_DIR = Path(__file__).resolve().parents[2]
DATA_RAW = ROOT_DIR / "data" / "raw"
DATA_PROCESSED = ROOT_DIR / "data" / "processed"
OUTPUT_TABLES = ROOT_DIR / "outputs" / "tables"
OUTPUT_FIGURES = ROOT_DIR / "outputs" / "figures"

OUTPUT_TABLES.mkdir(parents=True, exist_ok=True)
OUTPUT_FIGURES.mkdir(parents=True, exist_ok=True)

IRA_PATH = DATA_RAW / "iras_updated.csv"
POP_PATH = DATA_PROCESSED / "deptPopulationInterpolated_2000-2023.csv"

BOXPLOT_PATH = OUTPUT_FIGURES / "boxplot_seasonality.png"
HEATMAP_PATH = OUTPUT_FIGURES / "seasonality_heatmaps.png"
STL_PATH = OUTPUT_FIGURES / "stl_decomposition.png"
EXCEL_PATH = OUTPUT_TABLES / "IRA_seasonality_incidence_tables.xlsx"


# Load data

ira = pd.read_csv(IRA_PATH)
pop = pd.read_csv(POP_PATH)

ira.columns = ira.columns.str.lower().str.strip()
pop.columns = pop.columns.str.lower().str.strip()

ira["iddpto"] = ira["iddpto"].astype(str).str.zfill(2)
ira["ano"] = ira["ano"].astype(int)
ira["semana"] = ira["semana"].astype(int)

# converting to date (year + week number + day)
ira["date"] = pd.to_datetime(
    ira["ano"].astype(str) + "-" + ira["semana"].astype(str) + "-1",
    format="%Y-%W-%w"
)

ira = ira.sort_values("date")


# Weekly series

weekly_nat = (
    ira.groupby(["date", "ano", "semana"], as_index=False)
       .agg(
           cases_men5=("neumonias_men5", "sum"),
           cases_60mas=("neumonias_60mas", "sum")
       )
)

# national annual population
annual_pop = pop.groupby("year", as_index=False)["population"].sum()

weekly_nat = weekly_nat.merge(
    annual_pop,
    left_on="ano",
    right_on="year",
    how="left"
)

# incidence calculation
weekly_nat["inc_cases_men5"] = (
    weekly_nat["cases_men5"] / weekly_nat["population"]
) * 100000

weekly_nat["inc_cases_60mas"] = (
    weekly_nat["cases_60mas"] / weekly_nat["population"]
) * 100000

# weekly -> monthly aggregation
weekly_nat["year"] = weekly_nat["date"].dt.year
weekly_nat["month"] = weekly_nat["date"].dt.month

monthly = (
    weekly_nat.groupby(["year", "month"], as_index=False)
              .agg(
                  cases_men5=("cases_men5", "sum"),
                  cases_60mas=("cases_60mas", "sum"),
                  population=("population", "first")
              )
)

# monthly incidence
monthly["inc_men5"] = (monthly["cases_men5"] / monthly["population"]) * 100000
monthly["inc_60mas"] = (monthly["cases_60mas"] / monthly["population"]) * 100000

# adults data restriction
monthly_adults = monthly[monthly["year"] >= 2006].copy()

# Print outputs

print("Sample Weekly Incidence Data")
print(
    weekly_nat[
        [
            "date",
            "cases_men5",
            "cases_60mas",
            "population",
            "inc_cases_men5",
            "inc_cases_60mas"
        ]
    ].head(10)
)

print("Monthly Incidence Values")
print(
    monthly[
        [
            "year",
            "month",
            "cases_men5",
            "cases_60mas",
            "population",
            "inc_men5",
            "inc_60mas"
        ]
    ].head(20)
)

print("Children <5 Monthly Incidence Summary (per 100k)")
child_summary = (
    monthly.groupby("month")["inc_men5"]
    .agg(["mean", "median", "std", "min", "max"])
    .round(3)
)
print(child_summary)

print("Adults 60+ Monthly Incidence Summary (per 100k)")
adult_summary = (
    monthly_adults.groupby("month")["inc_60mas"]
    .agg(["mean", "median", "std", "min", "max"])
    .round(3)
)
print(adult_summary)

# Boxplots

fig, axes = plt.subplots(1, 2, figsize=(14, 6))

sns.boxplot(
    data=monthly,
    x="month",
    y="inc_men5",
    ax=axes[0]
)
axes[0].set_title("Monthly Seasonality (Children <5)")
axes[0].set_ylabel("Incidence per 100,000")

sns.boxplot(
    data=monthly_adults,
    x="month",
    y="inc_60mas",
    ax=axes[1]
)
axes[1].set_title("Monthly Seasonality (Adults 60+)")
axes[1].set_ylabel("Incidence per 100,000")

plt.tight_layout()
plt.savefig(BOXPLOT_PATH, dpi=300)
plt.close()


# Heatmaps

heat_child = monthly.pivot(index="year", columns="month", values="inc_men5")
heat_adult = monthly_adults.pivot(index="year", columns="month", values="inc_60mas")

fig, axes = plt.subplots(1, 2, figsize=(16, 6))

sns.heatmap(heat_child, cmap="YlOrRd", ax=axes[0])
axes[0].set_title("Seasonal Heatmap (Children <5)")

sns.heatmap(heat_adult, cmap="YlOrRd", ax=axes[1])
axes[1].set_title("Seasonal Heatmap (Adults 60+)")

plt.tight_layout()
plt.savefig(HEATMAP_PATH, dpi=300)
plt.close()

# STL decomposition

weekly_nat = weekly_nat.set_index("date")

child_series = weekly_nat["inc_cases_men5"]
adult_series = weekly_nat[weekly_nat["year"] >= 2006]["inc_cases_60mas"]

stl_child = STL(child_series, period=52).fit()
stl_adult = STL(adult_series, period=52).fit()

fig, axes = plt.subplots(4, 2, figsize=(16, 10), sharex="col")

# Observed
axes[0, 0].plot(child_series)
axes[0, 0].set_title("Children <5")

axes[0, 1].plot(adult_series)
axes[0, 1].set_title("Adults 60+")

# Trend
axes[1, 0].plot(stl_child.trend)
axes[1, 0].set_ylabel("Trend")

axes[1, 1].plot(stl_adult.trend)

# Seasonal
axes[2, 0].plot(stl_child.seasonal)
axes[2, 0].set_ylabel("Seasonal")

axes[2, 1].plot(stl_adult.seasonal)

# Residual
axes[3, 0].plot(stl_child.resid)
axes[3, 0].set_ylabel("Residual")

axes[3, 1].plot(stl_adult.resid)

plt.tight_layout()
plt.savefig(STL_PATH, dpi=300)
plt.close()

weekly_nat = weekly_nat.reset_index()


# Save Excel file

with pd.ExcelWriter(EXCEL_PATH) as writer:
    weekly_nat.to_excel(writer, sheet_name="Weekly Incidence", index=False)
    monthly.to_excel(writer, sheet_name="Monthly Incidence All Years", index=False)
    monthly_adults.to_excel(writer, sheet_name="Monthly Incidence Adults", index=False)
    child_summary.to_excel(writer, sheet_name="Children Summary")
    adult_summary.to_excel(writer, sheet_name="Adults Summary")

print(f"\nExcel file saved: {EXCEL_PATH}")
print(f"Boxplot saved: {BOXPLOT_PATH}")
print(f"Heatmap saved: {HEATMAP_PATH}")
print(f"STL decomposition saved: {STL_PATH}")
