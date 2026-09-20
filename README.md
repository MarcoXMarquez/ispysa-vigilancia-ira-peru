# Healthcare Analytics: Time Series Analysis of IRA for Public Health Monitoring in Peru

## Project Overview

This project analyzes Acute Respiratory Infections (IRA), including pneumonia-related indicators, in Peru using public health surveillance data from 2000–2023. The analysis focuses on two high-risk age groups:

- Children under 5 years
- Adults aged 60 years and above

The project includes data preparation, exploratory data analysis, regional burden analysis, disease severity analysis, forecasting, feature importance analysis, confidence interval analysis, and national-level modeling.

The main goal is to understand temporal and regional patterns in IRA incidence and evaluate forecasting models that can support public health monitoring and early-warning decisions.

---

## ISO/IEC 25000 Quality Measurement

The application includes a **Product Quality Metrics** panel. It presents a formal
measurement model and exports session evidence as JSON. It never treats a missing
measurement as a passing result.

| Characteristic | Indicator | Capture method | Target |
|---|---|---|---|
| Functional suitability | Validation Compliance Rate | Data-validation evidence from the current session | >= 95% |
| Reliability | Traceable Source Rate | SHA-256 and UTC read time for verified sources | 100% |
| Performance efficiency | Data load / filter calculation time | `time.perf_counter()` in the current session | Establish a baseline before setting a limit |
| Maintainability | Service Test Coverage; Critical Flake8 Errors | GitHub Actions evidence | >= 80%; 0 errors |
| Usability | Task Completion Rate | Observed usability-test CSV | >= 80% |

To capture usability evidence, download `usability_test_template.csv` from the
quality panel, register one attempted task per row, and upload the completed file.
The CSV must include `id_participante`, `id_tarea`, `completada`,
`duracion_segundos`, and `claridad_1_a_5`. The dashboard calculates task completion
only from those recorded observations.

The CI workflow saves `coverage.json`, the critical Flake8 output, and
`ci_quality_metrics.json` as a **quality-evidence** artifact for each run. This
artifact is the source for test coverage and critical lint findings; it is not
silently substituted by an earlier run.

---

## Objectives

The project aims to:

1. Analyze long-term IRA incidence trends in Peru.
2. Examine seasonal patterns in IRA incidence.
3. Identify high-burden regions using rate-based ranking.
4. Compare disease patterns across selected high-burden regions.
5. Evaluate disease severity using hospitalization rate and case fatality ratio.
6. Build and compare forecasting models for IRA incidence.
7. Interpret machine learning models using feature importance.
8. Estimate forecast uncertainty using confidence intervals.
9. Extend the best-performing model framework to national-level analysis.

---

## Data

### Raw Data

The main IRA surveillance file is:

```text
data/raw/iras_updated.csv
```

The dataset contains weekly observations with:

- Year and epidemiological week
- Department, province, and district information
- Cases
- Hospitalizations
- Deaths
- Age-group-specific indicators

Important columns include:

```text
neumonias_men5
neumonias_60mas
hospitalizados_men5
hospitalizados_60mas
defunciones_men5
defunciones_60mas
```

### Population Data

Population files include:

```text
data/raw/dept_updated.xlsx
data/raw/province_updated.xlsx
data/raw/district_updated.xlsx
data/processed/dept_updated_census.xlsx
data/processed/deptPopulationInterpolated_2000-2023.csv
```

Population interpolation was required because incidence rates need annual population values for each department across the full analysis period.

---

## Data Preparation

The preprocessing pipeline includes:

1. Cleaning and standardizing column names.
2. Standardizing department identifiers.
3. Converting `ano` and `semana` into weekly dates.
4. Interpolating department-level population from 2000–2023.
5. Aggregating data to weekly, monthly, annual, regional, and national levels.
6. Computing incidence rates per 100,000 population.

Incidence was calculated as:

```text
Incidence = (Cases / Population) × 100,000
```

