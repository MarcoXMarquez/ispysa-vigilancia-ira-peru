# Guía de Ejecución de Demostración — Trabajo Parcial 6 (TP-6)
**Curso:** Calidad de Software (UNSA - 2026-B)  
**Proyecto:** ISPySA-Pneumonia (Vigilancia Epidemiológica de Salud Pública)  
**Líder de Proyecto:** Marco Antonio Marquez Herrera  

Esta carpeta contiene los scripts ejecutables en formato `.bat` para realizar la demostración interactiva y automatizada de todos los requisitos exigidos para el **Trabajo Parcial 6 (Aplicación de la Norma ISO/IEC 25010 mediante el Modelo GQM de la UNLP)**.

---

## 🚀 Script Principal Recomendado (Menú Interactivo)

Simplemente haz doble clic en:
👉 **`0_MENU_DEMOSTRACION_TP6.bat`**

Este menú permite elegir de forma interactiva cualquiera de las evaluaciones y demostraciones del proyecto.

---

## 📋 Catálogo de Scripts Disponibles

| Archivo `.bat` | Descripción Técnica | Estándar / Herramienta |
|---|---|---|
| **`0_MENU_DEMOSTRACION_TP6.bat`** | **Menú interactivo central.** Permite lanzar todas las demostraciones desde una única consola. | Menú Maestro |
| **`1_EJECUTAR_APP_STREAMLIT.bat`** | Levanta el servidor local de Streamlit y abre automáticamente `http://localhost:8501` en el navegador, posicionando la pestaña de *Calidad del producto (ISO 25010)* con el radar interactivo. | Streamlit / ISO 25010 |
| **`2_EJECUTAR_AUDITORIA_CALIDAD_ISO25010.bat`** | Ejecuta el motor computacional GQM (`scripts/run_quality_audit.py`), evaluando las 54 preguntas operacionales del modelo UNLP y generando `data/quality/last_audit.json`. | ISO/IEC 25010 / GQM UNLP |
| **`3_EJECUTAR_PRUEBAS_UNITARIAS.bat`** | Ejecuta la suite completa de **105 pruebas unitarias** en `tests/` con reporte detallado de aserciones. | `unittest` (100% OK) |
| **`4_VERIFICAR_QUALITY_GATES_COBERTURA_Y_LINT.bat`** | Mide la cobertura de código en `src/` (umbral exigido $\ge 80\%$, obtenido **$93.1\%$**) y ejecuta el análisis estático Flake8 (cero errores, $v(G) \le 12$). | `coverage` / `flake8` / ISO 5055 |
| **`5_EJECUTAR_PRUEBAS_E2E_PLAYWRIGHT.bat`** | Ejecuta el protocolo de 3 corridas consecutivas en Playwright sobre la aplicación en vivo y la auditoría de accesibilidad con `axe-core`. | Playwright / WCAG 2.1 AA |
| **`6_ABRIR_ENTREGABLES_TP6.bat`** | Abre el Informe Técnico formal (DOCX / PDF) y la Presentación de diapositivas en inglés (PPTX / PDF) en la carpeta `TP-6/`. | Informes y Diapositivas |

---

## ⚙️ Requisitos de Entorno en Windows
* **Opción A (Recomendada):** Tener instalado [`uv`](https://astral.sh/uv) (`powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"`). Los scripts descargarán y aislarán automáticamente todas las dependencias requeridas.
* **Opción B (Python tradicional):** Tener instalado Python 3.10 o superior añadido al PATH con las librerías de `requirements.txt` y `requirements-dev.txt`.
