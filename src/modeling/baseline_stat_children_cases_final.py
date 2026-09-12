from pathlib import Path
import warnings
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from statsmodels.tsa.arima.model import ARIMA

warnings.filterwarnings("ignore")



# SETTINGS


ROOT_DIR = Path(__file__).resolve().parents[2]

IRA_PATH = ROOT_DIR / "data" / "raw" / "iras_updated.csv"
POP_PATH = ROOT_DIR / "data" / "processed" / "deptPopulationInterpolated_2000-2023.csv"
OUTPUT_DIR = ROOT_DIR / "outputs" / "children_cases_baseline_stat_updated"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

REGION = "UCAYALI"
TARGET_COL = "neumonias_men5"

START_YEAR = 2000
END_YEAR = 2023

SMOOTH_WINDOW = 3

TRAIN_WINDOW_WEEKS = 5 * 52
FORECAST_HORIZON = 4
STEP_WEEKS = 4
SEASONAL_PERIOD = 52

FUTURE_WEEKS = 52
FUTURE_BLOCKS = FUTURE_WEEKS // FORECAST_HORIZON

MODEL_COLORS = {
    "actual": "black",
    "naive": "tab:blue",
    "seasonal_naive": "tab:orange",
    "holt_winters": "tab:green",
    "arima": "tab:red",
}



# LOAD DATA


def load_data():
    ira = pd.read_csv(IRA_PATH)
    pop = pd.read_csv(POP_PATH)

    ira.columns = ira.columns.str.lower().str.strip()
    pop.columns = pop.columns.str.lower().str.strip()

    ira["iddpto"] = ira["iddpto"].astype(str).str.zfill(2)
    ira["departamento"] = ira["departamento"].astype(str).str.strip().str.upper()

    pop["iddpto"] = pop["iddpto"].astype(str).str.zfill(2)
    pop["department"] = pop["department"].astype(str).str.strip().str.upper()

    ira["ano"] = pd.to_numeric(ira["ano"], errors="coerce").astype("Int64")
    ira["semana"] = pd.to_numeric(ira["semana"], errors="coerce").astype("Int64")

    ira["date"] = pd.to_datetime(
        ira["ano"].astype(str) + "-" + ira["semana"].astype(str).str.zfill(2) + "-1",
        format="%G-%V-%u",
        errors="coerce"
    )

    ira = ira.dropna(subset=["date"]).copy()
    ira["year"] = ira["date"].dt.year.astype(int)
    ira = ira[(ira["year"] >= START_YEAR) & (ira["year"] <= END_YEAR)].copy()

    ira[TARGET_COL] = pd.to_numeric(ira[TARGET_COL], errors="coerce").fillna(0)

    pop["year"] = pd.to_numeric(pop["year"], errors="coerce").astype("Int64")
    pop["population"] = pd.to_numeric(pop["population"], errors="coerce")

    return ira, pop


def prepare_region_series(ira, pop, region_name):
    region = region_name.upper()

    ira_region = ira[ira["departamento"] == region].copy()

    weekly = (
        ira_region
        .groupby(["date", "year", "iddpto", "departamento"], as_index=False)[TARGET_COL]
        .sum()
    )

    weekly = weekly.merge(
        pop[["iddpto", "year", "population"]],
        on=["iddpto", "year"],
        how="left"
    )

    weekly = weekly.dropna(subset=["population"]).copy()

    weekly["incidence_raw"] = (weekly[TARGET_COL] / weekly["population"]) * 100000

    weekly = weekly.set_index("date").sort_index().asfreq("W-MON")
    weekly["departamento"] = region
    weekly["year"] = weekly.index.year
    weekly["incidence_raw"] = weekly["incidence_raw"].fillna(0)

    weekly["incidence_smooth"] = (
        weekly["incidence_raw"]
        .rolling(window=SMOOTH_WINDOW, min_periods=1)
        .mean()
    )

    weekly = weekly.reset_index()

    return weekly[[
        "date",
        "year",
        "departamento",
        "incidence_raw",
        "incidence_smooth"
    ]]



# BASELINE + STAT TRAINER


