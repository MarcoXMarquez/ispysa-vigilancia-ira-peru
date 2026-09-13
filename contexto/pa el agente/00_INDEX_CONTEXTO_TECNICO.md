# Manual de Contexto Técnico para Agentes de IA

**Proyecto:** Plataforma de Vigilancia Epidemiológica de Infecciones Respiratorias Agudas (IRA en Perú 2000–2023)  
**Asignatura:** Calidad de Software (Teoría - `TEO-CS`) — Trabajo Parcial 2  
**Destinatario:** Agente de Inteligencia Artificial (Subagente / Peer Agent)  
**Propósito:** Proporcionar la arquitectura conceptual, matemática, normativa y de código para permitir la colaboración autónoma, generación de código, auditoría y resolución de requerimientos.

---

## 1. Topología del Proyecto y Rutas Clave

* **Raíz de Trabajo:** `c:\Users\marco\Desktop\TEO-CS\TRABAJO 2`
* **Código Fuente a Publicar en GitHub:** `TRABAJO 2\Código\ISPySA-Pneumonia-main\ISPySA-Pneumonia-main\`
* **Archivo de Presentación Principal:** `ISPySA-Pneumonia-main\ISPySA-Pneumonia-main\app.py` (Streamlit Dashboard)
* **Capa de Servicios:** `ISPySA-Pneumonia-main\ISPySA-Pneumonia-main\src\services\`
  * `data_service.py` (`EpidemiologyDataService`): Ingesta, interpolación censal, cálculo de tasas por 100k y severidad.
  * `model_service.py` (`EpidemiologyModelService`): Acceso a métricas de Machine Learning (XGBoost, Random Forest, LSTM) y proyecciones.
* **Suite de Pruebas Automatizadas:** `ISPySA-Pneumonia-main\ISPySA-Pneumonia-main\tests\test_services.py` (12 tests unitarios, 88% de cobertura).
* **Pipeline de Integración Continua (CI):** `ISPySA-Pneumonia-main\ISPySA-Pneumonia-main\.github\workflows\ci.yml` (Separado en jobs `auditoria-codigo` y `pruebas-unitarias`).

---

## 2. Índice de Documentación Normativa para el Agente

En este mismo directorio encontrarás los documentos detallados con fundamentación profunda:

1. [`01_ISO_9000_2015.md`](file:///c:/Users/marco/Desktop/TEO-CS/TRABAJO%202/contexto/pa%20el%20agente/01_ISO_9000_2015.md): Sistemas de Gestión de la Calidad aplicados al pipeline de datos y decisiones predictivas.
2. [`02_ISO_9241_11.md`](file:///c:/Users/marco/Desktop/TEO-CS/TRABAJO%202/contexto/pa%20el%20agente/02_ISO_9241_11.md): Usabilidad (Eficacia, Eficiencia mediante `@st.cache_resource` y Satisfacción).
3. [`03_ISO_9241_210.md`](file:///c:/Users/marco/Desktop/TEO-CS/TRABAJO%202/contexto/pa%20el%20agente/03_ISO_9241_210.md): Diseño Centrado en el Humano (HCD) adaptado a directores de salud pública y epidemiólogos.
4. [`04_ISO_9241_110.md`](file:///c:/Users/marco/Desktop/TEO-CS/TRABAJO%202/contexto/pa%20el%20agente/04_ISO_9241_110.md): Principios de diálogo ergonómico (adecuación a la tarea, autodescripción, control y tolerancia a fallos).
5. [`05_ISO_9241_12.md`](file:///c:/Users/marco/Desktop/TEO-CS/TRABAJO%202/contexto/pa%20el%20agente/05_ISO_9241_12.md): Presentación visual de la información y eliminación sistemática de sesgos de "AI-Slop".
6. [`06_ISO_IEC_25010.md`](file:///c:/Users/marco/Desktop/TEO-CS/TRABAJO%202/contexto/pa%20el%20agente/06_ISO_IEC_25010.md): Calidad de producto software (modularidad, fiabilidad con cobertura $\ge 80\%$ y portabilidad).
7. [`07_COMPONENTES_2_Y_3_IMPLEMENTACION.md`](file:///c:/Users/marco/Desktop/TEO-CS/TRABAJO%202/contexto/pa%20el%20agente/07_COMPONENTES_2_Y_3_IMPLEMENTACION.md): Especificación técnica para implementar el Componente 2 (informe académico y mapeo a GitHub Projects) y Componente 3 (guía Git).
8. [`08_AGILE_TUTORIAL_ARQUITECTURA_Y_USO.md`](file:///c:/Users/marco/Desktop/TEO-CS/TRABAJO%202/contexto/pa%20el%20agente/08_AGILE_TUTORIAL_ARQUITECTURA_Y_USO.md): Deconstrucción de `agile-tutorial` (IBM) y su adopción en Scrum, GitHub Flow y CI Quality Gates.
