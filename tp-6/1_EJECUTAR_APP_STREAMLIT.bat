@echo off
chcp 65001 >nul
title [1/6] Tablero Interactivo Streamlit — ISPySA-Pneumonia (ISO 25010)
cls

echo ===============================================================================
echo   DEMOSTRACION 1: TABLERO DE CONTROL DE CALIDAD Y ANALITICA (STREAMLIT)
echo   SISTEMA DE VIGILANCIA EPIDEMIOLOGICA: ISPySA-Pneumonia
echo   ESTANDARES: ISO/IEC 25010 (GQM UNLP), ISO 9241 (Ergonomia Medica) y WCAG 2.1 AA
echo ===============================================================================
echo.

set APP_DIR=%~dp0..
cd /d "%APP_DIR%"
echo Directorio de la aplicacion: %CD%
echo.

if not exist "app.py" (
    echo [ERROR] No se encontro app.py en el directorio %CD%
    pause
    exit /b 1
)

echo [Paso 1/3] Verificando entorno de ejecucion (uv / Python)...
where uv >nul 2>nul
if %ERRORLEVEL% equ 0 (
    echo [OK] Motor 'uv' detectado. Ejecutando con dependencias de requirements.txt...
    echo.
    echo [Paso 2/3] Abriendo navegador en http://localhost:8501 ...
    start "" http://localhost:8501
    echo.
    echo [Paso 3/3] Levantando servidor Streamlit...
    echo ===============================================================================
    echo   Instrucciones para la evaluacion del docente:
    echo   1. En el navegador, haga clic en la pestana "Calidad del producto (ISO 25010)".
    echo   2. Observe el grafico Radar polar con las 8 caracteristicas evaluadas.
    echo   3. Verifique el Scorecard ejecutivo: Indice Aplicable 100.0%%, Estricto 91.5%%.
    echo   4. Pruebe los botones de descarga de reportes en JSON y CSV.
    echo   * Para detener el servidor presione Ctrl+C en esta consola.
    echo ===============================================================================
    echo.
    uv run --with-requirements requirements.txt streamlit run app.py --server.port 8501
    goto fin
)

where python >nul 2>nul
if %ERRORLEVEL% equ 0 (
    echo [OK] Python detectado en el sistema.
    echo [Paso 2/3] Abriendo navegador en http://localhost:8501 ...
    start "" http://localhost:8501
    echo.
    echo [Paso 3/3] Levantando servidor Streamlit con Python...
    echo ===============================================================================
    echo   Para detener el servidor presione Ctrl+C en esta consola.
    echo ===============================================================================
    echo.
    python -m streamlit run app.py --server.port 8501
    goto fin
)

echo [ERROR] No se detecto ni 'uv' ni 'python' en el PATH del sistema.
echo Por favor instale Python 3.10+ o el gestor uv (https://astral.sh/uv).
pause
exit /b 1

:fin
echo.
echo Servidor Streamlit finalizado.
pause
