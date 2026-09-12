from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from statsmodels.tsa.seasonal import STL

sns.set_style("whitegrid")


# PATH SETUP 


ROOT_DIR = Path(__file__).resolve().parents[2]

DATA_RAW = ROOT_DIR / "data" / "raw"
DATA_PROCESSED = ROOT_DIR / "data" / "processed"
INPUT_TABLES = ROOT_DIR / "outputs" / "tables"
OUTPUT_DIR = ROOT_DIR / "outputs" / "figures"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

IRA_PATH = DATA_RAW / "iras_updated.csv"
POP_PATH = DATA_PROCESSED / "deptPopulationInterpolated_2000-2023.csv"

# ranking output files
FILES = {
    "children_cases": INPUT_TABLES / "top3_frequency_children_cases_rate.csv",
    "children_hosp": INPUT_TABLES / "top3_frequency_children_hosp_rate.csv",
    "children_death": INPUT_TABLES / "top3_frequency_children_death_rate.csv",
    "adult_cases": INPUT_TABLES / "top3_frequency_older_cases_rate.csv",
    "adult_hosp": INPUT_TABLES / "top3_frequency_older_hosp_rate.csv",
    "adult_death": INPUT_TABLES / "top3_frequency_older_death_rate.csv"
}


# YEAR FILTERS


CHILD_START_YEAR = 2000
ADULT_START_YEAR = 2006
END_YEAR = 2023


# LOAD DATA

ira = pd.read_csv(IRA_PATH)
pop = pd.read_csv(POP_PATH)

ira.columns = ira.columns.str.lower().str.strip()
pop.columns = pop.columns.str.lower().str.strip()

ira["iddpto"] = ira["iddpto"].astype(str).str.zfill(2)

# build weekly date
ira["date"] = pd.to_datetime(
    ira["ano"].astype(str) + "-" + ira["semana"].astype(str).str.zfill(2) + "-1",
    format="%G-%V-%u",
    errors="coerce"
)

ira = ira.dropna(subset=["date"]).copy()
ira = ira.sort_values("date")

ira["year"] = ira["date"].dt.year.astype(int)
ira["month"] = ira["date"].dt.month.astype(int)

# standardize region names
ira["departamento"] = ira["departamento"].astype(str).str.strip().str.upper()
pop["department"] = pop["department"].astype(str).str.strip().str.upper()

# numeric population
pop["year"] = pd.to_numeric(pop["year"], errors="coerce").astype("Int64")
pop["population"] = pd.to_numeric(pop["population"], errors="coerce")


# READ TOP REGIONS


def load_regions(path):
    df = pd.read_csv(path)
    df.columns = df.columns.str.lower().str.strip()

    region_col = [c for c in df.columns if "depart" in c or "region" in c][0]
    regions = df[region_col].head(3).astype(str).str.strip().str.upper().tolist()

    return regions


# ANALYSIS FUNCTION


def run_analysis(region, case_column, label):

    print("Region:", region, "|", label)

    df_region = ira[ira["departamento"] == region].copy()

    # year filter
    if "Adults 60+" in label:
        df_region = df_region[
            (df_region["year"] >= ADULT_START_YEAR) &
            (df_region["year"] <= END_YEAR)
        ].copy()
    else:
        df_region = df_region[
            (df_region["year"] >= CHILD_START_YEAR) &
            (df_region["year"] <= END_YEAR)
        ].copy()

    if df_region.empty:
        print(f"No data found for {region} | {label}")
        return

    # weekly aggregation
    weekly = (
        df_region.groupby(["date", "year", "month"], as_index=False)
        .agg(cases=(case_column, "sum"))
    )

    # merge population
    region_pop = pop[pop["department"] == region].copy()

    weekly = weekly.merge(
        region_pop[["year", "population"]],
        on="year",
        how="left"
    )

    weekly = weekly.dropna(subset=["population"]).copy()

    # incidence
    weekly["incidence"] = (weekly["cases"] / weekly["population"]) * 100000

    # monthly mean
    monthly = weekly.groupby(["year", "month"], as_index=False)["incidence"].mean()

    heat = monthly.pivot(index="year", columns="month", values="incidence")

    annual = weekly.groupby("year", as_index=False)["incidence"].mean()

    # STL decomposition
    weekly = weekly.set_index("date").sort_index()
    series = weekly["incidence"].asfreq("W-MON").interpolate(limit_direction="both")

    stl = STL(series, period=52).fit()

    
    # PLOT
    

    fig = plt.figure(figsize=(18, 12))
    fig.suptitle(f"{region} — {label}", fontsize=16)

    # annual trend
    ax1 = plt.subplot(2, 2, 1)
    ax1.plot(annual["year"], annual["incidence"], marker="o")
    ax1.set_title("Annual Trend")
    ax1.set_xlabel("Year")
    ax1.set_ylabel("Incidence per 100k")
    ax1.set_xticks(annual["year"])
    ax1.tick_params(axis="x", rotation=45)
    ax1.grid(alpha=0.3)

    # monthly boxplot
    ax2 = plt.subplot(2, 2, 2)
    sns.boxplot(data=monthly, x="month", y="incidence", ax=ax2)
    ax2.set_title("Monthly Seasonality")
    ax2.set_xlabel("Month")
    ax2.set_ylabel("Incidence")
    ax2.grid(axis="y", alpha=0.3)

    # heatmap
    ax3 = plt.subplot(2, 2, 3)
    sns.heatmap(heat, cmap="YlOrRd", ax=ax3)
    ax3.set_title("Year × Month Heatmap")
    ax3.set_xlabel("Month")
    ax3.set_ylabel("Year")

    # STL
    ax4 = plt.subplot(2, 2, 4)
    ax4.plot(series.index, series.values, color="gray", alpha=0.4, label="Observed")
    ax4.plot(stl.trend.index, stl.trend.values, label="Trend")
    ax4.plot(stl.seasonal.index, stl.seasonal.values, label="Seasonal")
    ax4.set_title("STL Decomposition")
    ax4.legend()
    ax4.grid(alpha=0.3)

    plt.tight_layout()

    safe_region = region.replace(" ", "_")
    safe_label = (
        label.replace(" ", "_")
             .replace("<", "")
             .replace(">", "")
             .replace("+", "plus")
    )

    filename = f"{safe_region}_{safe_label}.png"
    save_path = OUTPUT_DIR / filename

    plt.savefig(save_path, dpi=300, bbox_inches="tight")
    print("Saved:", save_path)

    plt.show()
    plt.close()


# CHILDREN CASES


regions = load_regions(FILES["children_cases"])

for r in regions:
    run_analysis(r, "neumonias_men5", "Children <5 Cases")


# ADULT CASES


regions = load_regions(FILES["adult_cases"])

for r in regions:
    run_analysis(r, "neumonias_60mas", "Adults 60+ Cases")

print("\nTask 4 completed. Plots saved in:", OUTPUT_DIR)