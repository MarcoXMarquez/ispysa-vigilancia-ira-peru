@echo off
chcp 65001 >nul
title [2/6] Auditoría Automática de Calidad ISO/IEC 25010 (GQM UNLP)
cls

echo ===============================================================================
echo   DEMOSTRACION 2: AUDITORIA AUTOMATICA DE CALIDAD ISO/IEC 25010 (MOTOR GQM)
echo   MODELO COMPUTACIONAL: Calabrese et al. (2018) — III-LIDI, UNLP
echo   SISTEMA EVALUADO: ISPySA-Pneumonia (Salud Publica)
echo ===============================================================================
echo.

set APP_DIR=%~dp0..
cd /d "%APP_DIR%"
echo Directorio de ejecucion: %CD%
echo.

if not exist "scripts\run_quality_audit.py" (
    echo [ERROR] No se encontro scripts\run_quality_audit.py en %CD%
    pause
    exit /b 1
)

echo [1/2] Ejecutando motor GQM y evaluando 54 preguntas operacionales...
echo       (19 sondas de codigo AST, 8 verificaciones documentales, 27 exclusiones justificadas)
echo.

where uv >nul 2>nul
if %ERRORLEVEL% equ 0 (
    uv run --with-requirements requirements.txt --with-requirements requirements-dev.txt python scripts/run_quality_audit.py
    goto exito
)

where python >nul 2>nul
if %ERRORLEVEL% equ 0 (
    python scripts/run_quality_audit.py
    goto exito
)

echo [ERROR] Se requiere 'uv' o 'python' para ejecutar la auditoria.
pause
exit /b 1

:exito
echo.
echo ===============================================================================
echo   VERIFICACION DE ARTEFACTOS GENERADOS:
echo   • JSON de Auditoria: data\quality\last_audit.json
echo   • Catalogo CSV:      data\quality\last_audit.csv
echo ===============================================================================
echo.
pause
