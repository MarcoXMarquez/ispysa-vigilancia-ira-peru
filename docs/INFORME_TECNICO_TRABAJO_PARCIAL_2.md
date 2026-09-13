# Adopción de la Norma ISO 9000:2015 y el Marco Ágil IBM en una Plataforma de Vigilancia Epidemiológica de Salud Pública

**Curso:** Calidad de Software (Teoría - `TEO-CS`) — Trabajo Parcial 2  
**Institución:** Universidad Nacional de San Agustín de Arequipa (UNSA)  
**Facultad:** Facultad de Ingeniería de Producción y Servicios  
**Escuela:** Escuela Profesional de Ingeniería de Sistemas (EPIS)  
**Docente:** Mg. Jesús Martín Silva Fernández  
**Despliegue Cloud en Producción:** [https://ispysa-vigilancia-ira-peru.onrender.com/](https://ispysa-vigilancia-ira-peru.onrender.com/)  
**Repositorio Oficial en GitHub:** [https://github.com/MarcoXMarquez/ispysa-vigilancia-ira-peru](https://github.com/MarcoXMarquez/ispysa-vigilancia-ira-peru)  

---

### Autores (Equipo de Ingeniería - Formato IEEE):

1. **Leonardo Ruben Arce Mayhua**  
   *Universidad Nacional de San Agustín — Arequipa, Perú*  
   *Rol Scrum:* Data Engineer / Backend Lead | *GitHub:* `@Larcem` | *Correo:* `larcem@unsa.edu.pe`
2. **Joel Isaias Condori Leon**  
   *Universidad Nacional de San Agustín — Arequipa, Perú*  
   *Rol Scrum:* Product Owner & Experto de Dominio Clínico | *GitHub:* `@YoelLeon` | *Correo:* `jcondorile@unsa.edu.pe`
3. **Marco Antonio Marquez Herrera**  
   *Universidad Nacional de San Agustín — Arequipa, Perú*  
   *Rol Scrum:* Scrum Master & QA/DevOps Lead | *GitHub:* `@MarcoXMarquez` | *Correo:* `mmarquezhe@unsa.edu.pe`
4. **Rafael Diego Nina Calizaya**  
   *Universidad Nacional de San Agustín — Arequipa, Perú*  
   *Rol Scrum:* Frontend & UX Engineer (ISO 9241) | *GitHub:* `@DrN25` | *Correo:* `rninacal@unsa.edu.pe`
5. **Jeremy Joshua Perez Huamani**  
   *Universidad Nacional de San Agustín — Arequipa, Perú*  
   *Rol Scrum:* Machine Learning Engineer | *GitHub:* `@jperezh04` | *Correo:* `jperezhua@unsa.edu.pe`

---

## Resumen

El presente informe técnico expone la convergencia metodológica entre el marco normativo internacional de gestión de la calidad ISO 9000:2015 [1], las directrices de ergonomía visual e interacción humano-sistema ISO 9241 [3], el modelo de calidad de producto software ISO/IEC 25010 [2], y las prácticas de ingeniería ágil promovidas por el repositorio referencial `agile-tutorial` de IBM [7]. Esta integración se materializó sobre la plataforma de analítica y vigilancia epidemiológica `ISPySA-Pneumonia`, orientada al monitoreo de Infecciones Respiratorias Agudas (IRA) en el Perú durante la serie temporal 2000–2023 [8]. Se adoptaron principios esenciales como el enfoque a procesos, la toma de decisiones basada en la evidencia (demostrada mediante validación matemática de algoritmos predictivos XGBoost con $R^2 = 0.935$ [9]) y el control de salidas no conformes mediante funciones defensivas (`safe_rate`). Asimismo, se estructuró un proceso ágil Scrum quincenal gobernado bajo el modelo de ramificación GitHub Flow, con un pipeline de Integración Continua (CI) en GitHub Actions que desacopla la auditoría estática (`flake8`) de la ejecución de pruebas unitarias, estableciendo un Quality Gate riguroso del 80% que alcanzó un 88% de cobertura real [5], [6]. La gestión del proyecto se orquestó sinérgicamente mediante GitHub Projects v2 y ZenHub [10], asegurando la trazabilidad de 3 Épicas y 9 Historias de Usuario bajo una matriz RACI de cinco integrantes, culminando con el despliegue automatizado continuo en la infraestructura cloud de Render.

**Palabras Clave—** *ISO 9000:2015, Scrum, agile-tutorial IBM, GitHub Flow, CI/CD Quality Gate, ZenHub, Vigilancia Epidemiológica, IRA Perú, Cobertura de Código.*

---

## I. INTRODUCCIÓN Y CONTEXTO DEL SISTEMA

Las Infecciones Respiratorias Agudas (IRA) y la neumonía constituyen la principal causa de morbimortalidad infantil (menores de 5 años) y geriátrica (adultos de 60 años a más) en el sistema de salud pública del Perú [8]. La toma de decisiones de asignación de camas UCI, oxígeno medicinal y vacunación estacional por parte de las Direcciones Regionales de Salud (DIRESA) y el Ministerio de Salud (MINSA) requiere plataformas computacionales que garanticen absoluta integridad matemática, trazabilidad histórica y alta disponibilidad.

Bajo este escenario, el Trabajo Parcial 2 del curso de Calidad de Software exige la evolución de la plataforma analítica `ISPySA-Pneumonia`, transitando desde un aplicativo funcional local hacia un sistema certificado bajo estándares internacionales de calidad de proceso y producto. Para ello, se articuló de manera formal la norma ISO 9000:2015 [1] con las prácticas de desarrollo colaborativo del repositorio `agile-tutorial` de IBM [7], desplegando la solución en el entorno cloud Render (disponible en: `https://ispysa-vigilancia-ira-peru.onrender.com/`).

---

## II. REVISIÓN, SELECCIÓN Y ADOPCIÓN DE CARACTERÍSTICAS DE LA NORMA ISO 9000:2015 Y AGILE-TUTORIAL (PUNTO 1)

### A. Fundamentos y Principios de la Norma ISO 9000:2015 Adoptados en el Proyecto

La norma internacional ISO 9000:2015 define los fundamentos y vocabulario de los sistemas de gestión de la calidad [1]. En lugar de una adopción meramente burocrática, el equipo seleccionó e instrumentó cuatro principios esenciales directamente en la arquitectura y código de la plataforma:

| Principio / Cláusula ISO | Definición Formal ISO 9000:2015 | Materialización en ISPySA-Pneumonia |
| :--- | :--- | :--- |
| **Enfoque al Cliente**<br>*(Cláusula 2.3.1)* | El éxito sostenido se alcanza atrayendo y reteniendo la confianza de los clientes. | El usuario objetivo es el epidemiólogo de campo. La interfaz sustituye tablas crudas por un semáforo clínico de alerta temprana (Éxito, Seguridad, Alarma, Epidemia) y segmentación por cohortes vulnerables (`< 5 años` y `60+ años`). |
| **Enfoque a Procesos**<br>*(Cláusula 2.3.4)* | Resultados coherentes y previsibles se alcanzan cuando las actividades se entienden y gestionan como procesos interrelacionados. | Cadena de valor de datos determinista: `Ingesta de CSVs históricos (2000–2023) -> Interpolación censal INEI -> Normalización de tasas x 100k hab. -> Inferencia predictiva ML -> Renderizado en Dashboard`. |
| **Toma de Decisiones Basada en Evidencia**<br>*(Cláusula 2.3.6)* | Las decisiones basadas en el análisis y la evaluación de datos tienen mayor probabilidad de producir los resultados deseados. | La selección del modelo predictivo oficial no fue heurística: se evaluaron empíricamente Random Forest, LSTM y XGBoost, seleccionando este último por evidencia matemática comprobable ($R^2 = 0.935$, RMSE mínimo con backtesting de 5 años) [9]. |
| **Control de Salidas No Conformes**<br>*(Cláusula 3.10.1)* | Identificación y control de elementos que no cumplen con los requisitos para prevenir su uso o entrega no intencional. | Implementación de funciones defensivas como `safe_rate()`, que previenen caídas del sistema, infinitos o divisiones por cero ante regiones sin censo o valores faltantes, retornando `0.0` de forma controlada. |

### B. Ergonomía Visual (ISO 9241) y Calidad del Producto Software (ISO/IEC 25010)

Complementando a la ISO 9000, la interfaz se rediseñó bajo la norma ISO 9241-11 (Eficacia, Eficiencia y Satisfacción del usuario) [3] y la ISO 9241-210 (Diseño centrado en el operador humano) [4]. Se erradicaron los clichés propios de interfaces genéricas generadas por inteligencia artificial (*AI-Slop*), tales como marquesinas deslizantes (*tickers*) con animaciones innecesarias y controles flotantes invasivos. En su reemplazo, se implementó una estructura sobria de tres columnas ejecutivas, tipografía sans-serif con alto contraste y una Ficha Técnica formal con fórmulas epidemiológicas normalizadas por el MINSA [8].

Desde la perspectiva de ISO/IEC 25010 [2], se aseguraron las características de Adecuación Funcional, Fiabilidad (tolerancia a fallos), Usabilidad (reconocibilidad) y Mantenibilidad (modularidad y comprobabilidad analítica mediante tests).

> [!NOTE]
> 📷 **[FIGURA 1: PLACEHOLDER DE CAPTURA - INTERFAZ INSTITUCIONAL Y SEMÁFORO EPIDEMIOLÓGICO EN RENDER]**  
> **Instrucciones para la captura:** Tomar captura de pantalla completa de la aplicación en producción en Render (`https://ispysa-vigilancia-ira-peru.onrender.com/`) en modo claro. La captura debe mostrar el encabezado ministerial, el resumen ejecutivo de 3 columnas (Casos Acumulados, Incidencia x 100k hab., y Letalidad CFR) y el mapa o gráfico epidemiológico departamental sin animaciones infantiles.

### C. Deconstrucción y Adopción del Repositorio agile-tutorial de IBM

El repositorio `agile-tutorial` de IBM [7] fue concebido para instruir a ingenieros en el desarrollo cloud nativo en Python. Nuestro equipo analizó su estructura técnica y adoptó los siguientes patrones arquitecturales:

1. **Desacoplamiento en Capa de Servicios:** Replicando el patrón de IBM (`src/default_services.py`), se aisló la lógica analítica de la capa de presentación Streamlit, encapsulándola en `data_service.py` (procesamiento de datos y censo) y `model_service.py` (calibración e inferencia de ML).
2. **Testing Unitario como Quality Gate:** Adopción del framework `unittest` (similar a `test/default_test.py` de IBM) y su automatización estricta.
3. **Modernización del Tooling:** IBM utilizó Travis CI y ZenHub en 2018; nuestro equipo modernizó la infraestructura migrando a **GitHub Actions** con runners Ubuntu y orquestando la gestión con la suite combinada de **GitHub Projects v2** y **ZenHub SaaS** [10].

---

## III. DESCRIPCIÓN DEL PROCESO DE METODOLOGÍAS ÁGILES UTILIZADO (PUNTO 2)

### A. Marco Metodológico: Scrum Híbrido con Prácticas DevOps y Extreme Programming (XP)

El equipo implementó un marco de trabajo Scrum adaptado [10], enriquecido con prácticas de ingeniería de software de Extreme Programming (XP) —específicamente Desarrollo Guiado por Pruebas (TDD), Integración Continua y Revisiones de Código por Pares (Peer Reviews) [5]— y principios DevOps de entrega automatizada.

1. **Justificación de la Cadencia de Sprints:** Se definieron Sprints de dos semanas de duración (quincenales), dado que es el estándar universal de Scrum adoptado en `agile-tutorial`. Este ciclo proporciona el balance perfecto entre la rapidez de entrega funcional y el tiempo necesario para ejecutar procesos complejos de calibración matemática y validación de backtesting epidemiológico:
   * **Sprint 1 (Semanas 1 y 2 - Cimientos y Calidad Base):** Ingesta de series temporales, demografía censal INEI, algoritmos defensivos `safe_rate()` y configuración de la infraestructura de CI en GitHub Actions.
   * **Sprint 2 (Semanas 3 y 4 - Analítica Avanzada, UX y Quality Gate):** Calibración del modelo XGBoost ($R^2 = 0.935$), rediseño institucional sobrio, suite de 12 pruebas unitarias con enforzamiento de cobertura al 88% y despliegue continuo en Render.
2. **Ceremonias Scrum Implementadas:**
   * **Sprint Planning:** Al inicio de cada iteración, el equipo estima la complejidad de las historias de usuario mediante la escala Fibonacci (Story Points: 1, 2, 3, 5, 8) y se compromete formalmente con el Sprint Backlog.
   * **Daily Scrum:** Sincronizaciones de 15 minutos para transparentar avances, planificar las próximas 24 horas y remover impedimentos técnicos.
   * **Sprint Review:** Demostración técnica del incremento funcional en la plataforma web frente a los requerimientos de vigilancia del MINSA.
   * **Sprint Retrospective:** Análisis de métricas del proceso (velocidad, cobertura de tests, deuda técnica de `flake8`) y acuerdos de mejora continua conforme a ISO 9000 Cláusula 2.3.5.

### B. Modelo de Ramificación GitHub Flow y Gobernanza de Pull Requests

Conforme a las directrices de IBM `agile-tutorial` [7], se adoptó el modelo de ramas GitHub Flow:
* **Rama `main` Protegida:** La rama principal representa el estado en producción y está estrictamente protegida. Ningún desarrollador puede hacer push directo a `main`.
* **Ramas de Funcionalidad:** Para cada requerimiento se crea una rama aislada con la nomenclatura `feature/issue-X-descripcion` (ej. `feature/issue-5-tasas-censales`).
* **Commits Atómicos:** Mensajes explicativos estructurados bajo la especificación Conventional Commits (`feat`, `fix`, `test`, `docs`).
* **Pull Requests (PR) y Vinculación Semántica:** Cada PR debe describir técnicamente el cambio y vincular el issue respectivo mediante directivas como `Fixes #5`.
* **Status Checks Obligatorios:** El merge a `main` queda condicionado a la aprobación unánime de los dos jobs del pipeline CI y a la revisión por pares (*Peer Review*).

> [!NOTE]
> 📷 **[FIGURA 2: PLACEHOLDER DE CAPTURA - PULL REQUEST Y REVISIÓN DE CÓDIGO CON STATUS CHECKS VERDES]**  
> **Instrucciones para la captura:** Tomar captura de pantalla de un Pull Request en GitHub en modo claro. La captura debe mostrar la rama de origen (`feature/...`), la rama destino (`main`), el mensaje *"All checks have passed"* con los dos checks verdes del pipeline (`auditoria-codigo` y `pruebas-unitarias`), y la aprobación de revisión.

### C. Arquitectura del Pipeline de Integración y Despliegue Continuo (CI/CD Quality Gate)

En el archivo `.github/workflows/ci.yml` se construyó un pipeline de CI/CD desacoplado en dos jobs paralelos que se ejecutan en runners virtuales Ubuntu bajo Python 3.11:

* **Job 1 (`auditoria-codigo`):** Ejecuta el linter Flake8 inspeccionando errores de sintaxis, complejidad ciclomática y estilo PEP 8.
* **Job 2 (`pruebas-unitarias`):** Ejecuta la suite de 12 pruebas unitarias implementadas en `tests/test_services.py`, auditando exhaustivamente la consistencia temporal de los años (2000–2023), el manejo defensivo ante divisiones por cero, la normalización demográfica y las métricas de ML.

**Enforzamiento del Quality Gate:** Conforme a los estándares IEEE 730 [5] e IEEE 829 [6], se implementó la bandera restrictiva:
```bash
python -m coverage report --fail-under=80
```
Si la cobertura acumulada desciende del 80%, el pipeline aborta la ejecución con código de error 1, bloqueando irreversiblemente el Pull Request. En la auditoría real, el equipo alcanzó un **88% de cobertura de código**, superando con creces la cota exigida.

> [!NOTE]
> 📷 **[FIGURA 3: PLACEHOLDER DE CAPTURA - EJECUCIÓN DEL PIPELINE CI EN GITHUB ACTIONS CON 88% DE COBERTURA]**  
> **Instrucciones para la captura:** Tomar captura de pantalla de la pestaña 'Actions' en el repositorio de GitHub (`https://github.com/MarcoXMarquez/ispysa-vigilancia-ira-peru/actions`) en modo claro. La imagen debe evidenciar los dos jobs ejecutados (`auditoria-codigo` y `pruebas-unitarias`) con check verde, y el despliegue del log de consola donde se lea `TOTAL ... 88%` y el éxito del test runner.

---

## IV. HERRAMIENTAS Y ROLES A CONSIDERAR EN EL PROCESO (PUNTO 3)

### A. Ecosistema de Herramientas Tecnológicas y su Función

| Herramienta | Categoría / Propósito | Función en el Flujo de Trabajo |
| :--- | :--- | :--- |
| **GitHub Projects (v2)** | Gestión Ágil y CI/CD Integrado | Tablero visual kanban/scrum nativo. Sincronizado automáticamente con los Pull Requests y ramas del repositorio. |
| **ZenHub SaaS** | Métricas Avanzadas de Scrum | Herramienta oficial de IBM `agile-tutorial`. Proporciona Burndown Charts en tiempo real, velocidad de Sprints y agregación multinivel de Épicas. |
| **GitHub Actions** | Pipeline DevOps y Quality Gate | Servidor de integración continua. Ejecuta auditorías estáticas con Flake8 y runners de pruebas unitarias en Ubuntu con Python 3.11. |
| **Render Cloud Platform** | Hosting Cloud y Despliegue (CD) | Infraestructura cloud que hospeda el aplicativo en vivo (`https://ispysa-vigilancia-ira-peru.onrender.com/`) mediante webhooks automáticos al fusionar en `main`. |
| **Python 3.11 / Streamlit / Coverage / Flake8** | Stack Analítico y Testing | Motor analítico de datos (Pandas, Plotly, Scikit-learn, XGBoost) y suite de pruebas unitarias con enforzamiento de cobertura mínima. |

### B. Deconstrucción de Artefactos Ágiles: Épicas, Historias de Usuario, Sprints y Custom Fields

Para dotar al proyecto de verdadero rigor ingenieril, se diseñó una taxonomía formal de artefactos ágiles en GitHub Projects y ZenHub:

1. **¿Qué es una Épica y por qué se definieron así?**  
   Una Épica es un contenedor macro que agrupa múltiples historias de usuario orientadas a un objetivo estratégico de largo plazo. En el proyecto se definieron exactamente 3 Épicas, mapeando 1-to-1 las 3 preguntas de la rúbrica del docente:
   * `[EPIC-01]`: Implementación y Cumplimiento Normativo ISO 9000:2015 en Pipeline Epidemiológico.
   * `[EPIC-02]`: Pipeline DevOps, Flujo Git Flow y Quality Gate de Cobertura (88%).
   * `[EPIC-03]`: Gobernanza del Equipo, Ceremonias Scrum y Ergonomía Institucional (ISO 9241).
2. **¿Por qué Historias de Usuario?**  
   Son la unidad fundamental de entrega de valor al usuario clínico. Se redactaron bajo la sintaxis Scrum estándar: *"Como [rol clínico/técnico], Quiero [capacidad del sistema], Para [beneficio epidemiológico]"*, acompañadas de Criterios de Aceptación verificables (*Definition of Done - DoD*: cobertura $\ge 80\%$, linter limpio y peer review) y su respectiva cláusula de trazabilidad ISO 9000.
3. **¿Qué significan los Custom Fields configurados en GitHub Projects?**
   * **Sprint (*Iteration*):** Campo temporal de 2 semanas de duración que enmarca las tareas comprometidas.
   * **Estimate (*Number*):** Esfuerzo relativo ponderado en la escala Fibonacci de Story Points (1, 2, 3, 5, 8).
   * **Epic (*Single select*):** Clasificación estratégica de la tarea dentro de los 3 paquetes de trabajo del docente.
   * **Priority (*Single select*):** Criticidad operativa (P0-Crítica, P1-Alta, P2-Media).
   * **Status (*Single select*):** Estado Kanban del flujo de valor (*Todo*, *In Progress*, *Review/QA*, *Done*).

> [!NOTE]
> 📷 **[FIGURA 4: PLACEHOLDER DE CAPTURA - TABLERO SCRUM EN ZENHUB CON LAS 3 ÉPICAS Y STORY POINTS]**  
> **Instrucciones para la captura:** Tomar captura de pantalla de la vista 'Work Tracker' en ZenHub (`app.zenhub.com`) en modo claro. La captura debe evidenciar las tarjetas de las 3 Épicas (#1, #3, #4) y las Historias de Usuario con sus etiquetas de colores (`epic`, `user-story`, `iso-9000`, `devops`), sus Story Points visibles y los avatares asignados.

> [!NOTE]
> 📷 **[FIGURA 5: PLACEHOLDER DE CAPTURA - GRÁFICO DE QUEMADO (BURNDOWN CHART) EN ZENHUB]**  
> **Instrucciones para la captura:** Tomar captura de pantalla de la sección 'Reports' -> 'Burndown' en ZenHub en modo claro. La imagen debe mostrar la curva de progreso del Sprint con el quemado de Story Points hacia la fecha de entrega, demostrando la velocidad del equipo y el cumplimiento del trabajo.

> [!NOTE]
> 📷 **[FIGURA 6: PLACEHOLDER DE CAPTURA - VISTA DE TABLA PRODUCT BACKLOG EN GITHUB PROJECTS]**  
> **Instrucciones para la captura:** Tomar captura de pantalla de la pestaña 'Product Backlog' en GitHub Projects en modo claro. La tabla debe mostrar claramente las columnas Title, Assignee (con avatares), Status, Epic, Sprint, Estimate (puntos) y Priority.

### C. Asignación de Roles del Equipo y Matriz RACI

El equipo de 5 estudiantes de la Escuela Profesional de Ingeniería de Sistemas de la UNSA asumió roles especializados conforme a las mejores prácticas de Scrum y la matriz de responsabilidades RACI (*Responsible*, *Accountable*, *Consulted*, *Informed*):

* **Marco Antonio Marquez Herrera:** Scrum Master & QA/DevOps Lead. Custodio del proceso ágil, modelado de ramas en GitHub Flow, configuración de GitHub Actions y enforzamiento del Quality Gate al 88% de cobertura.
* **Joel Isaias Condori Leon:** Product Owner & Experto de Dominio Clínico. Representante de los requerimientos del MINSA, priorización del Product Backlog y definición de los umbrales de los semáforos de alerta epidemiológica.
* **Leonardo Ruben Arce Mayhua:** Data Engineer / Backend Lead. Ingesta de series temporales crudas, interpolación censal INEI y diseño de algoritmos defensivos de tasa segura (`safe_rate`) en `data_service.py`.
* **Jeremy Joshua Perez Huamani:** Machine Learning Engineer. Calibración, evaluación empírica y selección del algoritmo predictivo XGBoost ($R^2 = 0.935$) en `model_service.py` [9].
* **Rafael Diego Nina Calizaya:** Frontend & UX Engineer. Rediseño visual ministerial sobrio bajo normas ISO 9241, erradicación de AI-Slop y confección de la Ficha Técnica oficial en `app.py`.

| Historia de Usuario (US) | PO (Joel) | SM (Marco) | Data (Leo) | ML (Jeremy) | UX (Rafael) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **US-01: Tasas epidemiológicas y censo** | A | C | **R** | C | I |
| **US-02: Control de salidas safe_rate()** | I | A | **R** | C | I |
| **US-03: Modelos predictivos XGBoost** | C | A | C | **R** | I |
| **US-04: GitHub Flow y .gitignore** | I | **R / A** | C | C | C |
| **US-05: Pipeline CI en GitHub Actions** | I | **R / A** | C | C | C |
| **US-06: Quality Gate cobertura >= 80%** | C | **R / A** | C | C | C |
| **US-07: Matriz RACI y ceremonias Scrum** | **R / A** | C | I | I | I |
| **US-08: Rediseño visual anti-AI slop** | A | C | I | I | **R** |
| **US-09: Ficha técnica y glosario MINSA** | A | C | C | C | **R** |

> [!NOTE]
> 📷 **[FIGURA 7: PLACEHOLDER DE CAPTURA - PLANTILLA DE HISTORIA DE USUARIO EN GITHUB ISSUES]**  
> **Instrucciones para la captura:** Tomar captura de pantalla de la creación de un nuevo Issue en GitHub (`https://github.com/MarcoXMarquez/ispysa-vigilancia-ira-peru/issues/new/choose`) en modo claro. La imagen debe mostrar las dos plantillas disponibles ('Historia de Usuario (Scrum)' y 'Épica de Proyecto') y el formulario prediseñado con los campos de 'Como/Quiero/Para', Criterios de Aceptación y Cláusula ISO 9000.

---

## V. EVIDENCIAS EMPÍRICAS Y RESULTADOS DE AUDITORÍA

| Métrica de Calidad | Estándar / Umbral Exigido | Resultado Empírico Obtenido |
| :--- | :--- | :--- |
| **Cobertura de Pruebas Unitarias** | Mínimo 80% (`--fail-under=80`) | **88% de cobertura real** (12 pruebas unitarias automatizadas en pytest/unittest). |
| **Auditoría Estática de Código** | Cero errores críticos de sintaxis PEP 8 | **Aprobado al 100%** con Flake8 en pipeline de CI de GitHub Actions. |
| **Ajuste del Modelo Predictivo** | Capacidad de generalización superior | **XGBoost con $R^2 = 0.935$** en pediatría y 0.890 en geriatría con backtesting de 5 años. |
| **Tolerancia a Fallos Matemáticos** | Cero caídas por división entre cero | `safe_rate()` retorna `0.0` determinista ante denominadores nulos o censos faltantes. |
| **Disponibilidad en Producción** | Despliegue cloud continuo verificado | Operativo 24/7 en Render Cloud (`https://ispysa-vigilancia-ira-peru.onrender.com/`). |

---

## VI. CONCLUSIONES

1. La articulación de la norma ISO 9000:2015 con metodologías ágiles demuestra que la agilidad y el rigor normativo no son mutuamente excluyentes. Los principios de enfoque a procesos y toma de decisiones basada en evidencia encontraron en Scrum y en el Quality Gate automatizado su vehículo natural de aseguramiento continuo.
2. La adopción de los patrones de IBM `agile-tutorial` (desacoplamiento en capa de servicios y GitHub Flow) permitió una transición limpia desde un prototipo local hacia un microservicio escalable con una suite de 12 pruebas unitarias y 88% de cobertura.
3. La gobernanza coordinada mediante GitHub Projects v2 y ZenHub garantizó la visibilidad operativa del equipo de 5 integrantes, permitiendo monitorear el quemado de Story Points (Burndown Chart) y automatizar el flujo de trabajo mediante eventos de Pull Requests.
4. El rediseño de la interfaz bajo ISO 9241 e ISO/IEC 25010 erradicó distracciones cognitivas de AI-Slop, dotando a los tomadores de decisiones de salud pública de una herramienta institucional, robusta y clínicamente relevante.

---

## REFERENCIAS (Formato IEEE)

* **[1]** International Organization for Standardization, *ISO 9000:2015: Quality management systems — Fundamentals and vocabulary*, Ginebra, Suiza: ISO, 2015.
* **[2]** International Organization for Standardization, *ISO/IEC 25010:2011: Systems and software engineering — Systems and software Quality Requirements and Evaluation (SQuaRE) — System and software quality models*, Ginebra, Suiza: ISO/IEC, 2011.
* **[3]** International Organization for Standardization, *ISO 9241-11:2018: Ergonomics of human-system interaction — Part 11: Usability: Definitions and concepts*, Ginebra, Suiza: ISO, 2018.
* **[4]** International Organization for Standardization, *ISO 9241-210:2019: Ergonomics of human-system interaction — Part 210: Human-centred design for interactive systems*, Ginebra, Suiza: ISO, 2019.
* **[5]** IEEE Computer Society, *IEEE Standard for Software Quality Assurance Processes*, IEEE Std 730-2014, pp. 1–138, 2014. doi: 10.1109/IEEESTD.2014.6835311.
* **[6]** IEEE Computer Society, *IEEE Standard for Software and System Test Documentation*, IEEE Std 829-2008, pp. 1–150, 2008. doi: 10.1109/IEEESTD.2008.4578383.
* **[7]** IBM Corporation, *Agile Tutorial: Cloud Native Agile Development with Python and Flask*, GitHub Repository, 2018. [En línea]. Disponible: https://github.com/IBM/agile-tutorial.
* **[8]** Centro Nacional de Epidemiología, Prevención y Control de Enfermedades (CDC Perú), *Vigilancia Epidemiológica de las Infecciones Respiratorias Agudas (IRA)*, Ministerio de Salud (MINSA), Lima, Perú, Bol. Epidemiol., vol. 32, no. 52, 2023.
* **[9]** T. Chen and C. Guestrin, "XGBoost: A Scalable Tree Boosting System," en *Proc. 22nd ACM SIGKDD Int. Conf. Knowl. Discovery Data Mining (KDD)*, San Francisco, CA, 2016, pp. 785–794. doi: 10.1145/2939672.2939785.
* **[10]** K. Schwaber and J. Sutherland, *The Scrum Guide: The Definitive Guide to Scrum: The Rules of the Game*, Scrum.org, 2020. [En línea]. Disponible: https://scrumguides.org.
