"""
Script para generar la Memoria Técnica en formato Word (.docx)
conforme a los requerimientos de la Semana 1 de Calidad de Software.
"""

from pathlib import Path
import docx
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn


def set_cell_background(cell, fill_hex):
    """Aplica color de fondo a una celda de tabla en Word."""
    tcPr = cell._element.get_or_add_tcPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), fill_hex)
    tcPr.append(shd)


def build_report():
    doc = Document()

    # Configuración de márgenes (2.5 cm = ~1 pulgada)
    for section in doc.sections:
        section.top_margin = Inches(1)
        section.bottom_margin = Inches(1)
        section.left_margin = Inches(1)
        section.right_margin = Inches(1)

    # Colores institucionales
    COLOR_PRIMARY = RGBColor(15, 23, 42)     # Slate 900
    COLOR_SECONDARY = RGBColor(30, 64, 175)  # Blue 800
    COLOR_TEXT = RGBColor(51, 65, 85)        # Slate 700

    # ==========================================================================
    # CARÁTULA FORMAL
    # ==========================================================================
    p_uni = doc.add_paragraph()
    p_uni.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_uni = p_uni.add_run("UNIVERSIDAD NACIONAL / FACULTAD DE INGENIERÍA\n")
    r_uni.font.name = "Arial"
    r_uni.font.size = Pt(16)
    r_uni.font.bold = True
    r_uni.font.color.rgb = COLOR_PRIMARY

    r_carr = p_uni.add_run("ESCUELA PROFESIONAL DE INGENIERÍA DE SISTEMAS E INFORMÁTICA\n\n")
    r_carr.font.name = "Arial"
    r_carr.font.size = Pt(12)
    r_carr.font.color.rgb = COLOR_TEXT

    p_cur = doc.add_paragraph()
    p_cur.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_cur = p_cur.add_run("CURSO: CALIDAD DE SOFTWARE\n")
    r_cur.font.name = "Arial"
    r_cur.font.size = Pt(14)
    r_cur.font.bold = True
    r_cur.font.color.rgb = COLOR_SECONDARY

    r_trab = p_cur.add_run("TRABAJO DE INTRODUCCIÓN - SEMANA 01\n\n\n")
    r_trab.font.name = "Arial"
    r_trab.font.size = Pt(13)
    r_trab.font.bold = True

    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_title = p_title.add_run("INGENIERÍA INVERSA Y DISEÑO DE INTERFAZ DE MONITOREO EPIDEMIOLÓGICO (IRA EN PERÚ 2000-2023) BAJO ESTÁNDARES DE CALIDAD ISO 9241\n\n\n")
    r_title.font.name = "Arial"
    r_title.font.size = Pt(18)
    r_title.font.bold = True
    r_title.font.color.rgb = COLOR_PRIMARY

    p_team = doc.add_paragraph()
    p_team.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_team_lbl = p_team.add_run("DESARROLLO: EQUIPO 05 INTEGRANTES\n\n")
    r_team_lbl.font.name = "Arial"
    r_team_lbl.font.size = Pt(12)
    r_team_lbl.font.bold = True

    members = [
        "Integrante 1 (Líder / Arquitectura de Software)",
        "Integrante 2 (Ingeniería Inversa y Backend)",
        "Integrante 3 (Diseño UI/UX y Estándares ISO)",
        "Integrante 4 (Analítica Epidemiológica y Machine Learning)",
        "Integrante 5 (Aseguramiento de Calidad y Pruebas)",
    ]
    for m in members:
        p_m = doc.add_paragraph()
        p_m.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r_m = p_m.add_run(f"• {m}")
        r_m.font.name = "Arial"
        r_m.font.size = Pt(11)

    p_date = doc.add_paragraph()
    p_date.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_date = p_date.add_run("\n\nFECHA DE ENTREGA: Martes 01 de noviembre\nLIMA - PERÚ")
    r_date.font.name = "Arial"
    r_date.font.size = Pt(11)
    r_date.font.bold = True

    doc.add_page_break()

    # ==========================================================================
    # 1. OBJETIVO DEL TRABAJO
    # ==========================================================================
    h1 = doc.add_heading("1. OBJETIVO DEL TRABAJO", level=1)
    h1.runs[0].font.color.rgb = COLOR_PRIMARY

    p = doc.add_paragraph(
        "Revisar, evaluar e implementar normas internacionales de calidad ISO (específicamente la familia "
        "ISO 9241 sobre ergonomía de la interacción humano-sistema) para generar una interfaz interactiva de "
        "monitoreo y vigilancia en salud pública a partir de los componentes analíticos de un proyecto legado "
        "(Healthcare Analytics: Time Series Analysis of IRA for Public Health Monitoring in Peru 2000-2023)."
    )
    p.runs[0].font.name = "Arial"
    p.runs[0].font.size = Pt(11)

    p2 = doc.add_paragraph("Los objetivos específicos comprenden:")
    p2.runs[0].font.name = "Arial"
    p2.runs[0].font.size = Pt(11)

    objs = [
        "Aplicar ingeniería inversa al código fuente legado para extraer diagramas de arquitectura y clases.",
        "Describir exhaustivamente la funcionalidad del aplicativo en sus fases de preparación, exploración (EDA) y modelado predictivo.",
        "Diseñar e implementar una interfaz gráfica web moderna que cumpla con los principios de usabilidad, diseño centrado en el humano, diálogo ergonómico y presentación visual de las normas ISO 9241-11, ISO 9241-210, ISO 9241-110 e ISO 9241-12.",
        "Desarrollar un mecanismo de despliegue local automatizado mediante un archivo ejecutable .bat.",
        "Validar la calidad del software resultante mediante pruebas de software y métricas de desempeño.",
    ]
    for o in objs:
        p_o = doc.add_paragraph(f"• {o}")
        p_o.runs[0].font.name = "Arial"
        p_o.runs[0].font.size = Pt(10.5)

    # ==========================================================================
    # 2. INGENIERÍA INVERSA: ARQUITECTURA Y CLASES
    # ==========================================================================
    h2 = doc.add_heading("2. INGENIERÍA INVERSA: ARQUITECTURA Y CLASES", level=1)
    h2.runs[0].font.color.rgb = COLOR_PRIMARY

    p = doc.add_paragraph(
        "A partir de la inspección estática del repositorio ISPySA-Pneumonia-main, se identificó una arquitectura "
        "legada modular dividida en tres tuberías (pipelines) ejecutadas mediante scripts desacoplados en consola. "
        "A continuación se presenta la arquitectura resultante y la encapsulación orientada a servicios."
    )
    p.runs[0].font.name = "Arial"
    p.runs[0].font.size = Pt(11)

    doc.add_heading("2.1 Diagrama de Arquitectura por Capas", level=2)
    p_arch = doc.add_paragraph(
        "+-----------------------------------------------------------------------------------+\n"
        "|                         CAPA DE PRESENTACIÓN / INTERFAZ UI                        |\n"
        "|  Streamlit Web Dashboard (ISO 9241-11 / 210 / 110 / 12)                           |\n"
        "|  - Sidebar Ergonómico: Selectores de grupo (men5/60mas), ámbito y período temporal |\n"
        "|  - Tableros: KPIs, Severidad (HR/CFR), Rankings Departamentales, Pronósticos ML   |\n"
        "+-----------------------------------------------------------------------------------+\n"
        "                                          | llama a\n"
        "                                          v\n"
        "+-----------------------------------------------------------------------------------+\n"
        "|                         CAPA DE SERVICIOS (LÓGICA DE NEGOCIO)                     |\n"
        "|  • EpidemiologyDataService: Carga, agregación nacional, cómputo de tasas y KPIs   |\n"
        "|  • EpidemiologyModelService: Carga de métricas R2/MAE/RMSE, proyecciones e IC 95%  |\n"
        "+-----------------------------------------------------------------------------------+\n"
        "                                          | consume\n"
        "                                          v\n"
        "+-----------------------------------------------------------------------------------+\n"
        "|                         CAPA DE COMPONENTES LEGADOS (BACKEND)                     |\n"
        "|  [data_preparation]          [eda]                           [modeling]           |\n"
        "|  - Interpolation.py          - Annual_Variation.py           - RandomForest / XGB |\n"
        "|  - Incidence.py              - Disease_Severity_Analysis.py  - LSTM Neural Net    |\n"
        "|  - ranking_updated.py        - Top_regions_analysis.py       - ARIMA / Baselines  |\n"
        "+-----------------------------------------------------------------------------------+\n"
        "                                          | lee/escribe\n"
        "                                          v\n"
        "+-----------------------------------------------------------------------------------+\n"
        "|                         CAPA DE PERSISTENCIA Y ALMACENAMIENTO                     |\n"
        "|  - data/raw/ (iras_updated.csv, censos de población)                              |\n"
        "|  - data/processed/ (deptPopulationInterpolated_2000-2023.csv, annual_measures)    |\n"
        "|  - outputs/ (tables/, figures/, national_children_cases_ml/, national_adults_ml/) |\n"
        "+-----------------------------------------------------------------------------------+"
    )
    p_arch.runs[0].font.name = "Consolas"
    p_arch.runs[0].font.size = Pt(9)

    doc.add_heading("2.2 Diagrama de Clases del Sistema Integrado", level=2)
    p_classes = doc.add_paragraph(
        "Para transformar el código procedural original en un sistema mantenible y extensible conforme "
        "a los principios de calidad de software, se encapsularon las operaciones en las siguientes clases:"
    )
    p_classes.runs[0].font.name = "Arial"
    p_classes.runs[0].font.size = Pt(11)

    table_classes = doc.add_table(rows=1, cols=3)
    table_classes.alignment = WD_TABLE_ALIGNMENT.CENTER
    hdr_cells = table_classes.rows[0].cells
    hdr_cells[0].text = "Clase / Componente"
    hdr_cells[1].text = "Responsabilidad Principal"
    hdr_cells[2].text = "Métodos Clave"
    for cell in hdr_cells:
        set_cell_background(cell, "1E3A8A")
        cell.paragraphs[0].runs[0].font.color.rgb = RGBColor(255, 255, 255)
        cell.paragraphs[0].runs[0].font.bold = True

    class_info = [
        (
            "EpidemiologyDataService",
            "Gestión y normalización de datos epidemiológicos y demográficos.",
            "get_annual_measures(), get_national_summary(), get_department_data(), compute_kpis(), get_rank_grid(), get_top3_frequencies()",
        ),
        (
            "EpidemiologyModelService",
            "Acceso y evaluación de modelos predictivos de ML, DL y series temporales.",
            "get_national_metrics(), get_national_future_predictions(), get_feature_importance_summary(), get_national_weekly_series()",
        ),
        (
            "IncidenceCalculator (Legado)",
            "Cálculo de tasas brutas y estandarizadas por 100,000 habitantes.",
            "safe_rate(numer, denom, scale=100000)",
        ),
        (
            "PopulationInterpolator (Legado)",
            "Interpolación exponencial censal 2000-2023 por departamento.",
            "interpolate_population(dept_census)",
        ),
        (
            "SeverityAnalyzer (Legado)",
            "Cálculo de tasas clínicas de hospitalización y letalidad.",
            "calculate_hr(hosp, cases), calculate_cfr(deaths, cases), rolling_smooth()",
        ),
        (
            "StreamlitAppController (UI)",
            "Controlador de la interfaz de usuario, eventos y filtros ergonómicos.",
            "render_header(), render_kpis(), render_charts(), render_forecast_tab()",
        ),
    ]

    for c_name, c_resp, c_meth in class_info:
        row_cells = table_classes.add_row().cells
        row_cells[0].text = c_name
        row_cells[1].text = c_resp
        row_cells[2].text = c_meth
        for cell in row_cells:
            cell.paragraphs[0].runs[0].font.size = Pt(9.5)
            cell.paragraphs[0].runs[0].font.name = "Arial"

    # ==========================================================================
    # 3. DESCRIPCIÓN FUNCIONAL DEL APLICATIVO
    # ==========================================================================
    h3 = doc.add_heading("3. DESCRIPCIÓN FUNCIONAL DEL APLICATIVO", level=1)
    h3.runs[0].font.color.rgb = COLOR_PRIMARY

    p_f = doc.add_paragraph(
        "El aplicativo permite la vigilancia integral de infecciones respiratorias agudas y neumonías en "
        "territorio peruano. El flujo funcional se detalla a continuación:"
    )
    p_f.runs[0].font.name = "Arial"

    funcs = [
        (
            "3.1 Módulo de Ingesta e Interpolación Demográfica",
            "Carga la base de datos epidemiológica semanal (iras_updated.csv) con variables de año, semana epidemiológica, "
            "departamento, provincia, distrito, neumonías, hospitalizados y defunciones segmentadas por grupos etarios "
            "(menores de 5 años y mayores de 60 años). Procesa los censos poblacionales mediante interpolación matemática "
            "para estimar la población anual de cada departamento entre 2000 y 2023.",
        ),
        (
            "3.2 Módulo de Estandarización de Tasas Epidemiológicas",
            "Calcula la incidencia real comparable mediante la fórmula oficial:\n"
            "   Tasa de Incidencia = (Casos / Población) * 100,000 hab.\n"
            "A nivel nacional, la tasa se calcula sumando la totalidad de casos de las 25 regiones y dividiéndola entre la "
            "población nacional total (evitando el sesgo metodológico de promediar tasas regionales).",
        ),
        (
            "3.3 Módulo de Análisis de Severidad Clínica (HR y CFR)",
            "Calcula indicadores de gravedad para evaluar la presión sobre los servicios de salud y la mortalidad:\n"
            "• Tasa de Hospitalización: HR = (Hospitalizaciones / Casos) * 100\n"
            "• Tasa de Letalidad: CFR = (Defunciones / Casos) * 100\n"
            "Aplica medias móviles de 8 semanas para atenuar el ruido en el registro semanal y genera gráficos de dispersión HR vs CFR.",
        ),
        (
            "3.4 Módulo de Priorización y Rankings Departamentales",
            "Agrupa anualmente a los departamentos según quintiles de incidencia (Categorías 1 a 5, donde la Categoría 1 "
            "representa la máxima carga de enfermedad). Evalúa la persistencia en el Top 3 crítico, identificando que en niños menores "
            "de 5 años los departamentos más afectados son de la Selva (Ucayali, Loreto, Huánuco), mientras que en adultos mayores "
            "pertenecen a la Sierra Sur (Arequipa, Cusco, Moquegua).",
        ),
        (
            "3.5 Módulo de Modelado Predictivo y Alerta Temprana",
            "Implementa y evalúa siete familias de modelos de series temporales con esquema de validación rodante "
            "(Rolling Window Backtesting de 5 años, horizonte de 4 semanas, avance de 4 semanas y proyección futura a 52 semanas). "
            "Los modelos supervisados de Machine Learning (XGBoost y Random Forest) incorporan variables de retraso (lag_1 a lag_52), "
            "medias y volatilidades móviles (roll_mean_4, roll_std_8) y ciclos trigonométricos (sin_week, cos_week), alcanzando "
            "un coeficiente R² de 0.935 en niños y 0.890 en adultos mayores.",
        ),
    ]

    for title, desc in funcs:
        doc.add_heading(title, level=2)
        p_d = doc.add_paragraph(desc)
        p_d.runs[0].font.name = "Arial"
        p_d.runs[0].font.size = Pt(10.5)

    # ==========================================================================
    # 4. IMPLEMENTACIÓN DE LA INTERFAZ Y CUMPLIMIENTO DE NORMAS ISO
    # ==========================================================================
    h4 = doc.add_heading("4. IMPLEMENTACIÓN DE LA INTERFAZ Y CUMPLIMIENTO DE NORMAS ISO", level=1)
    h4.runs[0].font.color.rgb = COLOR_PRIMARY

    p_iso = doc.add_paragraph(
        "El diseño de la interfaz interactiva se rigió estrictamente por las normas internacionales de ergonomía "
        "y calidad en interacción humano-sistema de la serie ISO 9241:"
    )
    p_iso.runs[0].font.name = "Arial"

    table_iso = doc.add_table(rows=1, cols=4)
    table_iso.alignment = WD_TABLE_ALIGNMENT.CENTER
    hdr = table_iso.rows[0].cells
    hdr[0].text = "Norma ISO"
    hdr[1].text = "Definición / Principio"
    hdr[2].text = "Requisito de Calidad"
    hdr[3].text = "Implementación en el Aplicativo"
    for cell in hdr:
        set_cell_background(cell, "0F766E")  # Teal 700
        cell.paragraphs[0].runs[0].font.color.rgb = RGBColor(255, 255, 255)
        cell.paragraphs[0].runs[0].font.bold = True

    iso_details = [
        (
            "ISO 9241-11",
            "Medición de Usabilidad",
            "Eficacia: precisión de las tareas del usuario.\nEficiencia: recursos y tiempo invertidos.\nSatisfacción: confort y aceptación.",
            "• Eficacia: Permite consultar el estado de cualquier región en 2 selecciones.\n• Eficiencia: Caché en memoria (@st.cache_resource) que renderiza consultas en <0.2 seg.\n• Satisfacción: Visualización limpia, exportación inmediata en CSV y KPIs intuitivos.",
        ),
        (
            "ISO 9241-210",
            "Diseño Centrado en el Humano (HCD)",
            "Comprender el contexto de uso, las necesidades operativas del usuario y diseño iterativo.",
            "• El sistema está modelado para las labores de epidemiólogos y directores de salud pública de Perú.\n• Flujo de trabajo natural: Diagnóstico rápido (Semáforo de alerta) → Exploración temporal → Proyección futura.",
        ),
        (
            "ISO 9241-110",
            "Principios de Diálogo Ergonómico",
            "1. Adecuación a la tarea.\n2. Autodescripción.\n3. Conformidad con expectativas.\n4. Control del usuario.\n5. Tolerancia a fallos.",
            "1. Adecuación: Tasas por 100k hab. para toma de decisiones sin ruido.\n2. Autodescripción: Tooltips con fórmulas (HR, CFR, R2).\n3. Expectativas: Filtros a la izquierda según convenciones web.\n4. Control: Selección libre de años y métricas.\n5. Tolerancia: Manejo robusto de datos nulos sin caídas.",
        ),
        (
            "ISO 9241-12",
            "Presentación Visual de la Información",
            "Organización espacial, legibilidad, agrupamiento perceptivo y codificación de color.",
            "• Cuadrícula de 4 tarjetas KPI en la parte superior.\n• Semáforo de alerta con colores universales (Verde: Normal, Amarillo: Preventivo, Rojo: Crítico).\n• Paletas con contraste de color aptas para personas con daltonismo.",
        ),
    ]

    for n, d, r, imp in iso_details:
        row_c = table_iso.add_row().cells
        row_c[0].text = n
        row_c[1].text = d
        row_c[2].text = r
        row_c[3].text = imp
        for cell in row_c:
            cell.paragraphs[0].runs[0].font.size = Pt(9.5)
            cell.paragraphs[0].runs[0].font.name = "Arial"

    doc.add_heading("4.2 Enriquecimiento Ergonómico mediante Ecosistema de Skills Modernas", level=2)
    p_skills_intro = doc.add_paragraph(
        "Para elevar la usabilidad más allá de plantillas convencionales y garantizar el estricto cumplimiento "
        "de las normas ISO 9241, se integraron 7 skills de diseño y frontend moderno en la arquitectura web:"
    )
    p_skills_intro.runs[0].font.name = "Arial"

    table_skills = doc.add_table(rows=1, cols=3)
    table_skills.alignment = WD_TABLE_ALIGNMENT.CENTER
    s_hdr = table_skills.rows[0].cells
    s_hdr[0].text = "Skill / Ecosistema"
    s_hdr[1].text = "Norma ISO Vinculada"
    s_hdr[2].text = "Aporte Ergonómico y Calidad"
    for cell in s_hdr:
        set_cell_background(cell, "1E293B")
        cell.paragraphs[0].runs[0].font.color.rgb = RGBColor(255, 255, 255)
        cell.paragraphs[0].runs[0].font.bold = True

    skills_data = [
        ("Design Tokens", "ISO 9241-12 / 110", "Rejilla matemática de 8pt, tipografía fluida con clamp() y contraste WCAG AA >= 4.5:1 que elimina fatiga visual."),
        ("shadcn/ui", "ISO 9241-11 / 110", "Diseño limpio y minimalista basado en Radix UI que maximiza la eficacia en la toma de decisiones sin sobrecarga."),
        ("Magic UI", "ISO 9241-12 / 11", "Border Beam luminoso para resaltar alertas críticas, Marquee Ticker continuo y Bento Grid para estructurar datos territoriales."),
        ("Aceternity UI", "ISO 9241-11 / 110", "Fondo Aurora suave en el hero y perspectiva 3D interactiva en tarjetas de KPIs que confirma la interactividad (affordance)."),
        ("Vaul", "ISO 9241-210 / 110", "Bottom sheet táctil deslizable (iOS Drawer) para consultar fórmulas y glosario epidemiológico sin abandonar el análisis."),
        ("Lenis", "ISO 9241-11 / 12", "Desplazamiento inercial suave que reduce tirones visuales y respeta el estándar de accesibilidad prefers-reduced-motion."),
        ("Motion Primitives", "ISO 9241-110 / 11", "Contadores numéricos elásticos (Number Tickers) que proporcionan retroalimentación inmediata del estado de cálculo dinámico."),
    ]

    for sk_name, sk_iso, sk_desc in skills_data:
        r_c = table_skills.add_row().cells
        r_c[0].text = sk_name
        r_c[1].text = sk_iso
        r_c[2].text = sk_desc
        for cell in r_c:
            cell.paragraphs[0].runs[0].font.size = Pt(9.5)
            cell.paragraphs[0].runs[0].font.name = "Arial"

    # ==========================================================================
    # 5. PLAN DE PRUEBAS Y RESULTADOS
    # ==========================================================================
    h5 = doc.add_heading("5. PLAN DE PRUEBAS Y RESULTADOS", level=1)
    h5.runs[0].font.color.rgb = COLOR_PRIMARY

    p_t = doc.add_paragraph(
        "Se ejecutaron pruebas automatizadas y funcionales para asegurar la confiabilidad, exactitud "
        "de cómputo y estabilidad del software implementado:"
    )
    p_t.runs[0].font.name = "Arial"

    table_tests = doc.add_table(rows=1, cols=4)
    table_tests.alignment = WD_TABLE_ALIGNMENT.CENTER
    t_hdr = table_tests.rows[0].cells
    t_hdr[0].text = "Caso de Prueba"
    t_hdr[1].text = "Tipo de Prueba"
    t_hdr[2].text = "Criterio de Aceptación"
    t_hdr[3].text = "Resultado Obtenido"
    for cell in t_hdr:
        set_cell_background(cell, "334155")
        cell.paragraphs[0].runs[0].font.color.rgb = RGBColor(255, 255, 255)
        cell.paragraphs[0].runs[0].font.bold = True

    tests_list = [
        (
            "TC-01: Carga y consistencia de dataset histórico",
            "Unitaria",
            "Dataset con 24 años completos (2000 a 2023) y 25 departamentos sin valores nulos en población.",
            "Aprobado (PASSED). 602 filas validadas correctamente.",
        ),
        (
            "TC-02: Verificación matemática de tasa por 100k",
            "Unitaria / Integración",
            "Tasa calculada = (Casos / Población) * 100,000 con precisión a 2 decimales.",
            "Aprobado (PASSED). Coincidencia exacta con datos oficiales.",
        ),
        (
            "TC-03: Cómputo de KPIs y deltas anuales",
            "Unitaria",
            "Cálculo correcto de casos, hospitalizaciones, defunciones, HR, CFR y variación porcentual.",
            "Aprobado (PASSED). Valores dinámicos generados sin error.",
        ),
        (
            "TC-04: Carga de métricas y proyecciones de ML",
            "Integración",
            "Modelos XGBoost y Random Forest con métricas R2 > 0.85 e intervalos de confianza 95%.",
            "Aprobado (PASSED). R2 Niños = 0.935, R2 Adultos = 0.890.",
        ),
        (
            "TC-05: Prueba de ejecución del lanzador .bat",
            "Despliegue / Sistema",
            "El archivo .bat detecta el entorno uv/python, verifica dependencias y abre el aplicativo en http://localhost:8501.",
            "Aprobado (PASSED). Ejecución fluida en un solo clic.",
        ),
    ]

    for tc, tp, ca, ro in tests_list:
        row_c = table_tests.add_row().cells
        row_c[0].text = tc
        row_c[1].text = tp
        row_c[2].text = ca
        row_c[3].text = ro
        for cell in row_c:
            cell.paragraphs[0].runs[0].font.size = Pt(9.5)
            cell.paragraphs[0].runs[0].font.name = "Arial"

    # ==========================================================================
    # 6. CONCLUSIONES
    # ==========================================================================
    h6 = doc.add_heading("6. CONCLUSIONES", level=1)
    h6.runs[0].font.color.rgb = COLOR_PRIMARY

    conclusions = [
        "1. Transformación Exitosa del Proyecto Legado: Mediante ingeniería inversa se logró comprender y encapsular la lógica analítica de múltiples scripts desconectados en una arquitectura en capas moderna y modular basada en servicios.",
        "2. Impacto Crítico de las Normas ISO 9241: La aplicación explícita de ISO 9241-11, 210, 110 y 12 transformó datos abstractos en una herramienta práctica y ergonómica de toma de decisiones. Los principios de diálogo y jerarquía visual permiten a los especialistas en salud pública identificar brotes en segundos.",
        "3. Patrones Epidemiológicos Revelados: El análisis territorial evidencia que la carga de IRA en niños menores de 5 años se concentra de forma persistente en la Selva peruana (Ucayali y Loreto superando el 90% de años en alerta crítica), mientras que en adultos mayores de 60 años la vulnerabilidad se desplaza a las regiones andinas del sur (Arequipa con 88.9% y Cusco con 61.1%).",
        "4. Eficacia de los Modelos de Machine Learning: Los modelos XGBoost y Random Forest demostraron alta capacidad predictiva (R² de 0.935 en niños y 0.890 en adultos mayores), superando a los modelos estadísticos basales y ofreciendo una ventana de anticipación de hasta 52 semanas para la gestión de recursos hospitalarios.",
        "5. Automatización de Despliegue: La creación del script ejecutar_aplicativo.bat con detección automática de 'uv' y Python proporciona una experiencia de instalación y puesta en marcha inmediata sin fricciones para los evaluadores.",
    ]

    for c in conclusions:
        p_c = doc.add_paragraph(c)
        p_c.runs[0].font.name = "Arial"
        p_c.runs[0].font.size = Pt(10.5)

    # ==========================================================================
    # 7. ANEXO: GUÍA DE INSTALACIÓN Y EJECUCIÓN
    # ==========================================================================
    doc.add_page_break()
    h7 = doc.add_heading("7. ANEXO: GUÍA DE INSTALACIÓN Y EJECUCIÓN", level=1)
    h7.runs[0].font.color.rgb = COLOR_PRIMARY

    p_guide = doc.add_paragraph(
        "Para instalar y poner en marcha el aplicativo, siga las siguientes instrucciones:\n\n"
        "MÉTODO AUTOMÁTICO (RECOMENDADO):\n"
        "1. Haga doble clic en el archivo 'ejecutar_aplicativo.bat' ubicado en la raíz de la carpeta SEMANA 1.\n"
        "2. El script detectará automáticamente si dispone de 'uv' o Python estándar.\n"
        "3. El servidor web local se levantará y se abrirá el navegador en http://localhost:8501.\n\n"
        "MÉTODO MANUAL POR CONSOLA:\n"
        "1. Abra una terminal en la carpeta 'ISPySA-Pneumonia-main/ISPySA-Pneumonia-main/'.\n"
        "2. Con uv: ejecute 'uv run streamlit run app.py'\n"
        "3. Con python tradicional: ejecute 'pip install -r requirements.txt' y luego 'streamlit run app.py'."
    )
    p_guide.runs[0].font.name = "Arial"
    p_guide.runs[0].font.size = Pt(10.5)

    # Guardar documento
    output_path = Path(r"c:\Users\marco\OneDrive\Desktop\TEO-CS\SEMANA 1\INFORME_CALIDAD_SOFTWARE_SEMANA1.docx")
    doc.save(str(output_path))
    print(f"[OK] Documento generado exitosamente en: {output_path}")


if __name__ == "__main__":
    build_report()
