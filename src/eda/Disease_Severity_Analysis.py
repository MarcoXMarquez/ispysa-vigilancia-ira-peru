from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates


# PATH SETUP (repo-relative)

ROOT_DIR = Path(__file__).resolve().parents[2]

DATA_RAW = ROOT_DIR / "data" / "raw"
OUTPUT_TABLES = ROOT_DIR / "outputs" / "tables"
OUTPUT_FIGURES = ROOT_DIR / "outputs" / "figures"

OUTPUT_TABLES.mkdir(parents=True, exist_ok=True)
OUTPUT_FIGURES.mkdir(parents=True, exist_ok=True)

WEEKLY_PATH = DATA_RAW / "iras_updated.csv"


# CONFIG

CHILD_START_YEAR = 2000
ADULT_START_YEAR = 2006
END_YEAR = 2019

ROLL_WEEKS = 8
MIN_CASES_FOR_RATIO = 1
SAVE_FIGS = True


# HELPERS

def standardize_cols(df):
    df = df.copy()
    df.columns = [c.strip().lower() for c in df.columns]
    return df


def build_date_from_year_week(df):
    df = df.copy()

    df["ano"] = pd.to_numeric(df["ano"], errors="coerce").astype("Int64")
    df["semana"] = pd.to_numeric(df["semana"], errors="coerce").astype("Int64")

    df["date"] = pd.to_datetime(
        df["ano"].astype(str) + "-" + df["semana"].astype(str).str.zfill(2) + "-1",
        format="%G-%V-%u",
        errors="coerce"
    )

    df = df.dropna(subset=["date"]).copy()
    df["year"] = df["date"].dt.year.astype(int)
    return df


def to_numeric_safe(df, cols):
    df = df.copy()
    for c in cols:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)
    return df


def compute_hr_cfr(df, cases_col, hosp_col, death_col):
    out = df.copy()
    cases = out[cases_col].astype(float)

    out["HR"] = np.where(cases >= MIN_CASES_FOR_RATIO, out[hosp_col] / cases, np.nan)
    out["CFR"] = np.where(cases >= MIN_CASES_FOR_RATIO, out[death_col] / cases, np.nan)

    return out


def rolling_mean(s, window):
    return s.rolling(window=window, min_periods=1).mean()


def savefig(fig, filename):
    if SAVE_FIGS:
        path = OUTPUT_FIGURES / filename
        fig.savefig(path, dpi=300, bbox_inches="tight")
        print("Saved:", path)


def build_national_weekly(df, cols):
    return (
        df.groupby(["date", "year"], as_index=False)[cols]
        .sum()
        .sort_values("date")
    )


# PLOTTING

