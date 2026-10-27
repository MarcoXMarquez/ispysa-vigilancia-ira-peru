import re
from pathlib import Path

app_path = Path(__file__).resolve().parents[1] / "app.py"
content = app_path.read_text(encoding="utf-8")

# Normalize line endings to \n temporarily for matching
is_crlf = "\r\n" in content
content = content.replace("\r\n", "\n")

# 1. Update imports
import_target = "from src.app_indicators import previous_year_deltas, top3_for_period"
import_replacement = """from src.app_indicators import previous_year_deltas, top3_for_period
from src.epidemiology_analytics import (
    compute_bortman_corridor,
    compute_manchester_and_resources,
    compute_bioclimatic_vulnerability,
)"""

assert import_target in content, "Import target not found"
content = content.replace(import_target, import_replacement, 1)

# 2. Add extra CSS styles for Bortman, Manchester and Bioclimatic cards
css_marker = "/* Panel de Notas Metodológicas (Vaul) */"
extra_css = """    /* Canal Endémico de Bortman & Triaje Manchester */
    .bortman-panel {
        background-color: var(--bg-surface);
        border: 1px solid var(--border-subtle);
        border-radius: var(--radius-md);
        padding: 16px 20px;
        margin-bottom: 18px;
        box-shadow: var(--shadow-card);
    }
    .bortman-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 12px;
        margin-top: 10px;
    }
    .bortman-quartile-card {
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: var(--radius-sm);
        padding: 8px 12px;
        text-align: center;
    }
    .bortman-q-label {
        font-size: 0.75rem;
        font-weight: 700;
        color: #475569;
        text-transform: uppercase;
    }
    .bortman-q-val {
        font-size: 1.15rem;
        font-weight: 700;
        color: #0f172a;
    }
    .manchester-kpi-container {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 14px;
        margin-bottom: 16px;
    }
    .manchester-card {
        background: #ffffff;
        border: 1px solid var(--border-subtle);
        border-radius: var(--radius-md);
        padding: 14px 18px;
        box-shadow: var(--shadow-card);
    }

    """ + css_marker
assert css_marker in content, "CSS marker not found"
content = content.replace(css_marker, extra_css, 1)

# 3. Add data-testid to institutional hero
hero_target = '<div class="institutional-hero">'
hero_replacement = '<div class="institutional-hero" data-testid="hero-banner">'
assert hero_target in content, "Hero target not found"
content = content.replace(hero_target, hero_replacement, 1)

# 4. Replace section 3 (Alerta Sanitaria) to integrate Bortman Corridor Alert
section3_target = """# ==============================================================================
# 3. EVALUACIÓN Y SEMÁFORO DE ALERTA SANITARIA (ISO 9241-12)
# ==============================================================================
inc_rate = kpis["cases_rate"]
if inc_rate > 350:
    alert_class = "clinical-alert-danger"
    alert_code = "[ESTADO EPIDEMIOLÓGICO: ALERTA CRÍTICA]"
    alert_msg = (
        f"La tasa de incidencia acumulada se sitúa en {inc_rate:.1f} por 100,000 habitantes, superando "
        "el umbral de seguridad estacional. Se recomienda la activación de planes de contingencia hospitalaria, "
        "monitoreo de disponibilidad de oxígeno medicinal y abastecimiento oportuno de medicamentos esenciales."
    )
elif inc_rate > 150:
    alert_class = "clinical-alert-warning"
    alert_code = "[ESTADO EPIDEMIOLÓGICO: ALERTA PREVENTIVA]"
    alert_msg = (
        f"La tasa de incidencia se encuentra en {inc_rate:.1f} por 100,000 habitantes en zona de advertencia. "
        "Se recomienda intensificar el seguimiento semanal de casos y verificar cobertura de vacunación."
    )
else:
    alert_class = "clinical-alert-normal"
    alert_code = "[ESTADO EPIDEMIOLÓGICO: BAJO CONTROL]"
    alert_msg = (
        f"La tasa de incidencia de {inc_rate:.1f} por 100,000 habitantes se mantiene dentro de los percentiles "
        "históricos esperados para el período analizado."
    )

st.markdown(
    f\"\"\"
    <div class="clinical-alert {alert_class}">
        <strong>{alert_code}</strong> — {alert_msg}
    </div>
    \"\"\",
    unsafe_allow_html=True,
)"""

