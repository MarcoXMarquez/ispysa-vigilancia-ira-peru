from pathlib import Path
import warnings
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from sklearn.ensemble import RandomForestRegressor
from xgboost import XGBRegressor

warnings.filterwarnings("ignore")


# SETTINGS


ROOT_DIR = Path(__file__).resolve().parents[2]

IRA_PATH = ROOT_DIR / "data" / "raw" / "iras_updated.csv"
POP_PATH = ROOT_DIR / "data" / "processed" / "deptPopulationInterpolated_2000-2023.csv"

OUTPUT_DIR = ROOT_DIR / "outputs" / "children_feature_importance_ci"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

REGIONS = ["HUANUCO", "LORETO", "UCAYALI"]

TARGET_COL = "neumonias_men5"

START_YEAR = 2000
END_YEAR = 2023

SMOOTH_WINDOW = 3

TRAIN_WINDOW_WEEKS = 5 * 52
FORECAST_HORIZON = 4
STEP_WEEKS = 4

N_BOOTSTRAP = 30
RANDOM_SEED = 42



# LOAD + PREPARE DATA


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

    return weekly[["date", "year", "departamento", "incidence_raw", "incidence_smooth"]]



# FEATURE ENGINEERING


def create_features(df):
    out = df.copy().sort_values("date").reset_index(drop=True)
    y = out["incidence_smooth"].astype(float)

    # Lag features
    out["lag_1"] = y.shift(1)
    out["lag_2"] = y.shift(2)
    out["lag_4"] = y.shift(4)
    out["lag_12"] = y.shift(12)
    out["lag_52"] = y.shift(52)

    # Rolling features using past only
    out["roll_mean_4"] = y.shift(1).rolling(4).mean()
    out["roll_std_4"] = y.shift(1).rolling(4).std()

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
        "departamento",
        "incidence_raw",
        "incidence_smooth"
    }
    return [c for c in df.columns if c not in exclude_cols]



# MODELS


def create_model(model_name, random_state=42):
    if model_name == "random_forest":
        return RandomForestRegressor(
            n_estimators=300,
            max_depth=8,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=random_state,
            n_jobs=-1
        )

    if model_name == "xgboost":
        return XGBRegressor(
            n_estimators=300,
            max_depth=4,
            learning_rate=0.05,
            subsample=0.9,
            colsample_bytree=0.9,
            objective="reg:squarederror",
            random_state=random_state,
            n_jobs=-1
        )

    raise ValueError(f"Unknown model: {model_name}")



# FEATURE IMPORTANCE


def save_feature_importance(region, model_name, model, feature_cols):
    if not hasattr(model, "feature_importances_"):
        return

    feat_imp = (
        pd.DataFrame({
            "feature": feature_cols,
            "importance": model.feature_importances_
        })
        .sort_values("importance", ascending=False)
    )

    csv_path = OUTPUT_DIR / f"{region.lower()}_{model_name}_feature_importance.csv"
    feat_imp.to_csv(csv_path, index=False)

    top_feat = feat_imp.head(10).sort_values("importance")

    plt.figure(figsize=(8, 5))
    plt.barh(top_feat["feature"], top_feat["importance"])
    plt.xlabel("Feature Importance")
    plt.ylabel("Feature")
    plt.title(f"{region} Children <5 - {model_name} Feature Importance")
    plt.tight_layout()

    plot_path = OUTPUT_DIR / f"{region.lower()}_{model_name}_feature_importance.png"
    plt.savefig(plot_path, dpi=300, bbox_inches="tight")
    plt.close()



# CONFIDENCE BANDS


def random_forest_interval(model, X_test, lower_q=5, upper_q=95):
    tree_preds = np.array([tree.predict(X_test) for tree in model.estimators_])
    pred = np.mean(tree_preds, axis=0)
    lower = np.percentile(tree_preds, lower_q, axis=0)
    upper = np.percentile(tree_preds, upper_q, axis=0)
    return pred, lower, upper


