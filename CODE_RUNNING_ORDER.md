# Code Running Order

Run the scripts from the project root folder:

```bash
cd ISPySA - Pneumonia-main
```

Install requirements first:

```bash
pip install -r requirements.txt
```

---

## 1. Data Preparation

### 1.1 Population Interpolation

```bash
python src/data_preparation/Interpolation.py
```

Creates interpolated department-level population values for 2000–2023.

Expected output:

```text
data/processed/deptPopulationInterpolated_2000-2023.csv
```

### 1.2 Incidence Calculation

```bash
python src/data_preparation/Incidence.py
```

Creates annual disease measures using cases, hospitalizations, deaths, and interpolated population.

Expected output:

```text
data/processed/annual_disease_measures_dept_2000_2023.csv
```

### 1.3 Ranking Tables

```bash
python src/data_preparation/ranking_updated.py
```

Creates rank grids and top-3 frequency tables for children and adults across cases, hospitalizations, and deaths.

Expected outputs are saved in:

```text
outputs/tables/
```

---

## 2. Exploratory Data Analysis

### 2.1 Annual Variation

```bash
python src/eda/Annual_Variation.py
```

Creates national annual variation plots.

Expected outputs:

```text
outputs/figures/
outputs/tables/
```

### 2.2 Seasonality Analysis

```bash
python src/eda/seasonality_analysis.py
```

Creates monthly boxplots, year × month heatmaps, and STL decomposition plots.

Expected outputs:

```text
outputs/figures/
outputs/tables/
```

### 2.3 Top Regions Analysis

```bash
python src/eda/Top_regions_analysis.py
```

Creates rank-category heatmaps and top-3 frequency bar charts.

Expected outputs:

```text
outputs/figures/
```

### 2.4 Regional Analysis

```bash
python src/eda/Regional_Analysis.py
```

Runs detailed analysis for selected high-burden regions.

Expected outputs:

```text
outputs/figures/
```

### 2.5 Disease Severity Analysis

```bash
python src/eda/Disease_Severity_Analysis.py
```

Creates HR, CFR, rolling average, and HR vs CFR scatter plots.

Expected outputs:

```text
outputs/figures/
outputs/tables/
```

---

## 3. Regional Modeling

### 3.1 Children Under 5 Cases

Run baseline/statistical models:

```bash
python src/modeling/baseline_stat_children_cases_final.py
```

Run machine learning models:

```bash
python src/modeling/modeling_children_cases_ml_updated_final.py
```

Run LSTM model:

```bash
python src/modeling/modeling_children_cases_lstm_updated_final.py
```

Create final top-3 children model plots:

```bash
python src/modeling/Top3_regions_models_children_cases_final.py
```

Expected outputs:

```text
outputs/children_cases_baseline_stat_updated/
outputs/children_cases_ml_simulation_recursive/
outputs/children_cases_lstm_improved/
outputs/children_cases_top3_model_plots/
```

---

### 3.2 Adults 60+ Cases

Run baseline/statistical models:

```bash
python src/modeling/adults_cases_baseline_stats_final.py
```

Run machine learning models:

```bash
python src/modeling/adults_cases_ml_final.py
```

Run LSTM model:

```bash
python src/modeling/modeling_adults_cases_lstm_final.py
```

If your final LSTM version is `adults_cases_lstm_updated.py`, run this instead:

```bash
python src/modeling/adults_cases_lstm_updated.py
```

Create final top-3 adults model plots:

```bash
python src/modeling/top3_regions_adults_cases_final.py
```

Expected outputs:

```text
outputs/adults_cases_baseline_stat_optimized/
outputs/adults_cases_ml_optimized/
outputs/adults_cases_lstm_top3/
outputs/adults_cases_top3_models_final/
```

---

## 4. Feature Importance and Confidence Interval Analysis

### 4.1 Children Feature Importance and Confidence Intervals

```bash
python src/modeling/childran_feature_importance_ci.py
```

Expected outputs:

```text
outputs/children_feature_importance_ci/
```

### 4.2 Adults Feature Importance and Confidence Intervals

```bash
python src/modeling/adults_feature_impotance_ci.py
```

Expected outputs:

```text
outputs/adults_feature_importance_ci/
```

Note: The script names contain spelling variations in the current folder structure. Keep the filenames as they are unless you rename them consistently in the project.

---

## 5. National-Level Modeling

### 5.1 National Children Under 5 Cases

```bash
python src/modeling/Modeling_national_children_cases_ml.py
```

Expected outputs:

```text
outputs/national_children_cases_ml/
```

### 5.2 National Adults 60+ Cases

```bash
python src/modeling/modeling_national_adults_cases_ml.py
```

Expected outputs:

```text
outputs/national_adults_cases_ml/
```

---

## Complete Run Order

If running everything from scratch, use this order:

```bash
python src/data_preparation/Interpolation.py
python src/data_preparation/Incidence.py
python src/data_preparation/ranking_updated.py

python src/eda/Annual_Variation.py
python src/eda/seasonality_analysis.py
python src/eda/Top_regions_analysis.py
python src/eda/Regional_Analysis.py
python src/eda/Disease_Severity_Analysis.py

python src/modeling/baseline_stat_children_cases_final.py
python src/modeling/modeling_children_cases_ml_updated_final.py
python src/modeling/modeling_children_cases_lstm_updated_final.py
python src/modeling/Top3_regions_models_children_cases_final.py

python src/modeling/adults_cases_baseline_stats_final.py
python src/modeling/adults_cases_ml_final.py
python src/modeling/modeling_adults_cases_lstm_final.py
python src/modeling/top3_regions_adults_cases_final.py

python src/modeling/childran_feature_importance_ci.py
python src/modeling/adults_feature_impotance_ci.py

python src/modeling/Modeling_national_children_cases_ml.py
python src/modeling/modeling_national_adults_cases_ml.py
```

---

## Notes

1. Run all commands from the project root folder.
2. Make sure `iras_updated.csv` exists inside `data/raw/`.
3. Make sure the interpolated population file exists before running EDA or modeling scripts.
4. If a script fails because an output folder does not exist, create the folder manually or update the script to create it using `mkdir(parents=True, exist_ok=True)`.
5. Some scripts depend on ranking outputs, so run `ranking_updated.py` before top-region or regional modeling scripts.
6. National modeling should be run after regional modeling and feature importance/confidence interval analysis, following the final project workflow.
