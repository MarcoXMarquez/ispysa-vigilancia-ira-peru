from pathlib import Path
import warnings
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.ensemble import RandomForestRegressor
from xgboost import XGBRegressor

warnings.filterwarnings("ignore")



# SETTINGS


ROOT_DIR = Path(__file__).resolve().parents[2]

IRA_PATH = ROOT_DIR / "data" / "raw" / "iras_updated.csv"
POP_PATH = ROOT_DIR / "data" / "processed" / "deptPopulationInterpolated_2000-2023.csv"
OUTPUT_DIR = ROOT_DIR / "outputs" / "children_cases_ml_simulation_recursive"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

REGION = "UCAYALI"
TARGET_COL = "neumonias_men5"

START_YEAR = 2000
END_YEAR = 2023

SMOOTH_WINDOW = 3

# historical rolling backtest settings
TRAIN_WINDOW_WEEKS = 5 * 52
FORECAST_HORIZON = 4          # 1 month ahead
STEP_WEEKS = 4                # move 1 month each time

# future projection settings
FUTURE_WEEKS = 52
FUTURE_BLOCKS = FUTURE_WEEKS // FORECAST_HORIZON   # 13 blocks of 4 weeks



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
        ira_region.groupby(["date", "year", "iddpto", "departamento"], as_index=False)[TARGET_COL]
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
    return weekly[["date", "year", "departamento", "incidence_raw", "incidence_smooth"]]



# ML TRAINER CLASS


