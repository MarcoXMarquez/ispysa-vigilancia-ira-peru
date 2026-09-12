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

OUTPUT_DIR = ROOT_DIR / "outputs" / "national_adults_cases_ml"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

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
    return np.log1p(y) if USE_LOG_TARGET else y


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
            f"{TARGET_COL} not found. Available columns:\n{ira.columns.tolist()}"
        )

    ira["iddpto"] = ira["iddpto"].astype(str).str.zfill(2)
    pop["iddpto"] = pop["iddpto"].astype(str).str.zfill(2)

    ira["ano"] = pd.to_numeric(ira["ano"], errors="coerce").astype("Int64")
    ira["semana"] = pd.to_numeric(ira["semana"], errors="coerce").astype("Int64")

    ira[TARGET_COL] = pd.to_numeric(ira[TARGET_COL], errors="coerce").fillna(0)

    ira["date"] = pd.to_datetime(
        ira["ano"].astype(str) + "-" + ira["semana"].astype(str).str.zfill(2) + "-1",
        format="%G-%V-%u",
        errors="coerce"
    )

    ira = ira.dropna(subset=["date"]).copy()
    ira["year"] = ira["date"].dt.year.astype(int)

    ira = ira[
        (ira["year"] >= START_YEAR) &
        (ira["year"] <= END_YEAR)
    ].copy()

    pop["year"] = pd.to_numeric(pop["year"], errors="coerce").astype("Int64")
    pop["population"] = pd.to_numeric(pop["population"], errors="coerce")

    return ira, pop



# NATIONAL SERIES


def prepare_national_series(ira, pop):
    weekly_cases = (
        ira.groupby(["date", "year"], as_index=False)[TARGET_COL]
        .sum()
        .rename(columns={TARGET_COL: "cases"})
    )

    national_pop = (
        pop.groupby("year", as_index=False)["population"]
        .sum()
    )

    weekly = weekly_cases.merge(
        national_pop,
        on="year",
        how="left"
    )

    weekly = weekly.dropna(subset=["population"]).copy()

    weekly["incidence_raw"] = (weekly["cases"] / weekly["population"]) * 100000

    if CAP_OUTLIERS:
        cap_value = weekly["incidence_raw"].quantile(CAP_QUANTILE)
        weekly["incidence_raw"] = weekly["incidence_raw"].clip(upper=cap_value)

    weekly = weekly.set_index("date").sort_index().asfreq("W-MON")
    weekly["year"] = weekly.index.year

    weekly["incidence_raw"] = (
        weekly["incidence_raw"]
        .interpolate(limit_direction="both")
        .fillna(0)
    )

    weekly["incidence_smooth"] = (
        weekly["incidence_raw"]
        .rolling(window=SMOOTH_WINDOW, min_periods=1)
        .mean()
    )

    weekly = weekly.reset_index()

    return weekly[[
        "date",
        "year",
        "incidence_raw",
        "incidence_smooth"
    ]]



# FEATURE ENGINEERING


def create_features(df):
    out = df.copy().sort_values("date").reset_index(drop=True)

    y_original = out["incidence_smooth"].astype(float).values
    y_model = transform_y(y_original)

    out["target_model"] = y_model

    # Lag features
    out["lag_1"] = out["target_model"].shift(1)
    out["lag_2"] = out["target_model"].shift(2)
    out["lag_4"] = out["target_model"].shift(4)
    out["lag_8"] = out["target_model"].shift(8)
    out["lag_12"] = out["target_model"].shift(12)
    out["lag_26"] = out["target_model"].shift(26)
    out["lag_52"] = out["target_model"].shift(52)

    # Rolling features using past values only
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


def get_feature_columns(df):
    exclude_cols = {
        "date",
        "year",
        "incidence_raw",
        "incidence_smooth",
        "target_model"
    }

    return [c for c in df.columns if c not in exclude_cols]


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


def make_next_feature_row(history, next_date):
    y_original = history["incidence_smooth"].astype(float).values
    y_model = transform_y(y_original)

    weekofyear = pd.Timestamp(next_date).isocalendar().week

    row = {
        "lag_1": y_model[-1],
        "lag_2": y_model[-2],
        "lag_4": y_model[-4],
        "lag_8": y_model[-8],
        "lag_12": y_model[-12],
        "lag_26": y_model[-26],
        "lag_52": y_model[-52],

        "roll_mean_4": np.mean(y_model[-4:]),
        "roll_std_4": np.std(y_model[-4:], ddof=1) if len(y_model[-4:]) > 1 else 0.0,

        "roll_mean_8": np.mean(y_model[-8:]),
        "roll_std_8": np.std(y_model[-8:], ddof=1) if len(y_model[-8:]) > 1 else 0.0,
        "roll_max_8": np.max(y_model[-8:]),

        "roll_mean_12": np.mean(y_model[-12:]),
        "roll_max_12": np.max(y_model[-12:]),

        "weekofyear": int(weekofyear),
        "sin_week": np.sin(2 * np.pi * weekofyear / 52.0),
        "cos_week": np.cos(2 * np.pi * weekofyear / 52.0),
    }

    return pd.DataFrame([row])



# TRAINER


