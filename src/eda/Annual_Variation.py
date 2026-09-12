from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

ROOT_DIR = Path(__file__).resolve().parents[2]
DATA_PROCESSED = ROOT_DIR / "data" / "processed"
OUTPUT_TABLES = ROOT_DIR / "outputs" / "tables"
OUTPUT_FIGURES = ROOT_DIR / "outputs" / "figures"

DATA_PATH = DATA_PROCESSED / "annual_disease_measures_dept_2000_2023.csv"
OUT_PATH = OUTPUT_TABLES / "national_annual_variation_rates.csv"
OUTPUT_FIG = OUTPUT_FIGURES / "national_annual_variation_grid.png"

END_YEAR = None


def rate_per_100k(count, pop):
    return (count / pop) * 100000


def build_national_table(df):
    nat = (
        df.groupby("year", as_index=False)[
            [
                "population",
                "cases_men5", "cases_60mas",
                "hosp_men5", "hosp_60mas",
                "death_men5", "death_60mas"
            ]
        ]
        .sum()
        .sort_values("year")
        .reset_index(drop=True)
    )

    nat["cases_rate_men5"] = rate_per_100k(nat["cases_men5"], nat["population"])
    nat["hosp_rate_men5"] = rate_per_100k(nat["hosp_men5"], nat["population"])
    nat["death_rate_men5"] = rate_per_100k(nat["death_men5"], nat["population"])

    nat["cases_rate_60mas"] = rate_per_100k(nat["cases_60mas"], nat["population"])
    nat["hosp_rate_60mas"] = rate_per_100k(nat["hosp_60mas"], nat["population"])
    nat["death_rate_60mas"] = rate_per_100k(nat["death_60mas"], nat["population"])

    return nat


