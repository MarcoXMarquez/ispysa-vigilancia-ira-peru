# Guía Rápida de Normas ISO Implementadas

**Para quién es:** Integrantes del equipo de trabajo.  
**Objetivo:** Entender en 5 minutos qué normas ISO están en el proyecto y qué decirle al profesor si pregunta dónde están implementadas.

---

## 1. Mapa Resumen de Normas ISO en Nuestro Código

| Norma | Nombre Sencillo | ¿Para qué sirve? | ¿Dónde se ve en nuestro proyecto? |
| :--- | :--- | :--- | :--- |
| **ISO 9000:2015** | Gestión de Calidad (SGC) | Asegurar que los datos y procesos no tengan errores y se basen en evidencia real. | En el pipeline de datos: tasas estandarizadas por 100k, XGBoost con $R^2=0.935$ comprobado y prevención de división entre cero (`safe_rate`). |
| **ISO 9241-11** | Medición de Usabilidad | Que el sistema sea rápido, útil y fácil de usar. | Filtros directos de región en 2 clics, carga instantánea ($<0.2\text{s}$) con `@st.cache_resource` y botón de descarga en CSV. |
| **ISO 9241-210** | Diseño Centrado en el Humano | Que la pantalla siga la forma de pensar del médico o epidemiólogo. | Orden visual: Semáforo de alerta arriba $\to$ datos históricos $\to$ ocupación de camas (HR) y muertes (CFR) $\to$ predicciones futuras. |
| **ISO 9241-110** | Diálogo Ergonómico | Que los controles no confundan ni dejen al usuario cometer errores. | Sliders de años libres (2000-2023), textos de ayuda (`help`) en cada botón y glosario de fórmulas al final de la página. |
| **ISO 9241-12** | Presentación Visual | Que la pantalla sea limpia, legible y sin adornos molestos. | Diseño formal estilo MINSA (sin textos en movimiento continuo ni bordes neón), semáforo claro y colores aptos para personas con daltonismo. |
| **ISO/IEC 25010** | Calidad del Producto Software | Que el código esté bien programado, sea fácil de mantener y no se caiga. | Lógica separada en servicios (`src/services/`), 12 pruebas unitarias automatizadas con **88% de cobertura** y candado en GitHub Actions. |

---

## 2. ¿Cómo responderle al profesor sobre cada norma?

* **Si pregunta por ISO 9000:2015:**  
  *"Profesor, aplicamos los principios de ISO 9000: enfoque al cliente (médicos del MINSA), enfoque a procesos (flujo ordenado desde los CSVs hasta la pantalla), toma de decisiones basada en evidencia (elegimos el modelo predictivo que demostró menor error y no uno al azar) y control de salidas no conformes (bloqueamos divisiones por cero y datos corruptos)."*

* **Si pregunta por la familia ISO 9241 (Usabilidad y UI):**  
  *"Profesor, diseñamos el dashboard en Streamlit bajo ISO 9241. La parte 11 garantiza rapidez con caché; la 210 ordena la pantalla según el flujo clínico; la 110 explica las fórmulas con un glosario; y la 12 cuida los colores sobrios, el contraste y elimina distracciones visuales."*

* **Si pregunta por ISO/IEC 25010:**  
  *"Profesor, garantizamos la mantenibilidad desacoplando el código en capas de servicios y aseguramos la fiabilidad con 12 pruebas unitarias que cubren el 88% del código y corren solas en GitHub Actions antes de aceptar cualquier cambio."*
