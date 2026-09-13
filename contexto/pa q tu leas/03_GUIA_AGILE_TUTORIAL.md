# Guía Rápida: El Tutorial Ágil de IBM y Cómo lo Usamos

**Para quién es:** Integrantes del equipo.  
**Objetivo:** Entender en 3 minutos de qué trata la carpeta `agile-tutorial` y cómo responderle al profesor sobre cómo lo aplicamos en nuestro proyecto.

---

## 1. ¿De qué trata `agile-tutorial`?

Es un tutorial oficial publicado por **IBM** en GitHub (`IBM/agile-tutorial`) que enseña las buenas prácticas de la industria para desarrollar software en la nube de forma ágil y colaborativa.

Enseña 4 cosas principales:
1. **Scrum y Tableros:** Cómo organizar las tareas en Sprints y asignar roles (Product Owner, Scrum Master, Developers).
2. **Flujo de Ramas (GitHub Flow):** La regla de oro de nunca programar directo sobre `main`. Cada quien saca una rama (`feature/tarea-x`), programa, y abre un Pull Request (PR) para que otro compañero lo revise.
3. **Integración Continua (CI):** Automatizar pruebas para que la computadora revise el código antes de que se acepte cualquier cambio.
4. **Microservicios en Python:** Separar la lógica pesada en archivos de servicio independientes en lugar de tener un código espagueti desordenado.

---

## 2. ¿Cómo lo aplicamos en nuestro proyecto de Neumonía?

No copiamos el código del tutorial a ciegas; adaptamos sus **principios y buenas prácticas** a nuestro proyecto de salud pública:

1. **Separación por Capas:** Así como IBM separa su API en `default_services.py`, nosotros separamos la analítica en `data_service.py` y `model_service.py`. La interfaz `app.py` solo muestra los resultados, no hace cálculos pesados.
2. **Pruebas Automatizadas:** Creamos 12 pruebas unitarias en `test_services.py` para asegurar que las tasas matemáticas y las proyecciones no fallen.
3. **De Travis CI a GitHub Actions:** El tutorial de IBM usaba Travis CI (común en 2018). Nosotros lo modernizamos a **GitHub Actions**, configurando dos tareas: auditoría de código con Flake8 y verificación estricta de que la cobertura de pruebas sea mínimo del 80%.
4. **Trabajo en Equipo:** Organizamos el trabajo en Sprints y definimos los 5 roles del equipo para responder la pregunta 3 del profesor.
