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

OUTPUT_DIR = ROOT_DIR / "outputs" / "adults_cases_baseline_stat_optimized"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

REGIONS = ["AREQUIPA", "CUSCO", "MOQUEGUA"]

TARGET_COL = "neumonias_60mas"

START_YEAR = 2006
END_YEAR = 2023

SMOOTH_WINDOW = 3

TRAIN_WINDOW_WEEKS = 5 * 52
FORECAST_HORIZON = 4
STEP_WEEKS = 4
SEASONAL_PERIOD = 52

FUTURE_WEEKS = 52
FUTURE_BLOCKS = FUTURE_WEEKS // FORECAST_HORIZON

USE_LOG_TARGET = True
CAP_OUTLIERS = True
CAP_QUANTILE = 0.99

ARIMA_ORDERS = [
    (1, 1, 1),
    (2, 1, 1),
    (1, 1, 2),
    (2, 1, 2),
    (3, 1, 1)
]

MODEL_COLORS = {
    "actual": "black",
    "naive": "tab:blue",
    "seasonal_naive": "tab:orange",
    "holt_winters": "tab:green",
    "arima": "tab:red",
}


# HELPER FUNCTIONS

def transform_y(y):
    y = np.asarray(y, dtype=float)
    y = np.clip(y, 0, None)

    if USE_LOG_TARGET:
        return np.log1p(y)

    return y


def inverse_transform_y(y_transformed):
    y_transformed = np.asarray(y_transformed, dtype=float)

    if USE_LOG_TARGET:
        y = np.expm1(y_transformed)
    else:
        y = y_transformed

    return np.clip(y, 0, None)


def safe_rmse(y_true, y_pred):
    return np.sqrt(mean_squared_error(y_true, y_pred))


# LOAD DATA

def load_data():
    ira = pd.read_csv(IRA_PATH)
    pop = pd.read_csv(POP_PATH)

    ira.columns = ira.columns.str.lower().str.strip()
    pop.columns = pop.columns.str.lower().str.strip()

    if TARGET_COL not in ira.columns:
        raise KeyError(
            f"{TARGET_COL} not found. Available IRA columns:\n{ira.columns.tolist()}"
        )

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

    if CAP_OUTLIERS:
        cap_value = weekly["incidence_raw"].quantile(CAP_QUANTILE)
        weekly["incidence_raw"] = weekly["incidence_raw"].clip(upper=cap_value)

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

    return weekly[
        ["date", "year", "departamento", "incidence_raw", "incidence_smooth"]
    ]


# TRAINER CLASS