class BaselineStatTrainer:
    def __init__(self, region_df, region_name):
        self.region_df = region_df.copy()
        self.region_name = region_name
        self.results = []

    def load_dataset(self):
        self.region_df["date"] = pd.to_datetime(self.region_df["date"])
        self.region_df = self.region_df.sort_values("date").reset_index(drop=True)

        self.series = self.region_df["incidence_smooth"].values
        self.dates = self.region_df["date"].values

    @staticmethod
    def forecast_naive(train, horizon):
        preds = np.repeat(train[-1], horizon)
        return np.clip(preds, 0, None)

    @staticmethod
    def forecast_seasonal_naive(train, horizon):
        if len(train) < SEASONAL_PERIOD:
            preds = np.repeat(train[-1], horizon)
        else:
            last_season = train[-SEASONAL_PERIOD:]
            preds = np.array([last_season[i % SEASONAL_PERIOD] for i in range(horizon)])

        return np.clip(preds, 0, None)

    @staticmethod
    def forecast_holt_winters(train, horizon):
        try:
            fit = ExponentialSmoothing(
                train,
                trend="add",
                damped_trend=True,
                seasonal="add",
                seasonal_periods=SEASONAL_PERIOD,
                initialization_method="estimated"
            ).fit(optimized=True)

            preds = np.array(fit.forecast(horizon))

        except Exception:
            preds = np.repeat(train[-1], horizon)

        return np.clip(preds, 0, None)

    @staticmethod
    def forecast_arima(train, horizon):
        try:
            fit = ARIMA(train, order=(2, 1, 1)).fit()
            preds = np.array(fit.forecast(horizon))

        except Exception:
            preds = np.repeat(train[-1], horizon)

        return np.clip(preds, 0, None)

    def run_model(self, train, model_name, horizon):
        if model_name == "naive":
            return self.forecast_naive(train, horizon)

        if model_name == "seasonal_naive":
            return self.forecast_seasonal_naive(train, horizon)

        if model_name == "holt_winters":
            return self.forecast_holt_winters(train, horizon)

        if model_name == "arima":
            return self.forecast_arima(train, horizon)

        raise ValueError(f"Unknown model: {model_name}")

    def train(self, model_name):
        start = TRAIN_WINDOW_WEEKS

        while start + FORECAST_HORIZON <= len(self.series):
            train_start = start - TRAIN_WINDOW_WEEKS

            train_window = self.series[train_start:start]
            test_window = self.series[start:start + FORECAST_HORIZON]
            test_dates = self.dates[start:start + FORECAST_HORIZON]

            preds = self.run_model(
                train=train_window,
                model_name=model_name,
                horizon=FORECAST_HORIZON
            )

            for i in range(FORECAST_HORIZON):
                self.results.append([
                    str(test_dates[i])[:10],
                    test_window[i],
                    preds[i],
                    model_name,
                    self.region_name
                ])

            start += STEP_WEEKS

    def forecast_future(self, model_name):
        history = self.series.copy()
        future_rows = []

        last_actual_date = pd.to_datetime(self.region_df["date"].iloc[-1])

        for block in range(FUTURE_BLOCKS):
            train_window = history[-TRAIN_WINDOW_WEEKS:]

            block_preds = self.run_model(
                train=train_window,
                model_name=model_name,
                horizon=FORECAST_HORIZON
            )

            for j, pred_val in enumerate(block_preds, start=1):
                future_date = last_actual_date + pd.Timedelta(
                    weeks=(block * FORECAST_HORIZON) + j
                )

                future_rows.append({
                    "date": future_date,
                    "predicted": pred_val,
                    "model": model_name,
                    "region": self.region_name
                })

            history = np.append(history, block_preds)

        return pd.DataFrame(future_rows)

    def results_dataframe(self):
        return pd.DataFrame(
            self.results,
            columns=["date", "actual", "predicted", "model", "region"]
        )

    def metrics_dataframe(self):
        df = self.results_dataframe().copy()

        rows = []

        for model_name in df["model"].unique():
            temp = df[df["model"] == model_name].copy()

            rows.append({
                "region": self.region_name,
                "model": model_name,
                "mae": round(mean_absolute_error(temp["actual"], temp["predicted"]), 2),
                "rmse": round(np.sqrt(mean_squared_error(temp["actual"], temp["predicted"])), 2),
                "r2": round(r2_score(temp["actual"], temp["predicted"]), 2)
            })

        return pd.DataFrame(rows)

    def plot_group(self, model_names, future_df, title, output_png):
        df = self.results_dataframe().copy()
        df["date"] = pd.to_datetime(df["date"])

        actual_df = (
            df[["date", "actual"]]
            .drop_duplicates()
            .sort_values("date")
        )

        plt.figure(figsize=(14, 6))

        plt.plot(
            actual_df["date"],
            actual_df["actual"],
            label="Actual",
            color=MODEL_COLORS["actual"],
            linewidth=2.5
        )

        for model_name in model_names:
            temp = df[df["model"] == model_name].sort_values("date")

            plt.plot(
                temp["date"],
                temp["predicted"],
                label=model_name,
                color=MODEL_COLORS[model_name],
                linewidth=2
            )

            fut = future_df[future_df["model"] == model_name].sort_values("date")

            if not fut.empty:
                plt.plot(
                    fut["date"],
                    fut["predicted"],
                    label=f"{model_name}_future",
                    color=MODEL_COLORS[model_name],
                    linestyle="--",
                    linewidth=2
                )

        if not future_df.empty:
            plt.xlim(actual_df["date"].min(), future_df["date"].max())

        plt.axvline(
            actual_df["date"].max(),
            color="gray",
            linestyle=":",
            linewidth=1.5
        )

        plt.title(
            f"{self.region_name} | {title} | "
            f"1-Month Ahead Backtest + 1-Year Future Projection"
        )
        plt.xlabel("Date")
        plt.ylabel("Incidence per 100k")
        plt.grid(alpha=0.3)
        plt.legend()
        plt.tight_layout()
        plt.savefig(output_png, dpi=300, bbox_inches="tight")
        plt.close()



