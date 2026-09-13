# Resumen Ejecutivo para el Equipo de Trabajo

**Proyecto:** Plataforma de Vigilancia Epidemiológica IRA - Perú (2000–2023)  
**Curso:** Calidad de Software (`TEO-CS`) — Trabajo Parcial 2  
**Destinatarios:** Integrantes del Equipo (Lectura Humana Rápida)  
**Tiempo Estimado de Lectura:** 3 minutos  

---

## 1. ¿De qué trata este trabajo y qué tenemos listo?

Para este **Trabajo Parcial 2**, el profesor nos pidió articular 3 cosas:
1. La norma internacional **ISO 9000:2015** (calidad en los procesos de software).
2. El repositorio de IBM **`agile-tutorial`** (desarrollo ágil con Scrum, GitHub Flow y CI/CD).
3. Nuestro código fuente de **vigilancia de neumonía** en Perú (`ISPySA-Pneumonia-main`).

### ¿Qué hitos ya completamos?
* ✅ **Limpieza del Repositorio (Componente 1):** Se eliminó el `.bat` que no debía subirse a GitHub, se configuró `.gitignore` para bloquear temporales y se inicializó la rama `main` con un commit limpio.
* ✅ **Rediseño Profesional de la Interfaz:** Se eliminó la marquesina en movimiento y los clichés visuales de IA de `app.py`. Ahora luce como un sistema formal del Ministerio de Salud (MINSA).
* ✅ **Pruebas Unitarias y Cobertura (88%):** Se crearon 12 pruebas unitarias en `test_services.py` que aprueban al 100% y superan la meta del 80% exigida.
* ✅ **Pipeline de Integración Continua (CI/CD):** En `.github/workflows/ci.yml` se configuraron dos verificaciones automáticas: auditoría de código con Flake8 y ejecución de pruebas con bloqueo obligatorio si la cobertura es menor al 80%.
* ✅ **Guía de Subida a GitHub (Componente 3):** Lista en [`GUIA_SUBIDA_GITHUB.md`](file:///c:/Users/marco/Desktop/TEO-CS/TRABAJO%202/GUIA_SUBIDA_GITHUB.md).

---

## 2. Estructura de Documentación en esta Carpeta

* **Para nosotros (los humanos):** En esta carpeta `pa q tu leas/` tenemos explicaciones digeridas y al grano:
  * [`01_GUIA_ISOS_SIMPLIFICADA.md`](file:///c:/Users/marco/Desktop/TEO-CS/TRABAJO%202/contexto/pa%20q%20tu%20leas/01_GUIA_ISOS_SIMPLIFICADA.md): Qué normas ISO pusimos y dónde están en el código.
  * [`02_GUIA_COMPONENTES_2_Y_3.md`](file:///c:/Users/marco/Desktop/TEO-CS/TRABAJO%202/contexto/pa%20q%20tu%20leas/02_GUIA_COMPONENTES_2_Y_3.md): Qué se entrega en el Componente 2 (informe) y Componente 3 (subida).
  * [`03_GUIA_AGILE_TUTORIAL.md`](file:///c:/Users/marco/Desktop/TEO-CS/TRABAJO%202/contexto/pa%20q%20tu%20leas/03_GUIA_AGILE_TUTORIAL.md): Cómo usamos el tutorial de IBM en nuestro proyecto.
* **Para los agentes de IA de nuestros compañeros:** En la carpeta vecina `pa el agente/` están los archivos técnicos ultra-detallados con fórmulas, cláusulas y arquitectura de código para que sus IAs puedan trabajar sin perder contexto.