section3_replacement = """# ==============================================================================
# 3. EVALUACIÓN Y SEMÁFORO DE ALERTA SANITARIA — CANAL ENDÉMICO BORTMAN (OPS/MINSA)
# ==============================================================================
inc_rate = kpis["cases_rate"]
bortman_eval = compute_bortman_corridor(
    df_filtered, f"cases_rate_{group_key}", target_value=inc_rate
)

if bortman_eval["zone_code"] == "EPIDEMIA":
    alert_class = "clinical-alert-danger"
    alert_badge_title = "[CANAL BORTMAN OPS: ZONA DE EPIDEMIA / BROTE CRÍTICO]"
elif bortman_eval["zone_code"] == "ALARMA":
    alert_class = "clinical-alert-warning"
    alert_badge_title = "[CANAL BORTMAN OPS: ZONA DE ALARMA / VIGILANCIA INTENSIVA]"
elif bortman_eval["zone_code"] == "SEGURIDAD":
    alert_class = "clinical-alert-normal"
    alert_badge_title = "[CANAL BORTMAN OPS: ZONA DE SEGURIDAD / COMPORTAMIENTO ESPERADO]"
else:
    alert_class = "clinical-alert-normal"
    alert_badge_title = "[CANAL BORTMAN OPS: ZONA DE ÉXITO / CONTROL ÓPTIMO]"

st.markdown(
    f\"\"\"
    <div class="clinical-alert {alert_class}" data-testid="bortman-alert" style="border-left-color: {bortman_eval['zone_color']};">
        <div style="font-weight: 700; font-size: 0.95rem; margin-bottom: 4px; color: {bortman_eval['zone_color']};">
            {alert_badge_title}
        </div>
        <div style="font-size: 0.9rem; line-height: 1.45;">
            Tasa actual: <strong>{inc_rate:.1f} por 100k hab.</strong> (Umbral Epidémico Q3: <strong>{bortman_eval['q3']:.1f}</strong> | Mediana Q2: <strong>{bortman_eval['q2']:.1f}</strong> | Cuartil Éxito Q1: <strong>{bortman_eval['q1']:.1f}</strong>).
            <br>
            <em>Directiva OPS/MINSA:</em> {bortman_eval['recommendation']}
        </div>
    </div>
    \"\"\",
    unsafe_allow_html=True,
)"""

assert section3_target in content, "Section 3 target not found"
content = content.replace(section3_target, section3_replacement, 1)

# 5. Add data-testid to the 4 KPI cards
content = content.replace('<div class="kpi-card">\n            <div class="kpi-label">Casos Diagnosticados', '<div class="kpi-card" data-testid="kpi-card-cases">\n            <div class="kpi-label">Casos Diagnosticados')
content = content.replace('<div class="kpi-card">\n            <div class="kpi-label">Tasa Incidencia x 100k hab.', '<div class="kpi-card" data-testid="kpi-card-rate">\n            <div class="kpi-label">Tasa Incidencia x 100k hab.')
content = content.replace('<div class="kpi-card">\n            <div class="kpi-label">Tasa de Hospitalización (HR)', '<div class="kpi-card" data-testid="kpi-card-hr">\n            <div class="kpi-label">Tasa de Hospitalización (HR)')
content = content.replace('<div class="kpi-card">\n            <div class="kpi-label">Tasa de Letalidad (CFR)', '<div class="kpi-card" data-testid="kpi-card-cfr">\n            <div class="kpi-label">Tasa de Letalidad (CFR)')

# 6. Enhance Tab I with the Bortman Corridor Visualization
tab1_marker = """        st.download_button(
            label="Descargar Serie Consolidada (.CSV)",
            data=csv_data,
            file_name=f"reporte_epidemiologico_{group_key}_{scope_title.lower().replace(' ', '_')}.csv",
            mime="text/csv",
        )"""

