from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns


ROOT_DIR = Path(__file__).resolve().parents[2]
INPUT_DIR = ROOT_DIR / "outputs" / "tables"
OUTPUT_DIR = ROOT_DIR / "outputs" / "figures"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

RANK_GRIDS = {
    ("Children <5", "Cases"): INPUT_DIR / "rank_grid_children_cases_rate.csv",
    ("Children <5", "Hospitalizations"): INPUT_DIR / "rank_grid_children_hosp_rate.csv",
    ("Children <5", "Deaths"): INPUT_DIR / "rank_grid_children_death_rate.csv",
    ("Adults 60+", "Cases"): INPUT_DIR / "rank_grid_older_cases_rate.csv",
    ("Adults 60+", "Hospitalizations"): INPUT_DIR / "rank_grid_older_hosp_rate.csv",
    ("Adults 60+", "Deaths"): INPUT_DIR / "rank_grid_older_death_rate.csv",
}

FIGSIZE = (24, 10)
LABEL_EVERY = 1
SAVE_FIG = True

TOPN_FOR_FREQ = 3
HEAT_CMAP = "YlOrRd_r"

sns.set_style("white")


def rank_to_category(x):
    if pd.isna(x):
        return np.nan
    x = int(x)
    return ((x - 1) // 5) + 1


def load_rank_grid_wide(path):
    df = pd.read_csv(path)
    df = df.rename(columns={df.columns[0]: "region"})
    df["region"] = df["region"].astype(str).str.strip()

    year_cols = [c for c in df.columns if c != "region"]
    df[year_cols] = df[year_cols].apply(pd.to_numeric, errors="coerce")
    return df


def compute_global_region_order(rank_grids_dict):
    all_cat = {}

    for _, path in rank_grids_dict.items():
        wide = load_rank_grid_wide(path)
        year_cols = [c for c in wide.columns if c != "region"]

        cat = wide.copy()
        cat[year_cols] = cat[year_cols].apply(lambda col: col.map(rank_to_category))
        cat["_avg"] = cat[year_cols].mean(axis=1, skipna=True)

        for r, v in zip(cat["region"], cat["_avg"]):
            all_cat.setdefault(r, []).append(v)

    avg_overall = {r: float(np.nanmean(vals)) for r, vals in all_cat.items()}
    region_order = [r for r, _ in sorted(avg_overall.items(), key=lambda x: (x[1], x[0]))]
    return region_order


def build_category_heat(df_wide, region_order):
    year_cols = [c for c in df_wide.columns if c != "region"]

    cat = df_wide.copy()
    cat[year_cols] = cat[year_cols].apply(lambda col: col.map(rank_to_category))

    cat["region"] = pd.Categorical(cat["region"], categories=region_order, ordered=True)
    cat = cat.sort_values("region")
    cat["region"] = cat["region"].astype(str)

    heat = cat.set_index("region").T
    heat.index = pd.to_numeric(heat.index, errors="coerce").astype(int)
    heat = heat.sort_index()
    return heat


def top3_frequency_from_rankgrid(df_wide, region_order, top_n=3):
    year_cols = [c for c in df_wide.columns if c != "region"]
    tmp = df_wide.copy()

    mask = tmp[year_cols].le(top_n)
    tmp["freq_top3"] = mask.sum(axis=1)

    tmp["region"] = pd.Categorical(tmp["region"], categories=region_order, ordered=True)
    tmp = tmp.sort_values("region")

    freq = pd.Series(tmp["freq_top3"].values, index=tmp["region"].astype(str).values)
    return freq


def apply_sparse_xticklabels(ax, labels, every=1, rotation=90):
    ticks = np.arange(len(labels))
    ax.set_xticks(ticks + 0.5)
    shown = [(lab if (i % every == 0) else "") for i, lab in enumerate(labels)]
    ax.set_xticklabels(shown, rotation=rotation)


def plot_heatmaps_with_top3bars_for_age(age_label, region_order):
    measures = ["Cases", "Hospitalizations", "Deaths"]

    fig, axes = plt.subplots(
        2, 3,
        figsize=FIGSIZE,
        sharex="col",
        gridspec_kw={"height_ratios": [1, 4]},
        constrained_layout=True
    )

    for j, meas in enumerate(measures):
        path = RANK_GRIDS[(age_label, meas)]
        wide = load_rank_grid_wide(path)

        ax_bar = axes[0, j]
        freq = top3_frequency_from_rankgrid(wide, region_order, top_n=TOPN_FOR_FREQ)

        x = np.arange(len(freq.index))
        ax_bar.bar(x + 0.5, freq.values, width=0.8)

        ax_bar.set_ylim(0, 24)
        ax_bar.set_yticks([0, 5, 10, 15, 20, 24])
        ax_bar.set_title(f"{age_label}: {meas} — Top {TOPN_FOR_FREQ} Frequency")
        ax_bar.set_ylabel("Count (years)")
        ax_bar.grid(True, axis="y", alpha=0.2)

        ax_bar.set_xlim(0, len(x))
        ax_bar.set_xticks([])

        ax_hm = axes[1, j]
        heat = build_category_heat(wide, region_order)

        show_cbar = (j == 2)

        hm = sns.heatmap(
            heat,
            ax=ax_hm,
            cmap=HEAT_CMAP,
            vmin=1,
            vmax=5,
            linewidths=0.15,
            linecolor="white",
            cbar=show_cbar,
            cbar_kws={
                "label": "Rank Category",
                "ticks": [1, 2, 3, 4, 5]
            } if show_cbar else None
        )

        ax_hm.set_xlabel("Region")
        ax_hm.set_ylabel("Year" if j == 0 else "")
        apply_sparse_xticklabels(ax_hm, list(heat.columns), every=LABEL_EVERY, rotation=90)
        ax_hm.tick_params(axis="y", rotation=0)

        if j in [1, 2]:
            ax_hm.set_yticks([])
            ax_hm.set_ylabel("")

        if show_cbar:
            cbar = hm.collections[0].colorbar
            cbar.set_ticklabels([
                "1 (1–5)",
                "2 (6–10)",
                "3 (11–15)",
                "4 (16–20)",
                "5 (21–25)"
            ])

    fig.suptitle(
        f"Rank Category Heatmaps + Top-{TOPN_FOR_FREQ} Frequency Bars — {age_label}",
        fontsize=14
    )

    if SAVE_FIG:
        out = OUTPUT_DIR / (
            f"heatmap_and_top{TOPN_FOR_FREQ}_bars_"
            f"{age_label.replace(' ', '_').replace('+', 'plus').replace('<', 'lt')}.png"
        )
        fig.savefig(out, dpi=300, bbox_inches="tight")
        print("Saved:", out)

    plt.show()
    plt.close(fig)


region_order = compute_global_region_order(RANK_GRIDS)

plot_heatmaps_with_top3bars_for_age("Children <5", region_order)
plot_heatmaps_with_top3bars_for_age("Adults 60+", region_order)

print("Done", OUTPUT_DIR)
