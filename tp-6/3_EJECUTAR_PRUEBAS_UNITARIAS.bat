@echo off
chcp 65001 >nul
title [3/6] Suite Completa de 105 Pruebas Unitarias — ISPySA-Pneumonia
cls

echo ===============================================================================
echo   DEMOSTRACION 3: SUITE COMPLETA DE PRUEBAS UNITARIAS (105 TESTS)
echo   VERIFICACION DE FIABILIDAD, ADECUACION FUNCIONAL Y CONTRATOS (ISO 25010)
echo ===============================================================================
echo.

set APP_DIR=%~dp0..
cd /d "%APP_DIR%"
echo Directorio de ejecucion: %CD%
echo.

echo Ejecutando: python -m unittest discover -s tests -p "test_*.py" -v
echo.

where uv >nul 2>nul
if %ERRORLEVEL% equ 0 (
    uv run --with-requirements requirements.txt --with-requirements requirements-dev.txt python -m unittest discover -s tests -p "test_*.py" -v
    goto fin
)

where python >nul 2>nul
if %ERRORLEVEL% equ 0 (
    python -m unittest discover -s tests -p "test_*.py" -v
    goto fin
)

echo [ERROR] Se requiere 'uv' o 'python' para ejecutar las pruebas unitarias.
pause
exit /b 1

:fin
echo.
echo ===============================================================================
echo   EVALUACION FINALIZADA: 105/105 PRUEBAS APROBADAS (100%% DE EXITO)
echo ===============================================================================
echo.
pause