For national analysis, incidence was computed using:

```text
National Incidence = (Total Cases across all regions / Total Population across all regions) × 100,000
```

National incidence was not calculated by summing regional incidence rates.

---

## Exploratory Data Analysis

### Annual Variation Analysis

Annual case, hospitalization, and death rates were analyzed for both age groups to identify long-term trends and structural changes.

### Seasonality Analysis

Seasonality was examined using:

- Monthly boxplots
- Year × month heatmaps
- STL decomposition

This helped identify recurring seasonal peaks, long-term trend patterns, and irregular spikes.

### Top Regions Analysis

Departments were ranked annually using rates per 100,000 population. The analysis included:

- Rank grids
- Top-3 frequency tables
- Rank-category heatmaps

Rank categories were grouped as:

```text
1–5   -> Category 1
6–10  -> Category 2
11–15 -> Category 3
16–20 -> Category 4
21–25 -> Category 5
```

This helped identify regions with persistent high IRA burden.

### Regional Analysis

After identifying high-burden regions, detailed regional analysis was performed for:

Children under 5:

```text
HUANUCO
LORETO
UCAYALI
```

Adults 60+:

```text
AREQUIPA
CUSCO
MOQUEGUA
```

For each region, annual trends, monthly seasonality, heatmaps, and STL decomposition were created.

### Disease Severity Analysis

Disease severity was evaluated using:

```text
Hospitalization Rate (HR) = Hospitalizations / Cases
Case Fatality Ratio (CFR) = Deaths / Cases
```

Weekly HR and CFR were smoothed using an 8-week rolling average. Annual HR vs CFR scatter plots were also created.

---

## Forecasting Methodology

The forecasting task focuses on weekly IRA incidence rates per 100,000 population.

### Models Used

Seven forecasting models were compared:

Baseline models:

- Naive
- Seasonal Naive

Statistical models:

- Holt-Winters / Exponential Smoothing
- ARIMA

Machine learning models:

- Random Forest
- XGBoost

Deep learning model:

- LSTM

---

## Rolling Window Validation

A rolling-window backtesting strategy was used.

```text
Training window: 5 years
Forecast horizon: 4 weeks
Step size: 4 weeks
Future projection: 52 weeks
```

This setup ensures models are trained only on past data and evaluated on future observations.

---

## Feature Engineering

Machine learning models used lag, rolling, and seasonal features, including:

```text
lag_1
lag_2
lag_4
lag_8
lag_12
lag_26
lag_52
roll_mean_4
roll_std_4
roll_mean_8
roll_std_8
roll_max_8
roll_mean_12
roll_max_12
sin_week
cos_week
```

These features capture short-term persistence, seasonal memory, recent variability, and yearly cycles.

---

## Feature Importance and Confidence Intervals

Feature importance analysis was performed for machine learning models to understand which predictors contributed most to model predictions.

Confidence interval analysis was used to quantify forecast uncertainty and avoid presenting future predictions as exact values. This is important because IRA incidence can be affected by reporting variation, outbreaks, public health disruptions, and environmental factors.

---

## National-Level Modeling

After regional modeling, national analysis was performed using machine learning models for:

- National children under 5 cases
- National adults 60+ cases

National modeling uses all regions combined into one weekly national time series.

### National Results

Children under 5:

| Model | MAE | RMSE | R² |
|---|---:|---:|---:|
| Random Forest | 0.210 | 0.296 | 0.922 |
| XGBoost | 0.184 | 0.271 | 0.935 |

Adults 60+:

| Model | MAE | RMSE | R² |
|---|---:|---:|---:|
| Random Forest | 0.107 | 0.183 | 0.869 |
| XGBoost | 0.097 | 0.168 | 0.890 |

XGBoost performed best for both national children and national adult cases.

---

## Key Findings

