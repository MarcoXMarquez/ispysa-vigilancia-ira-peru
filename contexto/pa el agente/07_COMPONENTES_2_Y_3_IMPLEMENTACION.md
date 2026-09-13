# Implementación Técnica: Componentes 2 y 3

**Destinatario:** Agente de IA  
**Rol del Documento:** Especificación técnica para la construcción del documento académico del Trabajo Parcial 2 (Componente 2) y la operación de sincronización y subida a GitHub (Componente 3).

---

## 1. Deconstrucción del Componente 3: Subida a GitHub y Versionamiento

### 1.1. Propósito y Contexto
El Componente 3 consiste en aislar la aplicación analítica, depurar archivos locales que violen las políticas del repositorio (específicamente scripts `.bat` y temporales), inicializar el árbol Git y subirlo a GitHub.

### 1.2. Procedimiento de Ejecución
1. **Árbol de Directorio Seleccionado:** `TRABAJO 2\Código\ISPySA-Pneumonia-main\ISPySA-Pneumonia-main\`
2. **Depuración de Artefactos Prohibidos:** Se eliminó `ejecutar_aplicativo.bat` y se actualizó `.gitignore` para bloquear:
   ```text
   *.bat
   *.exe
   .venv/
   __pycache__/
   .coverage
   ```
3. **Inicialización y Commit Base:**
   * Rama principal: `main`.
   * Commit inicial: `feat: institutional redesign, split CI audit/tests and 88% unit test coverage` (hash `4c97fac`).
4. **Comandos de Sincronización Remota:**
   ```bash
   git remote add origin https://github.com/<USUARIO>/<REPO>.git
   git push -u origin main
   ```
5. **Comportamiento Automático al Subir:** El archivo `.github/workflows/ci.yml` gatilla automáticamente dos jobs en GitHub Actions:
   - `auditoria-codigo` (Flake8 linter).
   - `pruebas-unitarias` (12 tests con fail-under=80%).

---

## 2. Deconstrucción del Componente 2: Documento Académico Formal

### 2.1. Propósito y Contexto
El Componente 2 es la memoria técnica formal solicitada por el profesor en la consigna del Trabajo Parcial 2. Consta de 3 puntos obligatorios:

```text
Trabajo Parcial 2:
1. Revisar, seleccionar y adoptar características de la norma ISO 9000-2015 y de tutorial de modelos ágiles en el proyecto de salud pública.
2. Describir el proceso de metodologías ágiles que podría utilizar.
3. Indique herramientas y roles a considerar en el proceso mencionado.
```

### 2.2. Contexto Requerido para Resolver el Punto 1
* **Normativo:** ISO 9000:2015 cláusulas 2.3.1 (Cliente), 2.3.4 (Procesos), 2.3.5 (Mejora), 2.3.6 (Evidencia) y 3.10.1 (Salidas no conformes).
* **Tutorial Ágil:** Repositorio `agile-tutorial` de IBM: arquitectura de microservicios en capas, integración continua (CI) y modelo de ramificación GitHub Flow.
* **Proyecto:** `ISPySA-Pneumonia`: datos de IRA MINSA Perú 2000-2023, tasas por 100k hab., Machine Learning XGBoost con $R^2=0.935$, 12 tests con 88% de cobertura.

### 2.3. Contexto Requerido para Resolver el Punto 2
* **Marco Metodológico:** Scrum adaptado con prácticas de ingeniería XP y DevOps.
* **Ritmo:** Sprints de 2 semanas con ceremonias formales: Sprint Planning, Daily Scrum (15 min), Sprint Review y Sprint Retrospective.
* **Flujo de Ramas:** GitHub Flow: rama `main` protegida, ramas de funcionalidad (`feature/issue-X`), Pull Requests obligatorios y revisión por pares (*Peer Review*).

### 2.4. Contexto Requerido para Resolver el Punto 3
* **Distribución de Roles (5 integrantes):**
  1. *Product Owner:* Visión del producto, priorización epidemiológica en el Product Backlog.
  2. *Scrum Master:* Facilitador de Scrum, remoción de impedimentos técnicos y auditoría de calidad.
  3. *Ingeniero de Datos / Backend:* Pipelines de ingesta, interpolación demográfica y `data_service.py`.
  4. *Ingeniero de Machine Learning:* Calibración de modelos, evaluación de métricas ($R^2$, RMSE) y proyecciones.
  5. *Ingeniero de Calidad y Pruebas (QA / DevOps):* Automatización de pruebas unitarias, cobertura $\ge 80\%$ y mantenimiento del CI en GitHub Actions.
* **Ecosistema Tecnológico:** GitHub, GitHub Projects (v2), GitHub Actions, Python 3.12, Streamlit, `unittest` + `coverage`, Flake8.

---

## 3. Mapeo del Componente 2 a GitHub Projects (Plan de Integración)

Para estructurar este trabajo en el tablero **GitHub Projects**, se deben generar 3 Épicas que corresponden directamente a los 3 requerimientos del docente:

* **Épica 1 (Asociada al Punto 1):** `[EPIC-01] Implementación y Cumplimiento Normativo ISO 9000:2015 en Pipeline Epidemiológico`.
  - Issue 1.1: Estandarización matemática de tasas por 100k hab. y prevención de división por cero.
  - Issue 1.2: Validación empírica de algoritmos predictivos (XGBoost $R^2=0.935$).
  - Issue 1.3: Desacoplamiento de lógica en Capa de Servicios (`DataService` y `ModelService`).

* **Épica 2 (Asociada al Punto 2):** `[EPIC-02] Pipeline DevOps, Flujo Git Flow y Quality Gate de Cobertura`.
  - Issue 2.1: Configuración de workflow de CI en GitHub Actions con dos jobs separados.
  - Issue 2.2: Suite de 12 pruebas unitarias automatizadas en `test_services.py`.
  - Issue 2.3: Enforzamiento del umbral mínimo de cobertura del 80% (`--fail-under=80`).

* **Épica 3 (Asociada al Punto 3):** `[EPIC-03] Gobernanza del Equipo, Ceremonias Scrum y Ergonomía de Interfaz`.
  - Issue 3.1: Definición de la matriz RACI de los 5 integrantes del equipo.
  - Issue 3.2: Rediseño visual institucional de `app.py` eliminando sesgos de AI-Slop.
  - Issue 3.3: Elaboración de la memoria técnica de entrega para el docente.