class MLRegionTrainer:
    def __init__(self, region_df, region_name):
        self.region_df = region_df.copy()
        self.region_name = region_name
        self.results = []

    def load_dataset(self):
        self.region_df["date"] = pd.to_datetime(self.region_df["date"])
        self.region_df = self.region_df.sort_values(by="date").reset_index(drop=True)

    @staticmethod
    def create_features(df):
        out = df.copy().sort_values("date").reset_index(drop=True)
        y = out["incidence_smooth"]

        # lag features
        out["lag_1"] = y.shift(1)
        out["lag_2"] = y.shift(2)
        out["lag_4"] = y.shift(4)
        out["lag_12"] = y.shift(12)
        out["lag_52"] = y.shift(52)

        # rolling features using past only
        out["roll_mean_4"] = y.shift(1).rolling(4).mean()
        out["roll_std_4"] = y.shift(1).rolling(4).std()

        # seasonal features
        out["weekofyear"] = out["date"].dt.isocalendar().week.astype(int)
        out["sin_week"] = np.sin(2 * np.pi * out["weekofyear"] / 52.0)
        out["cos_week"] = np.cos(2 * np.pi * out["weekofyear"] / 52.0)

        out = out.dropna().reset_index(drop=True)
        return out

    @staticmethod
    def get_feature_columns(df):
        exclude_cols = {"date", "year", "departamento", "incidence_raw", "incidence_smooth"}
        return [c for c in df.columns if c not in exclude_cols]

    @staticmethod
    def create_model(model_name):
        if model_name == "random_forest":
            return RandomForestRegressor(
                n_estimators=300,
                max_depth=8,
                min_samples_split=5,
                min_samples_leaf=2,
                random_state=42,
                n_jobs=-1
            )

        elif model_name == "xgboost":
            return XGBRegressor(
                n_estimators=300,
                max_depth=4,
                learning_rate=0.05,
                subsample=0.9,
                colsample_bytree=0.9,
                objective="reg:squarederror",
                random_state=42,
                n_jobs=-1
            )

        else:
            raise ValueError(f"Unknown model: {model_name}")

    def train(self, model_name):
        """
        Original stronger backtest logic:
        uses true future feature rows during evaluation.
        """
        df_feat = self.create_features(self.region_df)
        feature_cols = self.get_feature_columns(df_feat)

        start = TRAIN_WINDOW_WEEKS

        while start + FORECAST_HORIZON <= len(df_feat):
            train_start = start - TRAIN_WINDOW_WEEKS

            train_df = df_feat.iloc[train_start:start].copy()
            test_df = df_feat.iloc[start:start + FORECAST_HORIZON].copy()

            X_train = train_df[feature_cols]
            y_train = train_df["incidence_smooth"]

            X_test = test_df[feature_cols]
            y_test = test_df["incidence_smooth"].values
            test_dates = test_df["date"].values

            model = self.create_model(model_name)
            model.fit(X_train, y_train)

            preds = model.predict(X_test)

            for i in range(len(test_df)):
                self.results.append([
                    str(test_dates[i])[:10],
                    y_test[i],
                    preds[i],
                    model_name
                ])

            start += STEP_WEEKS

    def forecast_future(self, model_name):
        """
        Forecast 1 year ahead in 4-week blocks.
        For each block:
          - train on latest 5-year rolling window
          - predict next 4 weeks recursively
          - append the predicted 4 weeks
          - repeat for 13 blocks
        """
        history = self.region_df.copy().sort_values("date").reset_index(drop=True)
        future_rows = []

        for _ in range(FUTURE_BLOCKS):
            # build train features from current history
            df_feat = self.create_features(history)
            feature_cols = self.get_feature_columns(df_feat)

            train_df = df_feat.iloc[-TRAIN_WINDOW_WEEKS:].copy()
            X_train = train_df[feature_cols]
            y_train = train_df["incidence_smooth"]

            model = self.create_model(model_name)
            model.fit(X_train, y_train)

            recursive_history = history.copy()
            last_date = history["date"].iloc[-1]

            block_rows = []

            for h in range(1, FORECAST_HORIZON + 1):
                next_date = last_date + pd.Timedelta(weeks=h)

                y_hist = recursive_history["incidence_smooth"].values

                lag_1 = y_hist[-1]
                lag_2 = y_hist[-2]
                lag_4 = y_hist[-4]
                lag_12 = y_hist[-12]
                lag_52 = y_hist[-52]

                roll_mean_4 = np.mean(y_hist[-4:])
                roll_std_4 = np.std(y_hist[-4:], ddof=1) if len(y_hist[-4:]) > 1 else 0.0

                weekofyear = pd.Timestamp(next_date).isocalendar().week
                sin_week = np.sin(2 * np.pi * weekofyear / 52.0)
                cos_week = np.cos(2 * np.pi * weekofyear / 52.0)

                X_next = pd.DataFrame([{
                    "lag_1": lag_1,
                    "lag_2": lag_2,
                    "lag_4": lag_4,
                    "lag_12": lag_12,
                    "lag_52": lag_52,
                    "roll_mean_4": roll_mean_4,
                    "roll_std_4": roll_std_4,
                    "weekofyear": int(weekofyear),
                    "sin_week": sin_week,
                    "cos_week": cos_week
                }])

                pred = model.predict(X_next)[0]

                future_rows.append({
                    "date": next_date,
                    "predicted": pred,
                    "model": model_name
                })

                new_row = {
                    "date": next_date,
                    "year": next_date.year,
                    "departamento": self.region_name,
                    "incidence_raw": pred,
                    "incidence_smooth": pred
                }
                block_rows.append(new_row)

                recursive_history = pd.concat(
                    [recursive_history, pd.DataFrame([new_row])],
                    ignore_index=True
                )

            history = pd.concat([history, pd.DataFrame(block_rows)], ignore_index=True)

        return pd.DataFrame(future_rows)

    def results_dataframe(self):
        return pd.DataFrame(self.results, columns=["date", "actual", "predicted", "model"])

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

    def plot_results(self, future_df, output_png):
        df = self.results_dataframe().copy()
        df["date"] = pd.to_datetime(df["date"])

        actual_df = df[["date", "actual"]].drop_duplicates().sort_values("date")

        plt.figure(figsize=(14, 6))
        plt.plot(actual_df["date"], actual_df["actual"], label="Actual", color="black", linewidth=2.5)

        color_map = {
            "random_forest": "tab:green",
            "xgboost": "tab:brown"
        }

        for model_name in df["model"].unique():
            temp = df[df["model"] == model_name].sort_values("date")
            plt.plot(
                temp["date"],
                temp["predicted"],
                label=model_name,
                color=color_map[model_name],
                linewidth=2
            )

            fut = future_df[future_df["model"] == model_name].sort_values("date")
            if not fut.empty:
                plt.plot(
                    fut["date"],
                    fut["predicted"],
                    linestyle="--",
                    color=color_map[model_name],
                    linewidth=2,
                    label=f"{model_name}_future"
                )

        if not future_df.empty:
            plt.xlim(actual_df["date"].min(), future_df["date"].max())

        plt.axvline(actual_df["date"].max(), color="gray", linestyle=":", linewidth=1.5)

        plt.title(f"{self.region_name} | Machine Learning Models | 1-Month Ahead Backtest + 1-Year Future Projection")
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

    trainer = MLRegionTrainer(df_region, REGION)
    trainer.load_dataset()

    trainer.train("random_forest")
    trainer.train("xgboost")

    future_rf = trainer.forecast_future("random_forest")
    future_xgb = trainer.forecast_future("xgboost")
    future_df = pd.concat([future_rf, future_xgb], ignore_index=True)

    results_df = trainer.results_dataframe()
    metrics_df = trainer.metrics_dataframe()

    results_path = OUTPUT_DIR / f"{REGION.lower()}_ml_predictions.csv"
    metrics_path = OUTPUT_DIR / f"{REGION.lower()}_ml_metrics.csv"
    future_path = OUTPUT_DIR / f"{REGION.lower()}_ml_future_predictions.csv"
    plot_path = OUTPUT_DIR / f"{REGION.lower()}_ml_plot.png"

    results_df.to_csv(results_path, index=False)
    metrics_df.to_csv(metrics_path, index=False)
    future_df.to_csv(future_path, index=False)
    trainer.plot_results(future_df, plot_path)

    print("\nDone.")
    print(f"Saved predictions to: {results_path}")
    print(f"Saved metrics to: {metrics_path}")
    print(f"Saved future predictions to: {future_path}")
    print(f"Saved plot to: {plot_path}")


if __name__ == "__main__":
    main()