def plot_group_1x3(df_weekly, annual, group_title, out_name):

    fig, axes = plt.subplots(1, 3, figsize=(22, 6), constrained_layout=True)

    # HR
    ax = axes[0]
    ax.plot(
        df_weekly["date"],
        df_weekly["HR"],
        linewidth=1,
        alpha=0.5,
        label="HR (weekly)"
    )
    ax.plot(
        df_weekly["date"],
        df_weekly["HR_roll"],
        linewidth=2,
        label=f"HR_roll ({ROLL_WEEKS}-week mean)"
    )
    ax.set_title(f"{group_title}: Weekly Hospitalization Rate")
    ax.set_xlabel("Year")
    ax.set_ylabel("HR")
    ax.grid(alpha=0.3)
    ax.legend()
    ax.xaxis.set_major_locator(mdates.YearLocator(1))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.tick_params(axis="x", rotation=45)

    # CFR
    ax = axes[1]
    ax.plot(
        df_weekly["date"],
        df_weekly["CFR"],
        linewidth=1,
        alpha=0.5,
        label="CFR (weekly)"
    )
    ax.plot(
        df_weekly["date"],
        df_weekly["CFR_roll"],
        linewidth=2,
        label=f"CFR_roll ({ROLL_WEEKS}-week mean)"
    )
    ax.set_title(f"{group_title}: Weekly Case Fatality Ratio")
    ax.set_xlabel("Year")
    ax.set_ylabel("CFR")
    ax.grid(alpha=0.3)
    ax.legend()
    ax.xaxis.set_major_locator(mdates.YearLocator(1))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.tick_params(axis="x", rotation=45)

    # Annual correlation
    ax = axes[2]
    ax.scatter(annual["HR"], annual["CFR"], s=45)

    for _, r in annual.iterrows():
        ax.text(r["HR"], r["CFR"], str(int(r["year"])), fontsize=8)

    corr = annual["HR"].corr(annual["CFR"])

    ax.set_title(f"{group_title}: HR vs CFR (annual averages)")
    ax.set_xlabel("Hospitalization Rate (HR)")
    ax.set_ylabel("Case Fatality Ratio (CFR)")
    ax.grid(alpha=0.3)

    ax.text(
        0.05, 0.95,
        f"Correlation (r) = {corr:.3f}",
        transform=ax.transAxes,
        fontsize=10,
        verticalalignment="top",
        bbox=dict(boxstyle="round", facecolor="white", alpha=0.7)
    )

    fig.suptitle(f"Disease Severity Analysis {group_title} (through {END_YEAR})")

    savefig(fig, out_name)

    plt.show()
    plt.close(fig)

# MAIN

def main():

    df = pd.read_csv(WEEKLY_PATH)
    df = standardize_cols(df)
    df = build_date_from_year_week(df)

    child_cases = "neumonias_men5"
    child_hosp = "hospitalizados_men5"
    child_death = "defunciones_men5"

    adult_cases = "neumonias_60mas"
    adult_hosp = "hospitalizados_60mas"
    adult_death = "defunciones_60mas"

    needed = [
        child_cases, child_hosp, child_death,
        adult_cases, adult_hosp, adult_death
    ]

    df = to_numeric_safe(df, needed)

    nat = build_national_weekly(df, needed)

    # CHILDREN
    nat_child = nat[(nat["year"] >= CHILD_START_YEAR) & (nat["year"] <= END_YEAR)].copy()
    nat_child = compute_hr_cfr(nat_child, child_cases, child_hosp, child_death)

    nat_child["HR_roll"] = rolling_mean(nat_child["HR"], ROLL_WEEKS)
    nat_child["CFR_roll"] = rolling_mean(nat_child["CFR"], ROLL_WEEKS)

    annual_child = nat_child.groupby("year", as_index=False)[["HR", "CFR"]].mean()

    nat_child.to_csv(OUTPUT_TABLES / "national_children_weekly_HR_CFR.csv", index=False)
    annual_child.to_csv(OUTPUT_TABLES / "national_children_annual_HR_CFR.csv", index=False)

    plot_group_1x3(
        nat_child,
        annual_child,
        "National Children <5",
        "national_children_severity.png"
    )

    # ADULTS
    nat_adult = nat[(nat["year"] >= ADULT_START_YEAR) & (nat["year"] <= END_YEAR)].copy()
    nat_adult = compute_hr_cfr(nat_adult, adult_cases, adult_hosp, adult_death)

    nat_adult["HR_roll"] = rolling_mean(nat_adult["HR"], ROLL_WEEKS)
    nat_adult["CFR_roll"] = rolling_mean(nat_adult["CFR"], ROLL_WEEKS)

    annual_adult = nat_adult.groupby("year", as_index=False)[["HR", "CFR"]].mean()

    nat_adult.to_csv(OUTPUT_TABLES / "national_adults_weekly_HR_CFR.csv", index=False)
    annual_adult.to_csv(OUTPUT_TABLES / "national_adults_annual_HR_CFR.csv", index=False)

    plot_group_1x3(
        nat_adult,
        annual_adult,
        "National Adults 60+",
        "national_adults_severity.png"
    )

    print("\nTask 5 complete. Outputs saved.")


if __name__ == "__main__":
    main()
