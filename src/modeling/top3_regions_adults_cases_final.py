from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt



# SETTINGS


ROOT_DIR = Path(__file__).resolve().parents[2]

BASELINE_STAT_DIR = ROOT_DIR / "outputs" / "adults_cases_baseline_stat_optimized"
ML_DIR = ROOT_DIR / "outputs" / "adults_cases_ml_optimized"
LSTM_DIR = ROOT_DIR / "outputs" / "adults_cases_lstm_top3"

OUTPUT_DIR = ROOT_DIR / "outputs" / "adults_cases_top3_models_final"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

REGIONS = ["AREQUIPA", "CUSCO", "MOQUEGUA"]

MODEL_COLORS = {
    "naive": "tab:blue",
    "seasonal_naive": "tab:orange",
    "holt_winters": "tab:green",
    "arima": "tab:red",
    "random_forest": "tab:purple",
    "xgboost": "tab:brown",
    "lstm": "tab:pink",
}



# HELPERS


def read_csv_if_exists(path):
    if path.exists():
        return pd.read_csv(path)

    print(f"Missing file: {path}")
    return pd.DataFrame()


def get_region_files(region):
    prefix = region.lower()

    return {
        "baseline_metrics": BASELINE_STAT_DIR / f"{prefix}_adults_cases_baseline_stat_metrics.csv",
        "baseline_preds": BASELINE_STAT_DIR / f"{prefix}_adults_cases_baseline_stat_predictions.csv",
        "baseline_future": BASELINE_STAT_DIR / f"{prefix}_adults_cases_baseline_stat_future_predictions.csv",

        "ml_metrics": ML_DIR / f"{prefix}_adults_cases_ml_metrics.csv",
        "ml_preds": ML_DIR / f"{prefix}_adults_cases_ml_predictions.csv",
        "ml_future": ML_DIR / f"{prefix}_adults_cases_ml_future_predictions.csv",

        "lstm_metrics": LSTM_DIR / f"{prefix}_adults_cases_lstm_metrics.csv",
        "lstm_preds": LSTM_DIR / f"{prefix}_adults_cases_lstm_predictions.csv",
        "lstm_future": LSTM_DIR / f"{prefix}_adults_cases_lstm_future_predictions.csv",
    }


def load_region_data(region):
    files = get_region_files(region)

    metrics_df = pd.concat(
        [
            read_csv_if_exists(files["baseline_metrics"]),
            read_csv_if_exists(files["ml_metrics"]),
            read_csv_if_exists(files["lstm_metrics"]),
        ],
        ignore_index=True
    )

    preds_df = pd.concat(
        [
            read_csv_if_exists(files["baseline_preds"]),
            read_csv_if_exists(files["ml_preds"]),
            read_csv_if_exists(files["lstm_preds"]),
        ],
        ignore_index=True
    )

    future_df = pd.concat(
        [
            read_csv_if_exists(files["baseline_future"]),
            read_csv_if_exists(files["ml_future"]),
            read_csv_if_exists(files["lstm_future"]),
        ],
        ignore_index=True
    )

    metrics_df["region"] = metrics_df["region"].astype(str).str.upper()
    preds_df["region"] = preds_df["region"].astype(str).str.upper()
    future_df["region"] = future_df["region"].astype(str).str.upper()

    preds_df["date"] = pd.to_datetime(preds_df["date"])
    future_df["date"] = pd.to_datetime(future_df["date"])

    return metrics_df, preds_df, future_df


def pick_top3_using_all_metrics(metrics_df, region):
    temp = metrics_df[metrics_df["region"] == region].copy()

    temp["rmse_rank"] = temp["rmse"].rank(method="min", ascending=True)
    temp["mae_rank"] = temp["mae"].rank(method="min", ascending=True)
    temp["r2_rank"] = temp["r2"].rank(method="min", ascending=False)

    temp["overall_score"] = (
        temp["rmse_rank"] +
        temp["mae_rank"] +
        temp["r2_rank"]
    ) / 3

    temp = temp.sort_values(
        by=["overall_score", "rmse", "mae", "r2"],
        ascending=[True, True, True, False]
    )

    top3 = temp.head(3)

    print(f"\nTop 3 models for {region}:")
    print(
        top3[
            [
                "region",
                "model",
                "mae",
                "rmse",
                "r2",
                "rmse_rank",
                "mae_rank",
                "r2_rank",
                "overall_score",
            ]
        ]
    )

    return top3["model"].tolist(), top3


def plot_top3(region, preds_df, future_df, top3_models, output_path):
    region_preds = preds_df[preds_df["region"] == region].copy()
    region_future = future_df[future_df["region"] == region].copy()

    # use FULL actual series from predictions 
    actual_df = (
        region_preds[["date", "actual"]]
        .drop_duplicates()
        .sort_values("date")
    )

    last_actual_date = actual_df["date"].max()
    last_actual_value = actual_df["actual"].iloc[-1]

    plt.figure(figsize=(14, 6))

    plt.plot(
        actual_df["date"],
        actual_df["actual"],
        label="Actual",
        color="black",
        linewidth=2.8
    )

    for model_name in top3_models:
        pred = (
            region_preds[region_preds["model"] == model_name]
            .sort_values("date")
        )

        fut = (
            region_future[region_future["model"] == model_name]
            .sort_values("date")
        )

        color = MODEL_COLORS.get(model_name, None)

        # Backtest predictions
        plt.plot(
            pred["date"],
            pred["predicted"],
            label=model_name,
            color=color,
            linewidth=2
        )

        # connect future to last actual
        if not fut.empty:
            fut_connected = pd.concat([
                pd.DataFrame({
                    "date": [last_actual_date],
                    "predicted": [last_actual_value],
                    "model": [model_name],
                    "region": [region]
                }),
                fut
            ], ignore_index=True)

            plt.plot(
                fut_connected["date"],
                fut_connected["predicted"],
                label=f"{model_name}_future",
                color=color,
                linestyle="--",
                linewidth=2
            )

    if not region_future.empty:
        plt.xlim(actual_df["date"].min(), region_future["date"].max())

    plt.axvline(
        last_actual_date,
        color="gray",
        linestyle=":",
        linewidth=1.5
    )

    plt.title(
        f"{region} | Adults 60+ Cases | Top 3 Models Based on MAE, RMSE, and R²"
    )
    plt.xlabel("Date")
    plt.ylabel("Incidence per 100k")
    plt.grid(alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()


# MAIN


def main():
    all_top3 = []

    for region in REGIONS:
        print(f"\nProcessing {region}")

        metrics_df, preds_df, future_df = load_region_data(region)

        top3_models, top3_metrics = pick_top3_using_all_metrics(
            metrics_df=metrics_df,
            region=region
        )

        all_top3.append(top3_metrics)

        plot_path = OUTPUT_DIR / f"{region.lower()}_adults_cases_top3_models.png"

        plot_top3(
            region=region,
            preds_df=preds_df,
            future_df=future_df,
            top3_models=top3_models,
            output_path=plot_path
        )

        print(f"Saved plot: {plot_path}")

    final_top3_df = pd.concat(all_top3, ignore_index=True)

    final_top3_df.to_csv(
        OUTPUT_DIR / "adults_cases_top3_models_selected_by_all_metrics.csv",
        index=False
    )

    print("\nDone.")
    print(f"Saved outputs to: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()