class BaselineStatTrainer:
    def __init__(self, region_df, region_name):
        self.region_df = region_df.copy()
        self.region_name = region_name
        self.results = []

    def load_dataset(self):
        self.region_df["date"] = pd.to_datetime(self.region_df["date"])
        self.region_df = self.region_df.sort_values("date").reset_index(drop=True)

        self.series_original = self.region_df["incidence_smooth"].values.astype(float)
        self.series_model = transform_y(self.series_original)
        self.dates = self.region_df["date"].values

    @staticmethod
    def forecast_naive(train_model, horizon):
        preds_model = np.repeat(train_model[-1], horizon)
        return inverse_transform_y(preds_model)

    @staticmethod
    def forecast_seasonal_naive(train_model, horizon):
        if len(train_model) < SEASONAL_PERIOD:
            preds_model = np.repeat(train_model[-1], horizon)
        else:
            last_season = train_model[-SEASONAL_PERIOD:]
            preds_model = np.array([last_season[i % SEASONAL_PERIOD] for i in range(horizon)])

        return inverse_transform_y(preds_model)

    @staticmethod
    def forecast_holt_winters(train_model, horizon):
        try:
            fit = ExponentialSmoothing(
                train_model,
                trend="add",
                damped_trend=True,
                seasonal="add",
                seasonal_periods=SEASONAL_PERIOD,
                initialization_method="estimated"
            ).fit(optimized=True)

            preds_model = np.array(fit.forecast(horizon))

        except Exception:
            preds_model = np.repeat(train_model[-1], horizon)

        preds = inverse_transform_y(preds_model)

        train_original = inverse_transform_y(train_model)
        upper_clip = np.percentile(train_original, 99)

        return np.clip(preds, 0, upper_clip)

    @staticmethod
    def forecast_arima(train_model, horizon):
        best_fit = None
        best_aic = np.inf

        for order in ARIMA_ORDERS:
            try:
                fit = ARIMA(train_model, order=order).fit()
                if fit.aic < best_aic:
                    best_aic = fit.aic
                    best_fit = fit
            except Exception:
                continue

        if best_fit is None:
            preds_model = np.repeat(train_model[-1], horizon)
        else:
            preds_model = np.array(best_fit.forecast(horizon))

        preds = inverse_transform_y(preds_model)

        train_original = inverse_transform_y(train_model)
        upper_clip = np.percentile(train_original, 99)

        return np.clip(preds, 0, upper_clip)

    def run_model(self, train_model, model_name, horizon):
        if model_name == "naive":
            return self.forecast_naive(train_model, horizon)

        if model_name == "seasonal_naive":
            return self.forecast_seasonal_naive(train_model, horizon)

        if model_name == "holt_winters":
            return self.forecast_holt_winters(train_model, horizon)

        if model_name == "arima":
            return self.forecast_arima(train_model, horizon)

        raise ValueError(f"Unknown model: {model_name}")

    def train(self, model_name):
        start = TRAIN_WINDOW_WEEKS

        while start + FORECAST_HORIZON <= len(self.series_model):
            train_start = start - TRAIN_WINDOW_WEEKS

            train_window_model = self.series_model[train_start:start]

            test_window_original = self.series_original[start:start + FORECAST_HORIZON]
            test_dates = self.dates[start:start + FORECAST_HORIZON]

            preds_original = self.run_model(
                train_model=train_window_model,
                model_name=model_name,
                horizon=FORECAST_HORIZON
            )

            for i in range(FORECAST_HORIZON):
                self.results.append([
                    str(test_dates[i])[:10],
                    test_window_original[i],
                    preds_original[i],
                    model_name,
                    self.region_name
                ])

            start += STEP_WEEKS

    def forecast_future(self, model_name):
        history_original = self.series_original.copy()
        history_model = transform_y(history_original)

        future_rows = []
        last_actual_date = pd.to_datetime(self.region_df["date"].iloc[-1])

        for block in range(FUTURE_BLOCKS):
            train_window_model = history_model[-TRAIN_WINDOW_WEEKS:]

            block_preds_original = self.run_model(
                train_model=train_window_model,
                model_name=model_name,
                horizon=FORECAST_HORIZON
            )

            for j, pred_val in enumerate(block_preds_original, start=1):
                future_date = last_actual_date + pd.Timedelta(
                    weeks=(block * FORECAST_HORIZON) + j
                )

                future_rows.append({
                    "date": future_date,
                    "predicted": pred_val,
                    "model": model_name,
                    "region": self.region_name
                })

            history_original = np.append(history_original, block_preds_original)
            history_model = transform_y(history_original)

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
                "mae": round(mean_absolute_error(temp["actual"], temp["predicted"]), 3),
                "rmse": round(safe_rmse(temp["actual"], temp["predicted"]), 3),
                "r2": round(r2_score(temp["actual"], temp["predicted"]), 3)
            })

        return pd.DataFrame(rows)

    def plot_group(self, model_names, future_df, title, output_png):
        df = self.results_dataframe().copy()
        df["date"] = pd.to_datetime(df["date"])

        actual_df = self.region_df[["date", "incidence_smooth"]].copy()
        actual_df["date"] = pd.to_datetime(actual_df["date"])
        actual_df = actual_df.rename(columns={"incidence_smooth": "actual"})
        actual_df = actual_df.sort_values("date")

        last_actual_date = actual_df["date"].max()
        last_actual_value = actual_df["actual"].iloc[-1]

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
                fut_connected = pd.concat([
                    pd.DataFrame({
                        "date": [last_actual_date],
                        "predicted": [last_actual_value],
                        "model": [model_name],
                        "region": [self.region_name]
                    }),
                    fut
                ], ignore_index=True)

                plt.plot(
                    fut_connected["date"],
                    fut_connected["predicted"],
                    label=f"{model_name}_future",
                    color=MODEL_COLORS[model_name],
                    linestyle="--",
                    linewidth=2
                )

        if not future_df.empty:
            plt.xlim(actual_df["date"].min(), future_df["date"].max())
        else:
            plt.xlim(actual_df["date"].min(), actual_df["date"].max())

        plt.axvline(
            last_actual_date,
            color="gray",
            linestyle=":",
            linewidth=1.5
        )

        plt.title(
            f"{self.region_name} | Adults 60+ Cases | {title} | "
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

    all_results = []
    all_metrics = []
    all_future = []

    model_names = ["naive", "seasonal_naive", "holt_winters", "arima"]

    for region in REGIONS:
        print(f"\nRunning region: {region}")

        df_region = prepare_region_series(ira, pop, region)

        trainer = BaselineStatTrainer(df_region, region)
        trainer.load_dataset()

        for model_name in model_names:
            print(f"  Running model: {model_name}")
            trainer.train(model_name)

        future_dfs = []
        for model_name in model_names:
            future_dfs.append(trainer.forecast_future(model_name))

        future_df = pd.concat(future_dfs, ignore_index=True)

        results_df = trainer.results_dataframe()
        metrics_df = trainer.metrics_dataframe()

        all_results.append(results_df)
        all_metrics.append(metrics_df)
        all_future.append(future_df)

        region_prefix = region.lower()

        results_df.to_csv(
            OUTPUT_DIR / f"{region_prefix}_adults_cases_baseline_stat_predictions.csv",
            index=False
        )

        metrics_df.to_csv(
            OUTPUT_DIR / f"{region_prefix}_adults_cases_baseline_stat_metrics.csv",
            index=False
        )

        future_df.to_csv(
            OUTPUT_DIR / f"{region_prefix}_adults_cases_baseline_stat_future_predictions.csv",
            index=False
        )

        trainer.plot_group(
            model_names=["naive", "seasonal_naive"],
            future_df=future_df,
            title="Baseline Models",
            output_png=OUTPUT_DIR / f"{region_prefix}_adults_cases_baseline_models.png"
        )

        trainer.plot_group(
            model_names=["holt_winters", "arima"],
            future_df=future_df,
            title="Statistical Models",
            output_png=OUTPUT_DIR / f"{region_prefix}_adults_cases_statistical_models.png"
        )

    final_results = pd.concat(all_results, ignore_index=True)
    final_metrics = pd.concat(all_metrics, ignore_index=True)
    final_future = pd.concat(all_future, ignore_index=True)

    final_results.to_csv(
        OUTPUT_DIR / "all_regions_adults_cases_baseline_stat_predictions.csv",
        index=False
    )

    final_metrics.to_csv(
        OUTPUT_DIR / "all_regions_adults_cases_baseline_stat_metrics.csv",
        index=False
    )

    final_future.to_csv(
        OUTPUT_DIR / "all_regions_adults_cases_baseline_stat_future_predictions.csv",
        index=False
    )

    print("\nDone.")
    print(f"Saved all outputs to: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()