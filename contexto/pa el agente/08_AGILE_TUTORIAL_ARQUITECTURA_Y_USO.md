# Implementación Técnica: Deconstrucción de `agile-tutorial` (IBM)

**Repositorio Fuente:** `https://github.com/IBM/agile-tutorial.git`  
**Directorio Local:** `c:\Users\marco\Desktop\TEO-CS\TRABAJO 2\agile-tutorial\`  
**Destinatario:** Agente de IA  
**Rol del Documento:** Analizar la arquitectura metodológica del tutorial ágil de IBM y detallar su adopción práctica en el proyecto epidemiológico.

---

## 1. Arquitectura y Contenido del Repositorio `agile-tutorial`

El repositorio de IBM fue creado como un laboratorio de formación para el desarrollo ágil de aplicaciones cloud en Python. Se divide en cuatro módulos esenciales:

### 1.1. Módulo 1 (`docs/1-INSTALL.md`): Tooling y Entorno Colaborativo
* **Propósito:** Establecer la infraestructura del desarrollador.
* **Componentes:**
  - Repositorio centralizado en **GitHub**.
  - Gestión de tableros de historias de usuario mediante **ZenHub**.
  - Pipeline de Integración Continua en la nube mediante **Travis CI**.
  - Editor estandarizado con configuración `.editorconfig`.

### 1.2. Módulo 2 (`docs/2-UNDERSTAND.md`): Metodología Ágil y Modelo de Ramas
* **Marco Scrum:**
  - Roles: *Product Owner* (voz del stakeholder), *Scrum Master* (facilitador del proceso) y *Development Team* (entrega de incrementos funcionales).
  - Rituales: *Sprint Planning* (quincenal), *Daily Scrum* (15 min diarios) y *Sprint Review / Retrospective*.
* **Modelo de Ramas "GitHub Flow":**
  1. La rama `external` (o `main`) siempre es potencialmente desplegable.
  2. Todo cambio se origina en una rama de feature: `git checkout -b feature/issue-id`.
  3. Commits atómicos con mensajes significativos.
  4. Apertura de **Pull Request (PR)** hacia la rama base con descripción técnica.
  5. Aprobación obligatoria de *Status Checks* (pruebas de CI) y revisión de código por pares.
  6. Fusión (*Merge*) y despliegue automatizado.

### 1.3. Módulo 3 (`docs/3-EXPLORE.md`): Arquitectura de Software y Testing
* **Microservicio en Python:** API REST construida con Flask y `flask_restplus` (`main.py`).
* **Capa de Servicios Desacoplada:** `src/default_services.py` separa la lógica de negocio del enrutamiento HTTP.
* **Pruebas Unitarias:** Implementación con el framework estándar `unittest` (`test/default_test.py`).

### 1.4. Módulo 4 (`docs/4-DEVELOP.md`): Ciclo de Desarrollo Colaborativo
* Simula la asignación de issues en un tablero Kanban, resolución de conflictos de merge y despliegue continuo (CD) a entornos cloud basados en Cloud Foundry (`manifest.yml` y `Procfile`).

---

## 2. Cómo se Adoptó `agile-tutorial` en el Proyecto Epidemiológico

La plataforma epidemiológica (`ISPySA-Pneumonia`) tomó la filosofía del tutorial de IBM y la adaptó al ecosistema moderno:

| Componente en `agile-tutorial` (IBM 2018) | Adopción y Modernización en `ISPySA-Pneumonia` (2026) |
| :--- | :--- |
| **Microservicio desacoplado (`src/default_services.py`)** | Se encapsuló la analítica pesada en la Capa de Servicios: [`data_service.py`](file:///c:/Users/marco/Desktop/TEO-CS/TRABAJO%202/Código/ISPySA-Pneumonia-main/ISPySA-Pneumonia-main/src/services/data_service.py) y [`model_service.py`](file:///c:/Users/marco/Desktop/TEO-CS/TRABAJO%202/Código/ISPySA-Pneumonia-main/ISPySA-Pneumonia-main/src/services/model_service.py). |
| **Pruebas unitarias básicas (`test/default_test.py`)** | Suite completa de 12 pruebas unitarias en [`tests/test_services.py`](file:///c:/Users/marco/Desktop/TEO-CS/TRABAJO%202/Código/ISPySA-Pneumonia-main/ISPySA-Pneumonia-main/tests/test_services.py) cubriendo el 100% de funciones analíticas clave con **88% de cobertura**. |
| **Pipeline en Travis CI (`.travis.yml`)** | Migración a **GitHub Actions** ([`.github/workflows/ci.yml`](file:///c:/Users/marco/Desktop/TEO-CS/TRABAJO%202/Código/ISPySA-Pneumonia-main/ISPySA-Pneumonia-main/.github/workflows/ci.yml)) en runner Ubuntu, separando en dos jobs (`auditoria-codigo` y `pruebas-unitarias`). |
| **Quality Gate por paso simple de tests** | **Quality Gate Estricto:** Falla obligatoria si la cobertura cae por debajo del 80% (`python -m coverage report --fail-under=80`). |
| **Gestor externo ZenHub** | Gestión nativa en **GitHub Projects (v2)**, reduciendo fricción y dependencias de extensiones de terceros para el equipo. |
| **Despliegue Cloud Foundry (`manifest.yml`)** | Despliegue en contenedor con runner Python 3.12 y soporte multiplataforma. |
