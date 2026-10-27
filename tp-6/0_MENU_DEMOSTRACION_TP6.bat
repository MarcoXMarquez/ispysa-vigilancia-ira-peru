@echo off
chcp 65001 >nul
title Demostración Integral TP-6 — ISO/IEC 25010 (ISPySA-Pneumonia)
cls

:menu
cls
echo ===============================================================================
echo   TRABAJO PARCIAL 6 (TP-6): APLICACION DE LA NORMA ISO/IEC 25010
echo   SISTEMA DE VIGILANCIA EPIDEMIOLOGICA: ISPySA-Pneumonia (PERU 2000-2023)
echo   UNIVERSIDAD NACIONAL DE SAN AGUSTIN DE AREQUIPA (UNSA - EPIS)
echo   Lider de Proyecto: Marco Antonio Marquez Herrera
echo ===============================================================================
echo.
echo   Seleccione la opcion de demostracion que desea ejecutar:
echo.
echo   [1] Iniciar Tablero de Control Web Interactivo (Streamlit - ISO 25010)
echo   [2] Ejecutar Auditoria de Calidad ISO 25010 (Motor GQM - Calabrese et al.)
echo   [3] Ejecutar Suite Completa de 105 Pruebas Unitarias (tests/)
echo   [4] Medir Cobertura de Codigo (Coverage >= 80%%) y Analisis Flake8
echo   [5] Ejecutar Pruebas E2E de Interfaz y Accesibilidad (Playwright + axe-core)
echo   [6] Abrir Entregables Oficiales (Informe Tecnico DOCX/PDF y Presentacion PPTX/PDF)
echo   [7] Ejecutar Demostracion Completa Automatizada (Auditoria + Tests + Cobertura)
echo.
echo   [0] Salir
echo.
echo ===============================================================================
set /p opt="Ingrese una opcion [0-7] y presione Enter: "

if "%opt%"=="1" goto opc1
if "%opt%"=="2" goto opc2
if "%opt%"=="3" goto opc3
if "%opt%"=="4" goto opc4
if "%opt%"=="5" goto opc5
if "%opt%"=="6" goto opc6
if "%opt%"=="7" goto opc7
if "%opt%"=="0" goto salir

echo.
echo [ERROR] Opcion no valida. Intente nuevamente.
timeout /t 2 >nul
goto menu

:opc1
call "%~dp01_EJECUTAR_APP_STREAMLIT.bat"
goto menu

:opc2
call "%~dp02_EJECUTAR_AUDITORIA_CALIDAD_ISO25010.bat"
goto menu

:opc3
call "%~dp03_EJECUTAR_PRUEBAS_UNITARIAS.bat"
goto menu

:opc4
call "%~dp04_VERIFICAR_QUALITY_GATES_COBERTURA_Y_LINT.bat"
goto menu

:opc5
call "%~dp05_EJECUTAR_PRUEBAS_E2E_PLAYWRIGHT.bat"
goto menu

:opc6
call "%~dp06_ABRIR_ENTREGABLES_TP6.bat"
goto menu

:opc7
cls
echo ===============================================================================
echo   EJECUTANDO DEMOSTRACION COMPLETA AUTOMATIZADA
echo ===============================================================================
echo.
echo (1/3) Ejecutando auditoria automatica ISO 25010...
call "%~dp02_EJECUTAR_AUDITORIA_CALIDAD_ISO25010.bat"
echo.
echo (2/3) Ejecutando suite de 105 pruebas unitarias...
call "%~dp03_EJECUTAR_PRUEBAS_UNITARIAS.bat"
echo.
echo (3/3) Verificando cobertura de codigo y calidad estatica...
call "%~dp04_VERIFICAR_QUALITY_GATES_COBERTURA_Y_LINT.bat"
echo.
echo ===============================================================================
echo   DEMOSTRACION COMPLETA FINALIZADA EXITOSAMENTE
echo ===============================================================================
pause
goto menu

:salir
cls
echo Saliendo de la demostracion TP-6. Hasta luego.
timeout /t 2 >nul
exit /b 0