# MAIN


def main():
    ira, pop = load_data()
    df_region = prepare_region_series(ira, pop, REGION)

    trainer = BaselineStatTrainer(df_region, REGION)
    trainer.load_dataset()

    model_names = [
        "naive",
        "seasonal_naive",
        "holt_winters",
        "arima"
    ]

    for model_name in model_names:
        print(f"Running model: {model_name}")
        trainer.train(model_name)

    future_dfs = []

    for model_name in model_names:
        future_dfs.append(trainer.forecast_future(model_name))

    future_df = pd.concat(future_dfs, ignore_index=True)

    results_df = trainer.results_dataframe()
    metrics_df = trainer.metrics_dataframe()

    results_path = OUTPUT_DIR / f"{REGION.lower()}_baseline_stat_predictions.csv"
    metrics_path = OUTPUT_DIR / f"{REGION.lower()}_baseline_stat_metrics.csv"
    future_path = OUTPUT_DIR / f"{REGION.lower()}_baseline_stat_future_predictions.csv"

    baseline_plot_path = OUTPUT_DIR / f"{REGION.lower()}_baseline_models.png"
    stat_plot_path = OUTPUT_DIR / f"{REGION.lower()}_statistical_models.png"

    results_df.to_csv(results_path, index=False)
    metrics_df.to_csv(metrics_path, index=False)
    future_df.to_csv(future_path, index=False)

    trainer.plot_group(
        model_names=["naive", "seasonal_naive"],
        future_df=future_df,
        title="Baseline Models",
        output_png=baseline_plot_path
    )

    trainer.plot_group(
        model_names=["holt_winters", "arima"],
        future_df=future_df,
        title="Statistical Models",
        output_png=stat_plot_path
    )

    print("\nDone.")
    print(f"Saved predictions to: {results_path}")
    print(f"Saved metrics to: {metrics_path}")
    print(f"Saved future predictions to: {future_path}")
    print(f"Saved baseline plot to: {baseline_plot_path}")
    print(f"Saved statistical plot to: {stat_plot_path}")


if __name__ == "__main__":
    main()