tab1_addition = """        st.download_button(
            label="Descargar Serie Consolidada (.CSV)",
            data=csv_data,
            file_name=f"reporte_epidemiologico_{group_key}_{scope_title.lower().replace(' ', '_')}.csv",
            mime="text/csv",
        )

    st.markdown("---")
    st.markdown(f"#### Canal Endémico de Bortman (Normativa Técnica OPS/MINSA) — {scope_title}")
    st.caption(
        "Herramienta canónica de epidemiología para delimitar zonas de comportamiento: "
        "Éxito (<Q1), Seguridad (Q1-Q2), Alarma (Q2-Q3) y Epidemia (>=Q3)."
    )

    q1_val, q2_val, q3_val = bortman_eval["q1"], bortman_eval["q2"], bortman_eval["q3"]
    max_y = max(float(df_filtered[f"cases_rate_{group_key}"].max()) * 1.15, q3_val * 1.35)

    fig_bortman = go.Figure()

    # Zonas de fondo
    years_x = df_filtered["year"].tolist()
    if len(years_x) > 1:
        x_bounds = [years_x[0], years_x[-1]]

        # Zona Epidemia (Q3 a max)
        fig_bortman.add_shape(
            type="rect", x0=x_bounds[0], x1=x_bounds[1], y0=q3_val, y1=max_y,
            fillcolor="rgba(254, 226, 226, 0.45)", line_width=0, layer="below"
        )
        # Zona Alarma (Q2 a Q3)
        fig_bortman.add_shape(
            type="rect", x0=x_bounds[0], x1=x_bounds[1], y0=q2_val, y1=q3_val,
            fillcolor="rgba(254, 243, 199, 0.45)", line_width=0, layer="below"
        )
        # Zona Seguridad (Q1 a Q2)
        fig_bortman.add_shape(
            type="rect", x0=x_bounds[0], x1=x_bounds[1], y0=q1_val, y1=q2_val,
            fillcolor="rgba(220, 252, 231, 0.45)", line_width=0, layer="below"
        )
        # Zona Éxito (0 a Q1)
        fig_bortman.add_shape(
            type="rect", x0=x_bounds[0], x1=x_bounds[1], y0=0, y1=q1_val,
            fillcolor="rgba(224, 242, 254, 0.45)", line_width=0, layer="below"
        )

    # Líneas de umbral
    fig_bortman.add_trace(go.Scatter(
        x=[years_x[0], years_x[-1]], y=[q3_val, q3_val],
        mode="lines", name=f"Q3 Umbral Epidémico ({q3_val:.1f})",
        line=dict(color="#b91c1c", width=1.5, dash="dash")
    ))
    fig_bortman.add_trace(go.Scatter(
        x=[years_x[0], years_x[-1]], y=[q2_val, q2_val],
        mode="lines", name=f"Q2 Mediana Histórica ({q2_val:.1f})",
        line=dict(color="#d97706", width=1.5, dash="dot")
    ))
    fig_bortman.add_trace(go.Scatter(
        x=[years_x[0], years_x[-1]], y=[q1_val, q1_val],
        mode="lines", name=f"Q1 Límite de Éxito ({q1_val:.1f})",
        line=dict(color="#0284c7", width=1.5, dash="dot")
    ))

    # Curva observada
    fig_bortman.add_trace(go.Scatter(
        x=df_filtered["year"], y=df_filtered[f"cases_rate_{group_key}"],
        mode="lines+markers", name="Incidencia Observada",
        line=dict(color="#0f172a", width=3),
        marker=dict(size=7, color="#0f172a")
    ))

    fig_bortman.update_layout(
        title="Corredor Endémico de Bortman: Zonas Epidemiológicas y Desempeño Histórico",
        xaxis_title="Año Epidemiológico",
        yaxis_title="Tasa de Incidencia x 100k hab.",
        template="plotly_white",
        hovermode="x unified",
        margin=dict(l=20, r=20, t=40, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig_bortman, use_container_width=True)

    # Panel de síntesis Bortman
    col_bort1, col_bort2, col_bort3, col_bort4 = st.columns(4)
    with col_bort1:
        st.markdown(f'''
        <div class="bortman-quartile-card" style="border-top: 3px solid #0284c7;">
            <div class="bortman-q-label">Cuartil 1 (Éxito)</div>
            <div class="bortman-q-val">{q1_val:.1f}</div>
            <div style="font-size: 0.72rem; color: #64748b;">Incidencia mínima esperada</div>
        </div>
        ''', unsafe_allow_html=True)
    with col_bort2:
        st.markdown(f'''
        <div class="bortman-quartile-card" style="border-top: 3px solid #15803d;">
            <div class="bortman-q-label">Cuartil 2 (Mediana)</div>
            <div class="bortman-q-val">{q2_val:.1f}</div>
            <div style="font-size: 0.72rem; color: #64748b;">Límite zona seguridad</div>
        </div>
        ''', unsafe_allow_html=True)
    with col_bort3:
        st.markdown(f'''
        <div class="bortman-quartile-card" style="border-top: 3px solid #d97706;">
            <div class="bortman-q-label">Cuartil 3 (Alarma)</div>
            <div class="bortman-q-val">{q3_val:.1f}</div>
            <div style="font-size: 0.72rem; color: #64748b;">Umbral epidémico superior</div>
        </div>
        ''', unsafe_allow_html=True)
    with col_bort4:
        st.markdown(f'''
        <div class="bortman-quartile-card" style="border-top: 3px solid {bortman_eval['zone_color']}; background: {bortman_eval['zone_bg']};">
            <div class="bortman-q-label" style="color: {bortman_eval['zone_color']};">Estado Actual ({latest_year})</div>
            <div class="bortman-q-val" style="color: {bortman_eval['zone_color']};">{bortman_eval['zone_name']}</div>
            <div style="font-size: 0.72rem; color: {bortman_eval['zone_color']}; font-weight: 600;">{inc_rate:.1f} x 100k hab.</div>
        </div>
        ''', unsafe_allow_html=True)"""

