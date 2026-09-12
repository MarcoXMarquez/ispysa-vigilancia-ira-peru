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

OUTPUT_DIR = ROOT_DIR / "outputs" / "adults_cases_ml_optimized"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

REGIONS = ["AREQUIPA", "CUSCO", "MOQUEGUA"]

TARGET_COL = "neumonias_60mas"

START_YEAR = 2006
END_YEAR = 2023

SMOOTH_WINDOW = 3

TRAIN_WINDOW_WEEKS = 5 * 52
FORECAST_HORIZON = 4
STEP_WEEKS = 4

FUTURE_WEEKS = 52
FUTURE_BLOCKS = FUTURE_WEEKS // FORECAST_HORIZON

USE_LOG_TARGET = True
CAP_OUTLIERS = True
CAP_QUANTILE = 0.99

MODEL_COLORS = {
    "actual": "black",
    "random_forest": "tab:green",
    "xgboost": "tab:brown",
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



# ML TRAINER CLASS


class MLRegionTrainer:
    def __init__(self, region_df, region_name):
        self.region_df = region_df.copy()
        self.region_name = region_name
        self.results = []

    def load_dataset(self):
        self.region_df["date"] = pd.to_datetime(self.region_df["date"])
        self.region_df = self.region_df.sort_values("date").reset_index(drop=True)

    @staticmethod
    def create_features(df):
        out = df.copy().sort_values("date").reset_index(drop=True)

        y_original = out["incidence_smooth"].astype(float).values
        y_model = transform_y(y_original)

        out["target_model"] = y_model

        # Lag features on transformed target
        out["lag_1"] = out["target_model"].shift(1)
        out["lag_2"] = out["target_model"].shift(2)
        out["lag_4"] = out["target_model"].shift(4)
        out["lag_8"] = out["target_model"].shift(8)
        out["lag_12"] = out["target_model"].shift(12)
        out["lag_26"] = out["target_model"].shift(26)
        out["lag_52"] = out["target_model"].shift(52)

        # Rolling features using past only
        out["roll_mean_4"] = out["target_model"].shift(1).rolling(4).mean()
        out["roll_std_4"] = out["target_model"].shift(1).rolling(4).std()

        out["roll_mean_8"] = out["target_model"].shift(1).rolling(8).mean()
        out["roll_std_8"] = out["target_model"].shift(1).rolling(8).std()
        out["roll_max_8"] = out["target_model"].shift(1).rolling(8).max()

        out["roll_mean_12"] = out["target_model"].shift(1).rolling(12).mean()
        out["roll_max_12"] = out["target_model"].shift(1).rolling(12).max()

        # Seasonal features
        out["weekofyear"] = out["date"].dt.isocalendar().week.astype(int)
        out["sin_week"] = np.sin(2 * np.pi * out["weekofyear"] / 52.0)
        out["cos_week"] = np.cos(2 * np.pi * out["weekofyear"] / 52.0)

        out = out.dropna().reset_index(drop=True)

        return out

    @staticmethod
    def get_feature_columns(df):
        exclude_cols = {
            "date",
            "year",
            "departamento",
            "incidence_raw",
            "incidence_smooth",
            "target_model"
        }

        return [c for c in df.columns if c not in exclude_cols]

    @staticmethod
    def create_model(model_name):
        if model_name == "random_forest":
            return RandomForestRegressor(
                n_estimators=500,
                max_depth=6,
                min_samples_split=6,
                min_samples_leaf=3,
                max_features="sqrt",
                random_state=42,
                n_jobs=-1
            )

        if model_name == "xgboost":
            return XGBRegressor(
                n_estimators=500,
                max_depth=3,
                learning_rate=0.03,
                subsample=0.8,
                colsample_bytree=0.8,
                min_child_weight=3,
                reg_alpha=0.05,
                reg_lambda=1.0,
                objective="reg:squarederror",
                random_state=42,
                n_jobs=-1
            )

        raise ValueError(f"Unknown model: {model_name}")

    def train(self, model_name):
        df_feat = self.create_features(self.region_df)
        feature_cols = self.get_feature_columns(df_feat)

        start = TRAIN_WINDOW_WEEKS

        while start + FORECAST_HORIZON <= len(df_feat):
            train_start = start - TRAIN_WINDOW_WEEKS

            train_df = df_feat.iloc[train_start:start].copy()
            test_df = df_feat.iloc[start:start + FORECAST_HORIZON].copy()

            X_train = train_df[feature_cols]
            y_train = train_df["target_model"]

            X_test = test_df[feature_cols]

            y_test_original = test_df["incidence_smooth"].values
            test_dates = test_df["date"].values

            model = self.create_model(model_name)
            model.fit(X_train, y_train)

            preds_model = model.predict(X_test)
            preds_original = inverse_transform_y(preds_model)

            train_original = train_df["incidence_smooth"].values
            upper_clip = np.percentile(train_original, 99)

            preds_original = np.clip(preds_original, 0, upper_clip)

            for i in range(len(test_df)):
                self.results.append([
                    str(test_dates[i])[:10],
                    y_test_original[i],
                    preds_original[i],
                    model_name,
                    self.region_name
                ])

            start += STEP_WEEKS

    def make_next_feature_row(self, history, next_date):
        y_original = history["incidence_smooth"].astype(float).values
        y_model = transform_y(y_original)

        lag_1 = y_model[-1]
        lag_2 = y_model[-2]
        lag_4 = y_model[-4]
        lag_8 = y_model[-8]
        lag_12 = y_model[-12]
        lag_26 = y_model[-26]
        lag_52 = y_model[-52]

        roll_mean_4 = np.mean(y_model[-4:])
        roll_std_4 = np.std(y_model[-4:], ddof=1) if len(y_model[-4:]) > 1 else 0.0

        roll_mean_8 = np.mean(y_model[-8:])
        roll_std_8 = np.std(y_model[-8:], ddof=1) if len(y_model[-8:]) > 1 else 0.0
        roll_max_8 = np.max(y_model[-8:])

        roll_mean_12 = np.mean(y_model[-12:])
        roll_max_12 = np.max(y_model[-12:])

        weekofyear = pd.Timestamp(next_date).isocalendar().week
        sin_week = np.sin(2 * np.pi * weekofyear / 52.0)
        cos_week = np.cos(2 * np.pi * weekofyear / 52.0)

        X_next = pd.DataFrame([{
            "lag_1": lag_1,
            "lag_2": lag_2,
            "lag_4": lag_4,
            "lag_8": lag_8,
            "lag_12": lag_12,
            "lag_26": lag_26,
            "lag_52": lag_52,
            "roll_mean_4": roll_mean_4,
            "roll_std_4": roll_std_4,
            "roll_mean_8": roll_mean_8,
            "roll_std_8": roll_std_8,
            "roll_max_8": roll_max_8,
            "roll_mean_12": roll_mean_12,
            "roll_max_12": roll_max_12,
            "weekofyear": int(weekofyear),
            "sin_week": sin_week,
            "cos_week": cos_week
        }])

        return X_next

    def forecast_future(self, model_name):
        history = self.region_df.copy().sort_values("date").reset_index(drop=True)
        future_rows = []

        for _ in range(FUTURE_BLOCKS):
            df_feat = self.create_features(history)
            feature_cols = self.get_feature_columns(df_feat)

            train_df = df_feat.iloc[-TRAIN_WINDOW_WEEKS:].copy()

            X_train = train_df[feature_cols]
            y_train = train_df["target_model"]

            model = self.create_model(model_name)
            model.fit(X_train, y_train)

            recursive_history = history.copy()
            last_date = history["date"].iloc[-1]

            block_rows = []

            train_original = train_df["incidence_smooth"].values
            upper_clip = np.percentile(train_original, 99)

            for h in range(1, FORECAST_HORIZON + 1):
                next_date = last_date + pd.Timedelta(weeks=h)

                X_next = self.make_next_feature_row(
                    history=recursive_history,
                    next_date=next_date
                )

                X_next = X_next[feature_cols]

                pred_model = model.predict(X_next)[0]
                pred_original = inverse_transform_y([pred_model])[0]
                pred_original = np.clip(pred_original, 0, upper_clip)

                future_rows.append({
                    "date": next_date,
                    "predicted": pred_original,
                    "model": model_name,
                    "region": self.region_name
                })

                new_row = {
                    "date": next_date,
                    "year": next_date.year,
                    "departamento": self.region_name,
                    "incidence_raw": pred_original,
                    "incidence_smooth": pred_original
                }

                block_rows.append(new_row)

                recursive_history = pd.concat(
                    [recursive_history, pd.DataFrame([new_row])],
                    ignore_index=True
                )

            history = pd.concat(
                [history, pd.DataFrame(block_rows)],
                ignore_index=True
            )

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

    def plot_results(self, future_df, output_png):
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

      for model_name in df["model"].unique():
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
            f"{self.region_name} | Adults 60+ Cases | Optimized ML Models | "
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

    model_names = ["random_forest", "xgboost"]

    for region in REGIONS:
        print(f"\nRunning region: {region}")

        df_region = prepare_region_series(ira, pop, region)

        trainer = MLRegionTrainer(df_region, region)
        trainer.load_dataset()

        for model_name in model_names:
            print(f"  Running model: {model_name}")
            trainer.train(model_name)

        future_dfs = []

        for model_name in model_names:
            print(f"  Future forecasting: {model_name}")
            future_dfs.append(trainer.forecast_future(model_name))

        future_df = pd.concat(future_dfs, ignore_index=True)

        results_df = trainer.results_dataframe()
        metrics_df = trainer.metrics_dataframe()

        all_results.append(results_df)
        all_metrics.append(metrics_df)
        all_future.append(future_df)

        region_prefix = region.lower()

        results_df.to_csv(
            OUTPUT_DIR / f"{region_prefix}_adults_cases_ml_predictions.csv",
            index=False
        )

        metrics_df.to_csv(
            OUTPUT_DIR / f"{region_prefix}_adults_cases_ml_metrics.csv",
            index=False
        )

        future_df.to_csv(
            OUTPUT_DIR / f"{region_prefix}_adults_cases_ml_future_predictions.csv",
            index=False
        )

        trainer.plot_results(
            future_df=future_df,
            output_png=OUTPUT_DIR / f"{region_prefix}_adults_cases_ml_plot.png"
        )

    final_results = pd.concat(all_results, ignore_index=True)
    final_metrics = pd.concat(all_metrics, ignore_index=True)
    final_future = pd.concat(all_future, ignore_index=True)

    final_results.to_csv(
        OUTPUT_DIR / "all_regions_adults_cases_ml_predictions.csv",
        index=False
    )

    final_metrics.to_csv(
        OUTPUT_DIR / "all_regions_adults_cases_ml_metrics.csv",
        index=False
    )

    final_future.to_csv(
        OUTPUT_DIR / "all_regions_adults_cases_ml_future_predictions.csv",
        index=False
    )

    print("\nDone.")
    print(f"Saved all outputs to: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()