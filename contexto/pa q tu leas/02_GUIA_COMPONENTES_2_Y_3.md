# Guía de Componentes 2 y 3 (Para Humanos)

**Para quién es:** Integrantes del equipo.  
**Objetivo:** Saber exactamente qué es el Componente 2, qué es el Componente 3, qué hace cada uno y qué debemos hacer para entregarlos.

---

## 1. Componente 3: Subida a GitHub (Lo Operativo)

### ¿Qué es?
Es la preparación y publicación del código fuente en nuestro repositorio de GitHub.

### ¿Qué se hizo ya?
1. Se limpió la carpeta `ISPySA-Pneumonia-main`: **se borró el `.bat`** que no correspondía subir a GitHub.
2. Se configuró `.gitignore` para que nadie suba entornos virtuales ni temporales.
3. Se dejó listo el archivo `.github/workflows/ci.yml` con 2 verificaciones automáticas (auditoría de código y pruebas unitarias con mínimo 80% de cobertura).

### ¿Qué falta hacer?
Solo que uno de nosotros cree el repositorio en GitHub y ejecute los 2 comandos de subida explicados en [`GUIA_SUBIDA_GITHUB.md`](file:///c:/Users/marco/Desktop/TEO-CS/TRABAJO%202/GUIA_SUBIDA_GITHUB.md):
```bash
git remote add origin https://github.com/TU_USUARIO/NOMBRE_REPO.git
git push -u origin main
```
Apenas suba, GitHub Actions correrá las pruebas y pondrá el check verde (`✔ Passed`).

---

## 2. Componente 2: Documento Académico (Lo Teórico / Informe)

### ¿Qué es?
Es el informe formal que debemos entregar al profesor respondiendo a sus 3 preguntas del Trabajo Parcial 2:
1. **Punto 1:** ¿Cómo aplicamos ISO 9000:2015 y el tutorial ágil en el proyecto de neumonía?
2. **Punto 2:** ¿Qué proceso ágil usamos para trabajar en equipo? (Scrum + GitHub Flow + CI).
3. **Punto 3:** ¿Qué herramientas usamos y qué rol tiene cada uno de los 5 integrantes?

### ¿Qué roles nos asignamos en el Punto 3?
Para la entrega académica, el equipo de 5 se distribuye así:
* **Integrante 1 (Product Owner):** Prioriza qué gráficos e indicadores se programan según necesidad del sector salud.
* **Integrante 2 (Scrum Master):** Organiza las reuniones, revisa que el tablero esté al día y elimina bloqueos.
* **Integrante 3 (Ingeniero de Datos):** Responsable de las tablas de datos, censos y `data_service.py`.
* **Integrante 4 (Ingeniero de Machine Learning):** Calibra el modelo XGBoost, calcula el $R^2=0.935$ y las proyecciones a 52 semanas.
* **Integrante 5 (Ingeniero de Calidad y Pruebas - QA / DevOps):** Hace las pruebas unitarias, vigila que la cobertura no baje del 80% y mantiene el CI en GitHub Actions.

### ¿Cómo se vincula esto a GitHub Projects?
Cuando subamos el repositorio, en **GitHub Projects** crearemos 3 Épicas (una por cada pregunta del profesor) con tareas asignadas a cada integrante. Así demostramos que no solo escribimos teoría, sino que gestionamos el proyecto de verdad.