assert tab1_marker in content, "Tab 1 marker not found"
content = content.replace(tab1_marker, tab1_addition, 1)

# 7. Enhance Tab II with Manchester Triage & Hospital Critical Demand
tab2_marker = "st.plotly_chart(fig_scatter, use_container_width=True)"
tab2_addition = """st.plotly_chart(fig_scatter, use_container_width=True)

    st.markdown("---")
    st.markdown("#### Monitor de Triaje de Emergencias Manchester y Demanda Crítica (UCI / Oxígeno)")
    st.caption(
        "Modelado de distribución de gravedad hospitalaria conforme al Sistema de Triaje Manchester (MTS) "
        "y estimación de requerimientos logísticos de soporte vital para la cohorte seleccionada."
    )

    manchester_data = compute_manchester_and_resources(kpis["hospitalizations"], kpis["cases"], group=group_key)

    col_m1, col_m2, col_m3 = st.columns(3)
    with col_m1:
        st.markdown(f'''
        <div class="manchester-card" style="border-left: 4px solid #b91c1c;">
            <div style="font-size: 0.78rem; font-weight: 700; color: #b91c1c; text-transform: uppercase;">
                Demanda Proyectada Camas UCI
            </div>
            <div style="font-size: 1.8rem; font-weight: 700; color: #0f172a; margin: 4px 0;">
                {manchester_data["icu_beds_estimated"]} <span style="font-size: 0.95rem; font-weight: 500; color: #64748b;">camas</span>
            </div>
            <div style="font-size: 0.8rem; color: #475569;">
                Basado en {int(kpis["hospitalizations"]):,} internamientos anuales ({'10%' if group_key=='men5' else '16%'} gravedad UCI).
            </div>
        </div>
        ''', unsafe_allow_html=True)
    with col_m2:
        st.markdown(f'''
        <div class="manchester-card" style="border-left: 4px solid #0284c7;">
            <div style="font-size: 0.78rem; font-weight: 700; color: #0284c7; text-transform: uppercase;">
                Consumo Diario Oxígeno Medicinal
            </div>
            <div style="font-size: 1.8rem; font-weight: 700; color: #0f172a; margin: 4px 0;">
                {manchester_data["oxygen_demand_m3_day"]} <span style="font-size: 0.95rem; font-weight: 500; color: #64748b;">m³/día</span>
            </div>
            <div style="font-size: 0.8rem; color: #475569;">
                Equivalente a <strong>{manchester_data["oxygen_cylinders_10m3_day"]} balones</strong> de 10 m³ por día calendario.
            </div>
        </div>
        ''', unsafe_allow_html=True)
    with col_m3:
        st.markdown(f'''
        <div class="manchester-card" style="border-left: 4px solid #d97706;">
            <div style="font-size: 0.78rem; font-weight: 700; color: #d97706; text-transform: uppercase;">
                Oxigenoterapia en Hospitalización
            </div>
            <div style="font-size: 1.8rem; font-weight: 700; color: #0f172a; margin: 4px 0;">
                {manchester_data["ward_oxygen_patients"]} <span style="font-size: 0.95rem; font-weight: 500; color: #64748b;">pacientes</span>
            </div>
            <div style="font-size: 0.8rem; color: #475569;">
                Soporte de bajo/medio flujo (cánula nasal y máscara Venturi).
            </div>
        </div>
        ''', unsafe_allow_html=True)

    col_triage_chart, col_triage_table = st.columns([7, 5])
    with col_triage_chart:
        fig_triage = px.bar(
            manchester_data["triage_df"],
            x="Porcentaje",
            y="Nivel de Triaje",
            orientation="h",
            text="Pacientes Estimados",
            title=f"Distribución Estratificada de Ingresos por Triaje Manchester ({group_label})",
            labels={"Porcentaje": "Proporción de Pacientes (%)", "Nivel de Triaje": "Prioridad Manchester"},
            color="Porcentaje",
            color_continuous_scale="Reds",
        )
        fig_triage.update_traces(texttemplate="%{text:,} pactes", textposition="outside", cliponaxis=False)
        fig_triage.update_layout(template="plotly_white", margin=dict(l=20, r=40, t=40, b=20))
        st.plotly_chart(fig_triage, use_container_width=True)

    with col_triage_table:
        st.markdown("##### Prioridades de Atención Clínica")
        st.dataframe(manchester_data["triage_df"], use_container_width=True, hide_index=True)
        st.caption(
            "Tiempos objetivo MTS: Nivel 1 Resucitación (Inmediato), Nivel 2 Emergencia (10 min), "
            "Nivel 3 Urgencia (60 min), Nivel 4 Menor (120 min), Nivel 5 No Urgente (240 min)."
        )"""