def bootstrap_xgb_interval(X_train, y_train, X_test, lower_q=5, upper_q=95):
    rng = np.random.default_rng(RANDOM_SEED)
    preds = []

    X_train = X_train.reset_index(drop=True)
    y_train = y_train.reset_index(drop=True)

    n = len(X_train)

    for b in range(N_BOOTSTRAP):
        sample_idx = rng.choice(np.arange(n), size=n, replace=True)

        X_boot = X_train.iloc[sample_idx]
        y_boot = y_train.iloc[sample_idx]

        model = create_model("xgboost", random_state=RANDOM_SEED + b)
        model.fit(X_boot, y_boot)

        preds.append(model.predict(X_test))

    preds = np.array(preds)

    pred = np.mean(preds, axis=0)
    lower = np.percentile(preds, lower_q, axis=0)
    upper = np.percentile(preds, upper_q, axis=0)

    return pred, lower, upper



# BACKTEST WITH CI


def run_region(region_df, region):
    df_feat = create_features(region_df)
    feature_cols = get_feature_columns(df_feat)

    all_results = []

    for model_name in ["random_forest", "xgboost"]:
        print(f"Running {region} - {model_name}")

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

            model = create_model(model_name, random_state=RANDOM_SEED)
            model.fit(X_train, y_train)

            # Save feature importance only for the last rolling window
            save_feature_importance(region, model_name, model, feature_cols)

            if model_name == "random_forest":
                pred, lower, upper = random_forest_interval(model, X_test)
            else:
                pred, lower, upper = bootstrap_xgb_interval(X_train, y_train, X_test)

            pred = np.clip(pred, 0, None)
            lower = np.clip(lower, 0, None)
            upper = np.clip(upper, 0, None)

            for i in range(len(test_df)):
                all_results.append({
                    "date": str(test_dates[i])[:10],
                    "actual": y_test[i],
                    "predicted": pred[i],
                    "lower_ci": lower[i],
                    "upper_ci": upper[i],
                    "model": model_name,
                    "region": region
                })

            start += STEP_WEEKS

    results_df = pd.DataFrame(all_results)
    csv_path = OUTPUT_DIR / f"{region.lower()}_children_ml_predictions_with_ci.csv"
    results_df.to_csv(csv_path, index=False)

    return results_df



# PLOT CI


def plot_ci(region, results_df):
    results_df["date"] = pd.to_datetime(results_df["date"])

    actual_df = (
        results_df[["date", "actual"]]
        .drop_duplicates()
        .sort_values("date")
    )

    plt.figure(figsize=(14, 6))
    plt.plot(actual_df["date"], actual_df["actual"], color="black", linewidth=2.5, label="Actual")

    for model_name in ["random_forest", "xgboost"]:
        temp = results_df[results_df["model"] == model_name].sort_values("date")

        plt.plot(temp["date"], temp["predicted"], linewidth=2, label=f"{model_name} prediction")

        plt.fill_between(
            temp["date"],
            temp["lower_ci"],
            temp["upper_ci"],
            alpha=0.2,
            label=f"{model_name} 90% interval"
        )

    plt.title(f"{region} Children <5 - RF/XGBoost Predictions with Confidence Bands")
    plt.xlabel("Date")
    plt.ylabel("Incidence per 100,000")
    plt.grid(alpha=0.3)
    plt.legend()
    plt.tight_layout()

    plot_path = OUTPUT_DIR / f"{region.lower()}_children_ml_confidence_bands.png"
    plt.savefig(plot_path, dpi=300, bbox_inches="tight")
    plt.close()



# MAIN


def main():
    ira, pop = load_data()

    for region in REGIONS:
        region_df = prepare_region_series(ira, pop, region)
        results_df = run_region(region_df, region)
        plot_ci(region, results_df)

    print(f"\nDone. Outputs saved to: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()