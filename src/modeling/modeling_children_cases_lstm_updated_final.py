from pathlib import Path
import warnings
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.preprocessing import MinMaxScaler

import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.callbacks import EarlyStopping

warnings.filterwarnings("ignore")



# SETTINGS


ROOT_DIR = Path(__file__).resolve().parents[2]

IRA_PATH = ROOT_DIR / "data" / "raw" / "iras_updated.csv"
POP_PATH = ROOT_DIR / "data" / "processed" / "deptPopulationInterpolated_2000-2023.csv"
OUTPUT_DIR = ROOT_DIR / "outputs" / "children_cases_lstm_improved"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

REGION = "UCAYALI"
TARGET_COL = "neumonias_men5"

START_YEAR = 2000
END_YEAR = 2023

SMOOTH_WINDOW = 3

TRAIN_WINDOW_WEEKS = 5 * 52
FORECAST_HORIZON = 4
STEP_WEEKS = 4

FUTURE_WEEKS = 52
FUTURE_BLOCKS = FUTURE_WEEKS // FORECAST_HORIZON


LOOKBACK = 52
EPOCHS = 60
BATCH_SIZE = 8
LSTM_UNITS_1 = 48
LSTM_UNITS_2 = 24
DROPOUT_RATE = 0.3
VAL_WEEKS = 26



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

    weekly["weekofyear"] = weekly["date"].dt.isocalendar().week.astype(int)
    weekly["sin_week"] = np.sin(2 * np.pi * weekly["weekofyear"] / 52.0)
    weekly["cos_week"] = np.cos(2 * np.pi * weekly["weekofyear"] / 52.0)

    return weekly[
        [
            "date",
            "year",
            "departamento",
            "incidence_raw",
            "incidence_smooth",
            "sin_week",
            "cos_week",
        ]
    ]



# LSTM TRAINER CLASS


