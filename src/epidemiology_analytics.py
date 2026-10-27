"""
Módulo de Métodos Analíticos Avanzados de Vigilancia Epidemiológica
Implementa el Canal Endémico de Bortman (OPS/MINSA),
el Modelo de Triaje de Emergencias Manchester y
la Matriz de Riesgo Bioclimático Regional (Heladas y Friaje).
"""

from typing import Dict, Any, Optional
import numpy as np
import pandas as pd


def compute_bortman_corridor(
    history_df: pd.DataFrame,
    col_name: str,
    target_value: Optional[float] = None
) -> Dict[str, Any]:
    """
    Calcula los límites del Canal Endémico según la metodología de Bortman (OPS/OMS)
    utilizando los cuartiles históricos Q1 (P25), Q2 (P50 - Mediana) y Q3 (P75).

    Zonas epidemiológicas:
    - Éxito: [0, Q1)
    - Seguridad: [Q1, Q2)
    - Alarma: [Q2, Q3)
    - Epidemia: >= Q3
    """
    series = history_df[col_name].dropna()
    if len(series) < 3:
        # Fallback defensivo
        q1 = float(series.quantile(0.25)) if not series.empty else 0.0
        q2 = float(series.median()) if not series.empty else 0.0
        q3 = float(series.quantile(0.75)) if not series.empty else 0.0
    else:
        q1 = float(series.quantile(0.25))
        q2 = float(series.median())
        q3 = float(series.quantile(0.75))

    val = target_value if target_value is not None else (series.iloc[-1] if not series.empty else 0.0)

    if val >= q3 and q3 > 0:
        zone_name = "Zona de Epidemia"
        zone_code = "EPIDEMIA"
        zone_color = "#991b1b"  # Rojo carmesí
        zone_bg = "#fef2f2"
        badge_border = "#f87171"
        recommendation = (
            "Brote epidémico activo. Activar sala de contingencia hospitalaria, "
            "movilización de insumos y refuerzo de triage diferenciado."
        )
    elif val >= q2:
        zone_name = "Zona de Alarma"
        zone_code = "ALARMA"
        zone_color = "#c2410c"  # Naranja
        zone_bg = "#fff7ed"
        badge_border = "#fb923c"
        recommendation = (
            "Incidencia por encima de la mediana esperada. Intensificar la búsqueda "
            "activa comunitaria y verificar stock de antibióticos y oxígeno."
        )
    elif val >= q1:
        zone_name = "Zona de Seguridad"
        zone_code = "SEGURIDAD"
        zone_color = "#15803d"  # Verde clínico
        zone_bg = "#f0fdf4"
        badge_border = "#86efac"
        recommendation = (
            "Incidencia dentro del rango normal esperado para la serie temporal. "
            "Mantener vigilancia centinela de rutina."
        )
    else:
        zone_name = "Zona de Éxito"
        zone_code = "EXITO"
        zone_color = "#0369a1"  # Azul sanitario
        zone_bg = "#f0f9ff"
        badge_border = "#7dd3fc"
        recommendation = (
            "Valores de incidencia significativamente reducidos (primer cuartil). "
            "Evaluar efectividad de campañas previas de vacunación."
        )

    return {
        "q1": round(q1, 2),
        "q2": round(q2, 2),
        "q3": round(q3, 2),
        "current_value": round(val, 2),
        "zone_name": zone_name,
        "zone_code": zone_code,
        "zone_color": zone_color,
        "zone_bg": zone_bg,
        "badge_border": badge_border,
        "recommendation": recommendation,
    }


