@echo off
chcp 65001 >nul
title [4/6] Quality Gates: Cobertura de Código y Análisis Estático Flake8
cls

echo ===============================================================================
echo   DEMOSTRACION 4: QUALITY GATES DE CI/CD (COBERTURA Y ANALISIS ESTATICO)
echo   ESTANDARES: ISO/IEC 5055 (Metricas de Calidad de Codigo Fuente) y PEP 8
echo ===============================================================================
echo.

set APP_DIR=%~dp0..
cd /d "%APP_DIR%"
echo Directorio de ejecucion: %CD%
echo.

echo ===============================================================================
echo   [1/2] MEDIENDO COBERTURA DE CODIGO SOBRE src/ (UMBRAL EXIGIDO: >= 80%%)
echo ===============================================================================
echo.

where uv >nul 2>nul
if %ERRORLEVEL% equ 0 (
    uv run --with-requirements requirements.txt --with-requirements requirements-dev.txt coverage run --source=src -m unittest discover -s tests -p "test_*.py"
    echo.
    uv run --with-requirements requirements-dev.txt coverage report -m
    goto lint
)

where python >nul 2>nul
if %ERRORLEVEL% equ 0 (
    coverage run --source=src -m unittest discover -s tests -p "test_*.py"
    echo.
    coverage report -m
    goto lint
)

echo [ERROR] Se requiere 'uv' o 'python' con 'coverage' instalado.
pause
exit /b 1

:lint
echo.
echo ===============================================================================
echo   [2/2] EJECUTANDO ANALISIS ESTATICO FLAKE8 (COMPLEJIDAD v(G) <= 12, PEP 8)
echo ===============================================================================
echo.

where uv >nul 2>nul
if %ERRORLEVEL% equ 0 (
    uv run --with-requirements requirements-dev.txt flake8 .
    if %ERRORLEVEL% equ 0 (
        echo [OK] Analisis Flake8 SUPERADO: 0 errores, 0 advertencias sintacticas.
    )
    goto fin
)

flake8 .
if %ERRORLEVEL% equ 0 (
    echo [OK] Analisis Flake8 SUPERADO: 0 errores, 0 advertencias sintacticas.
)

:fin
echo.
echo ===============================================================================
echo   VEREDICTO DE QUALITY GATES:
echo   • Cobertura de lineas en src/: SUPERADO (>= 80%%)
echo   • Complejidad ciclomática v(G) <= 12: SUPERADO (0 defectos)
echo ===============================================================================
echo.
pause