class LSTMRegionTrainer:
    def __init__(self, region_df, region_name):
        self.region_df = region_df.copy()
        self.region_name = region_name
        self.results = []

    def load_dataset(self):
        self.region_df["date"] = pd.to_datetime(self.region_df["date"])
        self.region_df = self.region_df.sort_values(by="date").reset_index(drop=True)

    @staticmethod
    def create_sequences(target_scaled, exog_values, lookback, horizon):
        X, y = [], []

        for i in range(lookback, len(target_scaled) - horizon + 1):
            target_seq = target_scaled[i - lookback:i, 0].reshape(-1, 1)
            exog_seq = exog_values[i - lookback:i]

            seq = np.concatenate([target_seq, exog_seq], axis=1)
            X.append(seq)
            y.append(target_scaled[i:i + horizon, 0])

        return np.array(X), np.array(y)

    @staticmethod
    def create_model(input_shape, horizon):
        model = Sequential()
        model.add(LSTM(LSTM_UNITS_1, return_sequences=True, input_shape=input_shape))
        model.add(Dropout(DROPOUT_RATE))
        model.add(LSTM(LSTM_UNITS_2))
        model.add(Dropout(DROPOUT_RATE))
        model.add(Dense(16, activation="relu"))
        model.add(Dense(horizon))

        model.compile(
               optimizer="adam",
               loss="mae"
            )

        return model

    def train(self):
        target_all = self.region_df["incidence_smooth"].values.reshape(-1, 1)
        exog_all = self.region_df[["sin_week", "cos_week"]].values
        dates_all = self.region_df["date"].values

        start = TRAIN_WINDOW_WEEKS

        while start + FORECAST_HORIZON <= len(self.region_df):
            train_start = start - TRAIN_WINDOW_WEEKS

            target_window = target_all[train_start:start]
            exog_window = exog_all[train_start:start]

            test_target = target_all[start:start + FORECAST_HORIZON].flatten()
            test_dates = dates_all[start:start + FORECAST_HORIZON]

            scaler = MinMaxScaler()
            target_window_scaled = scaler.fit_transform(target_window)

            X_all, y_all = self.create_sequences(
                target_scaled=target_window_scaled,
                exog_values=exog_window,
                lookback=LOOKBACK,
                horizon=FORECAST_HORIZON
            )

            if len(X_all) <= VAL_WEEKS:
                start += STEP_WEEKS
                continue

            X_train = X_all[:-VAL_WEEKS]
            y_train = y_all[:-VAL_WEEKS]

            X_val = X_all[-VAL_WEEKS:]
            y_val = y_all[-VAL_WEEKS:]

            model = self.create_model(
                input_shape=(X_train.shape[1], X_train.shape[2]),
                horizon=FORECAST_HORIZON
            )

            early_stop = EarlyStopping(
                monitor="val_loss",
                patience=8,
                restore_best_weights=True
            )

            model.fit(
                X_train,
                y_train,
                validation_data=(X_val, y_val),
                epochs=EPOCHS,
                batch_size=BATCH_SIZE,
                verbose=0,
                callbacks=[early_stop]
            )

            last_target_seq = target_window_scaled[-LOOKBACK:, 0].reshape(-1, 1)
            last_exog_seq = exog_window[-LOOKBACK:]

            X_test = np.concatenate([last_target_seq, last_exog_seq], axis=1)
            X_test = X_test.reshape(1, LOOKBACK, 3)

            pred_scaled = model.predict(X_test, verbose=0).reshape(-1, 1)
            preds = scaler.inverse_transform(pred_scaled).flatten()

            for i in range(FORECAST_HORIZON):
                self.results.append([
                    str(test_dates[i])[:10],
                    test_target[i],
                    preds[i],
                    "lstm",
                    self.region_name
                ])

            start += STEP_WEEKS

    def forecast_future(self):
        history = self.region_df.copy().sort_values("date").reset_index(drop=True)
        future_rows = []

        for _ in range(FUTURE_BLOCKS):
            target_window = history["incidence_smooth"].values[-TRAIN_WINDOW_WEEKS:].reshape(-1, 1)
            exog_window = history[["sin_week", "cos_week"]].values[-TRAIN_WINDOW_WEEKS:]

            scaler = MinMaxScaler()
            target_window_scaled = scaler.fit_transform(target_window)

            X_all, y_all = self.create_sequences(
                target_scaled=target_window_scaled,
                exog_values=exog_window,
                lookback=LOOKBACK,
                horizon=FORECAST_HORIZON
            )

            if len(X_all) <= VAL_WEEKS:
                break

            X_train = X_all[:-VAL_WEEKS]
            y_train = y_all[:-VAL_WEEKS]

            X_val = X_all[-VAL_WEEKS:]
            y_val = y_all[-VAL_WEEKS:]

            model = self.create_model(
                input_shape=(X_train.shape[1], X_train.shape[2]),
                horizon=FORECAST_HORIZON
            )

            early_stop = EarlyStopping(
                monitor="val_loss",
                patience=8,
                restore_best_weights=True
            )

            model.fit(
                X_train,
                y_train,
                validation_data=(X_val, y_val),
                epochs=EPOCHS,
                batch_size=BATCH_SIZE,
                verbose=0,
                callbacks=[early_stop]
            )

            last_target_seq = target_window_scaled[-LOOKBACK:, 0].reshape(-1, 1)
            last_exog_seq = exog_window[-LOOKBACK:]

            X_future = np.concatenate([last_target_seq, last_exog_seq], axis=1)
            X_future = X_future.reshape(1, LOOKBACK, 3)

            pred_scaled = model.predict(X_future, verbose=0).reshape(-1, 1)
            block_preds = scaler.inverse_transform(pred_scaled).flatten()

            last_date = pd.to_datetime(history["date"].iloc[-1])
            new_rows = []

            for j, pred_val in enumerate(block_preds, start=1):
                future_date = last_date + pd.Timedelta(weeks=j)

                weekofyear = future_date.isocalendar().week
                sin_week = np.sin(2 * np.pi * weekofyear / 52.0)
                cos_week = np.cos(2 * np.pi * weekofyear / 52.0)

                future_rows.append({
                    "date": future_date,
                    "predicted": pred_val,
                    "model": "lstm",
                    "region": self.region_name
                })

                new_rows.append({
                    "date": future_date,
                    "year": future_date.year,
                    "departamento": self.region_name,
                    "incidence_raw": pred_val,
                    "incidence_smooth": pred_val,
                    "sin_week": sin_week,
                    "cos_week": cos_week
                })

            history = pd.concat([history, pd.DataFrame(new_rows)], ignore_index=True)

        return pd.DataFrame(future_rows)

    def results_dataframe(self):
        return pd.DataFrame(
            self.results,
            columns=["date", "actual", "predicted", "model", "region"]
        )

    def metrics_dataframe(self):
        df = self.results_dataframe().copy()

        return pd.DataFrame([{
            "region": self.region_name,
            "model": "lstm",
            "mae": round(mean_absolute_error(df["actual"], df["predicted"]), 2),
            "rmse": round(np.sqrt(mean_squared_error(df["actual"], df["predicted"])), 2),
            "r2": round(r2_score(df["actual"], df["predicted"]), 2)
        }])

    def plot_results(self, future_df, output_png):
        df = self.results_dataframe().copy()
        df["date"] = pd.to_datetime(df["date"])

        actual_df = df[["date", "actual"]].drop_duplicates().sort_values("date")
        pred_df = df[["date", "predicted"]].sort_values("date")

        plt.figure(figsize=(14, 6))

        plt.plot(
            actual_df["date"],
            actual_df["actual"],
            label="Actual",
            color="black",
            linewidth=2.5
        )

        plt.plot(
            pred_df["date"],
            pred_df["predicted"],
            label="LSTM",
            color="tab:purple",
            linewidth=2
        )

        if not future_df.empty:
            plt.plot(
                future_df["date"],
                future_df["predicted"],
                label="LSTM_future",
                color="tab:purple",
                linestyle="--",
                linewidth=2
            )
            plt.xlim(actual_df["date"].min(), future_df["date"].max())

        plt.axvline(
            actual_df["date"].max(),
            color="gray",
            linestyle=":",
            linewidth=1.5
        )

        plt.title(
            f"{self.region_name} | LSTM Improved | "
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

    trainer = LSTMRegionTrainer(df_region, REGION)
    trainer.load_dataset()
    trainer.train()

    results_df = trainer.results_dataframe()
    metrics_df = trainer.metrics_dataframe()
    future_df = trainer.forecast_future()

    results_path = OUTPUT_DIR / f"{REGION.lower()}_lstm_predictions.csv"
    metrics_path = OUTPUT_DIR / f"{REGION.lower()}_lstm_metrics.csv"
    future_path = OUTPUT_DIR / f"{REGION.lower()}_lstm_future_predictions.csv"
    plot_path = OUTPUT_DIR / f"{REGION.lower()}_lstm_plot.png"

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