def plot_annual_variation_grid(nat):
    years = nat["year"].astype(int).tolist()

    colors = {
        "cases_child": "#8ecae6",
        "cases_old": "#1d4ed8",
        "hosp_child": "#ffd166",
        "hosp_old": "#f59e0b",
        "death_child": "#95d5b2",
        "death_old": "#2d6a4f",
    }

    markers = {"cases": "^", "hosp": "s", "death": "*"}

    max_cases_hosp = max(
        nat["cases_rate_men5"].max(), nat["hosp_rate_men5"].max(),
        nat["cases_rate_60mas"].max(), nat["hosp_rate_60mas"].max()
    )
    max_deaths = max(nat["death_rate_men5"].max(), nat["death_rate_60mas"].max())

    y_cases_hosp = (0, max_cases_hosp * 1.10 if max_cases_hosp > 0 else 1)
    y_deaths = (0, max_deaths * 1.15 if max_deaths > 0 else 1)

    fig, axes = plt.subplots(2, 2, figsize=(16, 9), sharex=True, constrained_layout=True)

    def add_combined_legend(ax, ax_r):
        h1, l1 = ax.get_legend_handles_labels()
        h2, l2 = ax_r.get_legend_handles_labels()
        ax.legend(h1 + h2, l1 + l2, loc="upper left")

    # Children: Cases vs Hosp
    ax = axes[0, 0]
    ax_r = ax.twinx()
    ax.plot(
        years, nat["cases_rate_men5"],
        color=colors["cases_child"], marker=markers["cases"], linewidth=2,
        label="Cases /100k"
    )
    ax_r.plot(
        years, nat["hosp_rate_men5"],
        color=colors["hosp_child"], marker=markers["hosp"], linewidth=2,
        label="Hospitalizations /100k"
    )
    ax.set_title("Children <5: Cases vs Hospitalizations")
    ax.set_ylabel("Cases rate per 100k", labelpad=10)
    ax_r.set_ylabel("Hospitalizations rate per 100k", labelpad=12)
    ax.set_ylim(*y_cases_hosp)
    ax_r.set_ylim(*y_cases_hosp)
    ax.grid(True, alpha=0.3)
    add_combined_legend(ax, ax_r)

    # Children: Cases vs Deaths
    ax = axes[0, 1]
    ax_r = ax.twinx()
    ax.plot(
        years, nat["cases_rate_men5"],
        color=colors["cases_child"], marker=markers["cases"], linewidth=2,
        label="Cases /100k"
    )
    ax_r.plot(
        years, nat["death_rate_men5"],
        color=colors["death_child"], marker=markers["death"], linewidth=2,
        label="Deaths /100k"
    )
    ax.set_title("Children <5: Cases vs Deaths")
    ax.set_ylabel("Cases rate per 100k", labelpad=10)
    ax_r.set_ylabel("Deaths rate per 100k", labelpad=12)
    ax.set_ylim(*y_cases_hosp)
    ax_r.set_ylim(*y_deaths)
    ax.grid(True, alpha=0.3)
    add_combined_legend(ax, ax_r)

    # Older: Cases vs Hosp
    ax = axes[1, 0]
    ax_r = ax.twinx()
    ax.plot(
        years, nat["cases_rate_60mas"],
        color=colors["cases_old"], marker=markers["cases"], linewidth=2,
        label="Cases /100k"
    )
    ax_r.plot(
        years, nat["hosp_rate_60mas"],
        color=colors["hosp_old"], marker=markers["hosp"], linewidth=2,
        label="Hospitalizations /100k"
    )
    ax.set_title("Adults 60+: Cases vs Hospitalizations")
    ax.set_ylabel("Cases rate per 100k", labelpad=10)
    ax_r.set_ylabel("Hospitalizations rate per 100k", labelpad=12)
    ax.set_ylim(*y_cases_hosp)
    ax_r.set_ylim(*y_cases_hosp)
    ax.grid(True, alpha=0.3)
    add_combined_legend(ax, ax_r)

    # Older: Cases vs Deaths
    ax = axes[1, 1]
    ax_r = ax.twinx()
    ax.plot(
        years, nat["cases_rate_60mas"],
        color=colors["cases_old"], marker=markers["cases"], linewidth=2,
        label="Cases /100k"
    )
    ax_r.plot(
        years, nat["death_rate_60mas"],
        color=colors["death_old"], marker=markers["death"], linewidth=2,
        label="Deaths /100k"
    )
    ax.set_title("Adults 60+: Cases vs Deaths")
    ax.set_ylabel("Cases rate per 100k", labelpad=10)
    ax_r.set_ylabel("Deaths rate per 100k", labelpad=12)
    ax.set_ylim(*y_cases_hosp)
    ax_r.set_ylim(*y_deaths)
    ax.grid(True, alpha=0.3)
    add_combined_legend(ax, ax_r)

    for r in range(2):
        for c in range(2):
            axes[r, c].set_xticks(years)
            axes[r, c].tick_params(axis="x", rotation=45)

    axes[1, 0].set_xlabel("Year")
    axes[1, 1].set_xlabel("Year")

    plt.suptitle("National Annual Variation (Rates per 100k): Children <5 vs Adults 60+")

    OUTPUT_FIG.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUTPUT_FIG, dpi=300, bbox_inches="tight")
    plt.show()


# Load
df = pd.read_csv(DATA_PATH)
df.columns = [c.strip().lower() for c in df.columns]

#  counts + population
needed = [
    "year", "population",
    "cases_men5", "cases_60mas",
    "hosp_men5", "hosp_60mas",
    "death_men5", "death_60mas"
]

missing = [c for c in needed if c not in df.columns]
if missing:
    raise ValueError(f"Missing columns: {missing}\nAvailable: {list(df.columns)}")

for c in needed:
    df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)

df["year"] = df["year"].astype(int)

if END_YEAR is not None:
    df = df[df["year"] <= END_YEAR].copy()

# Build + Save + Plot
nat = build_national_table(df)

OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
nat.to_csv(OUT_PATH, index=False)

print("Saved national table:", OUT_PATH)
print("Saved figure:", OUTPUT_FIG)
print(nat.head())

plot_annual_variation_grid(nat)