assert tab2_marker in content, "Tab 2 marker not found"
content = content.replace(tab2_marker, tab2_addition, 1)

# 8. Enhance Tab III with Bioclimatic Regional Matrix (Heladas y Friaje)
tab3_marker = """        st.download_button(
            "Descargar ranking del período (.CSV)",
            data=top3_df.to_csv(index=False).encode("utf-8-sig"),
            file_name=f"ranking_top3_{group_key}_{year_range[0]}_{year_range[1]}.csv",
            mime="text/csv",
        )"""

tab3_addition = """        st.download_button(
            "Descargar ranking del período (.CSV)",
            data=top3_df.to_csv(index=False).encode("utf-8-sig"),
            file_name=f"ranking_top3_{group_key}_{year_range[0]}_{year_range[1]}.csv",
            mime="text/csv",
        )

    st.markdown("---")
    st.markdown("#### Matriz de Vulnerabilidad Bioclimática Regional (Heladas Altoandinas y Friaje Amazónico)")
    st.caption(
        "Estratificación cruzada de la tasa de incidencia epidemiológica con los factores de exposición climática "
        "extrema del territorio peruano (Heladas >3000 msnm y Fenómenos de Friaje)."
    )

    df_bioclim = compute_bioclimatic_vulnerability(data_service.get_annual_measures(), year=latest_year, group=group_key)

    col_bio_chart, col_bio_info = st.columns([7, 5])
    with col_bio_chart:
        fig_bio = px.scatter(
            df_bioclim,
            x="incidence_rate",
            y="composite_risk_score",
            color="climate_zone",
            text="department",
            size="cases",
            title=f"Índice de Riesgo Bioclimático Compuesto vs Incidencia Observada ({latest_year})",
            labels={
                "incidence_rate": "Tasa Incidencia x 100k hab.",
                "composite_risk_score": "Índice de Riesgo Compuesto",
                "climate_zone": "Zona Bioclimática",
                "cases": "Casos Totales",
            },
            color_discrete_map={
                "Heladas Altoandinas (>3000 msnm)": "#b91c1c",
                "Friaje Amazónico (Selva Baja/Alta)": "#0284c7",
                "Costa y Valles Interandinos": "#15803d",
            }
        )
        fig_bio.update_traces(textposition="top center")
        fig_bio.update_layout(template="plotly_white", margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig_bio, use_container_width=True)

    with col_bio_info:
        st.markdown("##### Top 5 Departamentos en Riesgo Bioclimático Crítico")
        st.dataframe(
            df_bioclim.head(5)[["department", "climate_zone", "incidence_rate", "composite_risk_score", "risk_tier"]].rename(
                columns={
                    "department": "Departamento",
                    "climate_zone": "Zona Climática",
                    "incidence_rate": "Tasa x 100k",
                    "composite_risk_score": "Score Riesgo",
                    "risk_tier": "Nivel de Alerta",
                }
            ),
            use_container_width=True, hide_index=True
        )
        st.markdown(
            "• **Heladas Altoandinas (Factor 1.35x):** Afectan a Puno, Cusco, Huancavelica, Pasco y Junín con estrés térmico severo y letalidad infantil.<br>"
            "• **Friaje Amazónico (Factor 1.25x):** Ingreso de masas de aire subantártico por Loreto, Ucayali y Madre de Dios con descensos de hasta 15°C en 24h.",
            unsafe_allow_html=True
        )"""

assert tab3_marker in content, "Tab 3 marker not found"
content = content.replace(tab3_marker, tab3_addition, 1)

if is_crlf:
    content = content.replace("\n", "\r\n")

app_path.write_text(content, encoding="utf-8")
print("Successfully enhanced app.py with Bortman Corridor, Manchester Triage and Bioclimatic Matrix!")