def compute_manchester_and_resources(
    hospitalizations: float,
    cases: float,
    group: str = "men5"
) -> Dict[str, Any]:
    """
    Modela la demanda de camas críticas y recursos de soporte de oxígeno
    basado en el Sistema de Triaje Manchester (MTS) y directivas MINSA.
    """
    hosp = max(0.0, float(hospitalizations))
    _ = max(0.0, float(cases))

    if group == "men5":
        # Cohorte pediátrica
        icu_rate = 0.10  # 10% de hospitalizados a UCI pediátrica / UCIN
        oxygen_fraction = 0.35  # 35% de hospitalizados requieren oxigenoterapia suplementaria
        icu_oxygen_m3_day = 18.0  # Consumo m3/día en ventilación mecánica / alto flujo
        ward_oxygen_m3_day = 6.0  # Consumo m3/día en cánula nasal / máscara Venturi
        triage_weights = {
            "Nivel 1 - Resucitación (Rojo - Inmediato)": 0.03,
            "Nivel 2 - Emergencia (Naranja - 10 min)": 0.12,
            "Nivel 3 - Urgencia (Amarillo - 60 min)": 0.35,
            "Nivel 4 - Menor (Verde - 120 min)": 0.35,
            "Nivel 5 - No Urgente (Azul - 240 min)": 0.15,
        }
    else:
        # Cohorte geriátrica (60 a más)
        icu_rate = 0.16  # 16% de hospitalizados a UCI Adultos
        oxygen_fraction = 0.50  # 50% de hospitalizados requieren oxigenoterapia suplementaria
        icu_oxygen_m3_day = 22.0
        ward_oxygen_m3_day = 7.5
        triage_weights = {
            "Nivel 1 - Resucitación (Rojo - Inmediato)": 0.05,
            "Nivel 2 - Emergencia (Naranja - 10 min)": 0.18,
            "Nivel 3 - Urgencia (Amarillo - 60 min)": 0.40,
            "Nivel 4 - Menor (Verde - 120 min)": 0.27,
            "Nivel 5 - No Urgente (Azul - 240 min)": 0.10,
        }

    icu_beds = int(np.ceil(hosp * icu_rate))
    ward_oxygen_patients = int(np.ceil(hosp * oxygen_fraction))

    # Cálculo de volumen diario de oxígeno medicinal en m3
    oxygen_demand_m3_day = round(
        (icu_beds * icu_oxygen_m3_day) + (ward_oxygen_patients * ward_oxygen_m3_day),
        1
    )

    triage_breakdown = []
    for level, weight in triage_weights.items():
        est_count = int(np.round(hosp * weight)) if hosp > 0 else 0
        triage_breakdown.append({
            "Nivel de Triaje": level,
            "Pacientes Estimados": est_count,
            "Porcentaje": round(weight * 100, 1)
        })

    return {
        "hospitalizations": int(hosp),
        "icu_beds_estimated": icu_beds,
        "ward_oxygen_patients": ward_oxygen_patients,
        "oxygen_demand_m3_day": oxygen_demand_m3_day,
        "oxygen_cylinders_10m3_day": int(np.ceil(oxygen_demand_m3_day / 10.0)),
        "triage_df": pd.DataFrame(triage_breakdown)
    }


def compute_bioclimatic_vulnerability(
    annual_measures_df: pd.DataFrame,
    year: int,
    group: str = "men5"
) -> pd.DataFrame:
    """
    Cruza la tasa de incidencia del último año disponible con la tipología
    bioclimática regional del Perú (Heladas Altoandinas, Friaje Amazónico, Templado).
    """
    high_altitude_heladas = {
        "PUNO", "CUSCO", "HUANCAVELICA", "PASCO", "JUNIN",
        "AYACUCHO", "APURIMAC", "AREQUIPA", "MOQUEGUA", "TACNA"
    }
    amazon_friaje = {
        "LORETO", "UCAYALI", "MADRE DE DIOS", "SAN MARTIN", "AMAZONAS"
    }

    df_year = annual_measures_df[annual_measures_df["year"] == year].copy()
    if df_year.empty:
        df_year = annual_measures_df[
            annual_measures_df["year"] == annual_measures_df["year"].max()
        ].copy()

    records = []
    rate_col = f"cases_rate_{group}"
    cases_col = f"cases_{group}"

    for _, row in df_year.iterrows():
        dept = str(row["department"]).upper().strip()
        rate = float(row.get(rate_col, 0.0))
        cases = int(row.get(cases_col, 0))

        if dept in high_altitude_heladas:
            climate_zone = "Heladas Altoandinas (>3000 msnm)"
            exposure_factor = 1.35
            vulnerability_type = "Hipotermia y bajas temperaturas extremas"
        elif dept in amazon_friaje:
            climate_zone = "Friaje Amazónico (Selva Baja/Alta)"
            exposure_factor = 1.25
            vulnerability_type = "Descenso brusco térmico por vientos polares"
        else:
            climate_zone = "Costa y Valles Interandinos"
            exposure_factor = 1.00
            vulnerability_type = "Humedad relativa costera e inversión térmica"

        # Índice compuesto de riesgo bioclimático normalizado
        composite_risk = round(rate * exposure_factor, 1)
        if composite_risk >= 350:
            risk_tier = "Crítico (Alerta Roja)"
        elif composite_risk >= 180:
            risk_tier = "Alto (Alerta Naranja)"
        elif composite_risk >= 80:
            risk_tier = "Moderado (Alerta Amarilla)"
        else:
            risk_tier = "Bajo (Vigilancia Verde)"

        records.append({
            "department": dept,
            "climate_zone": climate_zone,
            "vulnerability_type": vulnerability_type,
            "cases": cases,
            "incidence_rate": round(rate, 1),
            "composite_risk_score": composite_risk,
            "risk_tier": risk_tier,
        })

    res_df = pd.DataFrame(records).sort_values(
        "composite_risk_score", ascending=False
    ).reset_index(drop=True)
    return res_df