- Children under 5 show a long-term decline in IRA incidence.
- Adults 60+ show increasing or more variable incidence patterns in later years.
- Children’s incidence has stronger and more consistent seasonality.
- Adult incidence is more irregular and harder to forecast.
- Machine learning models, especially XGBoost and Random Forest, performed best in short-term forecasting.
- LSTM models captured broad temporal structure but often smoothed extreme peaks.
- National models performed strongly because national series are smoother than regional series.
- Regional forecasts are more challenging due to local spikes and higher variability.

---

## Project Structure

```text
Thummalapally_OUDSA5900-main/
│
├── data/
│   ├── external/
│   ├── processed/
│   │   ├── annual_disease_measures_dept_2000_2023.csv
│   │   ├── dept_updated_census.xlsx
│   │   └── deptPopulationInterpolated_2000-2023.csv
│   │
│   └── raw/
│       ├── dept_updated.xlsx
│       ├── district_updated.xlsx
│       ├── iras_updated.csv
│       ├── iras_updated.csv.zip
│       └── province_updated.xlsx
│
├── docs/
│
├── outputs/
│   ├── adults_cases_baseline_stat_optimized/
│   ├── adults_cases_lstm_top3/
│   ├── adults_cases_ml_optimized/
│   ├── adults_cases_top3_models_final/
│   ├── adults_feature_importance_ci/
│   ├── children_cases_baseline_stat_updated/
│   ├── children_cases_lstm_improved/
│   ├── children_cases_ml_simulation_recursive/
│   ├── children_cases_top3_model_plots/
│   ├── children_deaths_top3_baseline_stat_simulation/
│   ├── children_deaths_top3_lstm/
│   ├── children_deaths_top3_ml/
│   ├── children_feature_importance_ci/
│   ├── figures/
│   ├── national_adults_cases_ml/
│   ├── national_children_cases_ml/
│   ├── summary_stats_final_report_tables/
│   └── tables/
│
├── src/
│   ├── data_preparation/
│   │   ├── Incidence.py
│   │   ├── Interpolation.py
│   │   └── ranking_updated.py
│   │
│   ├── eda/
│   │   ├── Annual_Variation.py
│   │   ├── Disease_Severity_Analysis.py
│   │   ├── Regional_Analysis.py
│   │   ├── seasonality_analysis.py
│   │   └── Top_regions_analysis.py
│   │
│   └── modeling/
│       ├── adults_cases_baseline_stats_final.py
│       ├── adults_cases_lstm_updated.py
│       ├── adults_cases_ml_final.py
│       ├── adults_feature_impotance_ci.py
│       ├── baseline_stat_children_cases_final.py
│       ├── childran_feature_importance_ci.py
│       ├── modeling_adults_cases_lstm_final.py
│       ├── modeling_children_cases_lstm_updated_final.py
│       ├── modeling_children_cases_ml_updated_final.py
│       ├── modeling_national_adults_cases_ml.py
│       ├── Modeling_national_children_cases_ml.py
│       ├── summary_stats_table.py
│       ├── top3_regions_adults_cases_final.py
│       └── Top3_regions_models_children_cases_final.py
│
├── README.md
└── requirements.txt
```

---

## Requirements

Install dependencies using:

```bash
pip install -r requirements.txt
```

Main Python libraries used:

- pandas
- numpy
- matplotlib
- seaborn
- scikit-learn
- statsmodels
- xgboost
- tensorflow / keras

---

## Notes

- Regional modeling is the primary focus.
- National modeling is an extension using aggregated national data.
- National incidence is computed from total cases and total population.
- Regional incidence is computed separately by department.
- Forecasts should be interpreted as public health monitoring support, not exact predictions.
- Feature importance explains model behavior but does not imply causality.
- Confidence intervals communicate uncertainty around future projections.

---

## Authors

Gopichandh Danala  
Anvitha Reddy Thummalapally  
Lakshmi Sahasra Jangoan  

University of Oklahoma  