class NationalMLTrainer:
    def __init__(self, national_df):
        self.df = national_df.copy().sort_values("date").reset_index(drop=True)
        self.results = []

    def train_backtest(self, model_name):
        start = TRAIN_WINDOW_WEEKS

        while start + FORECAST_HORIZON <= len(self.df):
            train_start = start - TRAIN_WINDOW_WEEKS

            history = self.df.iloc[train_start:start].copy().reset_index(drop=True)
            test = self.df.iloc[start:start + FORECAST_HORIZON].copy().reset_index(drop=True)

            df_feat = create_features(history)
            feature_cols = get_feature_columns(df_feat)

            train_df = df_feat.iloc[-TRAIN_WINDOW_WEEKS:].copy()

            X_train = train_df[feature_cols]
            y_train = train_df["target_model"]

            model = create_model(model_name)
            model.fit(X_train, y_train)

            recursive_history = history.copy()
            preds = []

            train_original = history["incidence_smooth"].values
            upper_clip = np.percentile(train_original, 99)

            for h in range(FORECAST_HORIZON):
                next_date = test.loc[h, "date"]

                X_next = make_next_feature_row(recursive_history, next_date)
                X_next = X_next[feature_cols]

                pred_model = model.predict(X_next)[0]
                pred_original = inverse_transform_y([pred_model])[0]
                pred_original = np.clip(pred_original, 0, upper_clip)

                preds.append(pred_original)

                new_row = {
                    "date": next_date,
                    "year": pd.Timestamp(next_date).year,
                    "incidence_raw": pred_original,
                    "incidence_smooth": pred_original
                }

                recursive_history = pd.concat(
                    [recursive_history, pd.DataFrame([new_row])],
                    ignore_index=True
                )

            for i in range(FORECAST_HORIZON):
                self.results.append({
                    "date": test.loc[i, "date"],
                    "actual": test.loc[i, "incidence_smooth"],
                    "predicted": preds[i],
                    "model": model_name
                })

            start += STEP_WEEKS

    def forecast_future(self, model_name):
        history = self.df.copy().sort_values("date").reset_index(drop=True)
        future_rows = []

        for _ in range(FUTURE_BLOCKS):
            df_feat = create_features(history)
            feature_cols = get_feature_columns(df_feat)

            train_df = df_feat.iloc[-TRAIN_WINDOW_WEEKS:].copy()

            X_train = train_df[feature_cols]
            y_train = train_df["target_model"]

            model = create_model(model_name)
            model.fit(X_train, y_train)

            recursive_history = history.copy()
            last_date = pd.to_datetime(history["date"].iloc[-1])

            block_rows = []

            train_original = train_df["incidence_smooth"].values
            upper_clip = np.percentile(train_original, 99)

            for h in range(1, FORECAST_HORIZON + 1):
                next_date = last_date + pd.Timedelta(weeks=h)

                X_next = make_next_feature_row(recursive_history, next_date)
                X_next = X_next[feature_cols]

                pred_model = model.predict(X_next)[0]
                pred_original = inverse_transform_y([pred_model])[0]
                pred_original = np.clip(pred_original, 0, upper_clip)

                future_rows.append({
                    "date": next_date,
                    "predicted": pred_original,
                    "model": model_name
                })

                new_row = {
                    "date": next_date,
                    "year": next_date.year,
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
        return pd.DataFrame(self.results)

    def metrics_dataframe(self):
        df = self.results_dataframe()

        rows = []

        for model_name in df["model"].unique():
            temp = df[df["model"] == model_name]

            rows.append({
                "scope": "National",
                "group": "Adults 60+",
                "target": "Cases",
                "model": model_name,
                "mae": round(mean_absolute_error(temp["actual"], temp["predicted"]), 3),
                "rmse": round(safe_rmse(temp["actual"], temp["predicted"]), 3),
                "r2": round(r2_score(temp["actual"], temp["predicted"]), 3)
            })

        return pd.DataFrame(rows)

    def plot_results(self, future_df, output_png):
        results_df = self.results_dataframe().copy()
        results_df["date"] = pd.to_datetime(results_df["date"])

        actual_df = self.df[["date", "incidence_smooth"]].copy()
        actual_df = actual_df.rename(columns={"incidence_smooth": "actual"})
        actual_df["date"] = pd.to_datetime(actual_df["date"])

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

        for model_name in results_df["model"].unique():
            temp = results_df[results_df["model"] == model_name].sort_values("date")

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
                        "model": [model_name]
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

        plt.axvline(
            last_actual_date,
            color="gray",
            linestyle=":",
            linewidth=1.5
        )

        if not future_df.empty:
            plt.xlim(actual_df["date"].min(), future_df["date"].max())

        plt.title(
            "National Adults 60+ Cases | ML Models | "
            "1-Month Ahead Backtest + 1-Year Future Projection"
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
    national_df = prepare_national_series(ira, pop)

    national_df.to_csv(
        OUTPUT_DIR / "national_adults_cases_weekly_series.csv",
        index=False
    )

    trainer = NationalMLTrainer(national_df)

    model_names = ["random_forest", "xgboost"]

    for model_name in model_names:
        print(f"Running backtest: {model_name}")
        trainer.train_backtest(model_name)

    future_dfs = []

    for model_name in model_names:
        print(f"Forecasting future: {model_name}")
        future_dfs.append(trainer.forecast_future(model_name))

    future_df = pd.concat(future_dfs, ignore_index=True)

    results_df = trainer.results_dataframe()
    metrics_df = trainer.metrics_dataframe()

    results_df.to_csv(
        OUTPUT_DIR / "national_adults_cases_ml_predictions.csv",
        index=False
    )

    metrics_df.to_csv(
        OUTPUT_DIR / "national_adults_cases_ml_metrics.csv",
        index=False
    )

    future_df.to_csv(
        OUTPUT_DIR / "national_adults_cases_ml_future_predictions.csv",
        index=False
    )

    trainer.plot_results(
        future_df=future_df,
        output_png=OUTPUT_DIR / "national_adults_cases_ml_plot.png"
    )

    print("\nDone.")
    print(f"Saved outputs to: {OUTPUT_DIR}")
    print(metrics_df)


if __name__ == "__main__":
    main()