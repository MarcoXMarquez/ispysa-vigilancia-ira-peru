from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt



# SETTINGS


ROOT_DIR = Path(__file__).resolve().parents[2]

BASELINE_DIR = ROOT_DIR / "outputs" / "children_cases_baseline_stat_updated"
ML_DIR = ROOT_DIR / "outputs" / "children_cases_ml_simulation_recursive"
LSTM_DIR = ROOT_DIR / "outputs" / "children_cases_lstm_improved"

OUTPUT_DIR = ROOT_DIR / "outputs" / "children_cases_top3_model_plots"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

REGIONS = ["HUANUCO", "LORETO", "UCAYALI"]

MODEL_COLORS = {
    "naive": "tab:blue",
    "seasonal_naive": "tab:orange",
    "holt_winters": "tab:green",
    "arima": "tab:red",
    "random_forest": "tab:purple",
    "xgboost": "tab:brown",
    "lstm": "tab:pink",
}

MODEL_LABELS = {
    "naive": "Naive",
    "seasonal_naive": "Seasonal Naive",
    "holt_winters": "Holt-Winters",
    "arima": "ARIMA",
    "random_forest": "Random Forest",
    "xgboost": "XGBoost",
    "lstm": "LSTM",
}



# HELPERS


def region_file_prefix(region):
    return region.lower()


def load_model_outputs(region):
    prefix = region_file_prefix(region)

    
    # Baseline + Statistical
    
    base_metrics = pd.read_csv(BASELINE_DIR / f"{prefix}_baseline_stat_metrics.csv")
    base_preds = pd.read_csv(BASELINE_DIR / f"{prefix}_baseline_stat_predictions.csv")
    base_future = pd.read_csv(BASELINE_DIR / f"{prefix}_baseline_stat_future_predictions.csv")

    
    # ML
    
    ml_metrics = pd.read_csv(ML_DIR / f"{prefix}_ml_metrics.csv")
    ml_preds = pd.read_csv(ML_DIR / f"{prefix}_ml_predictions.csv")
    ml_future = pd.read_csv(ML_DIR / f"{prefix}_ml_future_predictions.csv")

    # ML prediction file may not contain region column
    ml_preds["region"] = region
    ml_future["region"] = region

    
    # LSTM
    
    lstm_metrics = pd.read_csv(LSTM_DIR / f"{prefix}_lstm_metrics.csv")
    lstm_preds = pd.read_csv(LSTM_DIR / f"{prefix}_lstm_predictions.csv")
    lstm_future = pd.read_csv(LSTM_DIR / f"{prefix}_lstm_future_predictions.csv")

    
    # Combine all
    
    metrics = pd.concat(
        [base_metrics, ml_metrics, lstm_metrics],
        ignore_index=True
    )

    preds = pd.concat(
        [base_preds, ml_preds, lstm_preds],
        ignore_index=True
    )

    future = pd.concat(
        [base_future, ml_future, lstm_future],
        ignore_index=True
    )

    preds["date"] = pd.to_datetime(preds["date"])
    future["date"] = pd.to_datetime(future["date"])

    return metrics, preds, future


def get_top3_models(metrics):
    metrics = metrics.copy()

    # Higher R2 is better
    metrics = metrics.sort_values("r2", ascending=False)

    top3 = metrics.head(3)["model"].tolist()

    return top3, metrics


def plot_top3_region(region, metrics, preds, future, top3_models):
    region_preds = preds[preds["region"].str.upper() == region].copy()
    region_future = future[future["region"].str.upper() == region].copy()

    actual_df = (
        region_preds[["date", "actual"]]
        .drop_duplicates()
        .sort_values("date")
    )

    plt.figure(figsize=(14, 6))

    # Actual
    plt.plot(
        actual_df["date"],
        actual_df["actual"],
        label="Actual",
        color="black",
        linewidth=2.8
    )

    # Top 3 models
    for model in top3_models:
        model_preds = (
            region_preds[region_preds["model"] == model]
            .sort_values("date")
        )

        model_future = (
            region_future[region_future["model"] == model]
            .sort_values("date")
        )

        color = MODEL_COLORS.get(model, None)
        label = MODEL_LABELS.get(model, model)

        plt.plot(
            model_preds["date"],
            model_preds["predicted"],
            label=label,
            color=color,
            linewidth=2
        )

        if not model_future.empty:
            plt.plot(
                model_future["date"],
                model_future["predicted"],
                label=f"{label} Future",
                color=color,
                linestyle="--",
                linewidth=2
            )

    # Future divider
    last_actual_date = actual_df["date"].max()
    plt.axvline(
        last_actual_date,
        color="gray",
        linestyle=":",
        linewidth=1.5
    )

    if not region_future.empty:
        plt.xlim(actual_df["date"].min(), region_future["date"].max())

    plt.title(
        f"{region} | Children <5 Cases | Top 3 Models | "
        f"1-Month Ahead Backtest + 1-Year Future Projection"
    )
    plt.xlabel("Date")
    plt.ylabel("Incidence per 100k")
    plt.grid(alpha=0.3)
    plt.legend()
    plt.tight_layout()

    output_path = OUTPUT_DIR / f"{region.lower()}_children_cases_top3_models.png"
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()

    return output_path



# MAIN


def main():
    all_top3_rows = []

    for region in REGIONS:
        print(f"\nProcessing region: {region}")

        metrics, preds, future = load_model_outputs(region)

        top3_models, sorted_metrics = get_top3_models(metrics)

        print("Top 3 models by R2:")
        print(sorted_metrics[["region", "model", "mae", "rmse", "r2"]].head(3))

        plot_path = plot_top3_region(
            region=region,
            metrics=metrics,
            preds=preds,
            future=future,
            top3_models=top3_models
        )

        print(f"Saved plot to: {plot_path}")

        top3_table = sorted_metrics.head(3).copy()
        top3_table["selected_rank"] = range(1, len(top3_table) + 1)
        all_top3_rows.append(top3_table)

    final_top3 = pd.concat(all_top3_rows, ignore_index=True)

    final_csv = OUTPUT_DIR / "children_cases_top3_models_by_region.csv"
    final_top3.to_csv(final_csv, index=False)

    print("\nDone.")
    print(f"Saved top-3 model table to: {final_csv}")


if __name__ == "__main__":
    main()