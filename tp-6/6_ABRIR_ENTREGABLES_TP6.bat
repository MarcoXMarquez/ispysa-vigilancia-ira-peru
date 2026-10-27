@echo off
chcp 65001 >nul
title [6/6] Entregables Oficiales TP-6 — Documentación y Presentación
cls

echo ===============================================================================
echo   DEMOSTRACION 6: ACCESO A LOS ENTREGABLES OFICIALES DEL TP-6
echo   UNIVERSIDAD NACIONAL DE SAN AGUSTIN DE AREQUIPA (UNSA - EPIS)
echo ===============================================================================
echo.

set TP6_DIR=%~dp0..\..\..\TP-6
if not exist "%TP6_DIR%" (
    set TP6_DIR=%~dp0..\..\TP-6
)

cd /d "%TP6_DIR%"
echo Directorio de entregables: %CD%
echo.

echo Archivos disponibles:
echo.
if exist "reporte_calidad_iso25010_tp6.docx" (
    echo   [1] Informe Tecnico Academico (Word): reporte_calidad_iso25010_tp6.docx
)
if exist "reporte_calidad_iso25010_tp6.pdf" (
    echo   [2] Informe Tecnico Academico (PDF):  reporte_calidad_iso25010_tp6.pdf
)
if exist "presentacion_iso25010_tp6.pptx" (
    echo   [3] Presentacion en Ingles (PPTX):     presentacion_iso25010_tp6.pptx
)
if exist "presentacion_iso25010_tp6.pdf" (
    echo   [4] Presentacion en Ingles (PDF):      presentacion_iso25010_tp6.pdf
)

echo.
echo ===============================================================================
echo   Seleccione el documento que desea abrir con su visor predeterminado:
echo   [1] Abrir Informe Tecnico en PDF
echo   [2] Abrir Presentacion de Diapositivas en PDF
echo   [3] Abrir Informe en DOCX (Microsoft Word)
echo   [4] Abrir Presentacion en PPTX (PowerPoint)
echo   [5] Abrir Carpeta contenedora de entregables en el Explorador de Windows
echo   [0] Volver al menu principal
echo ===============================================================================
set /p doc_opt="Ingrese una opcion [0-5]: "

if "%doc_opt%"=="1" (
    start "" "reporte_calidad_iso25010_tp6.pdf"
    goto fin
)
if "%doc_opt%"=="2" (
    start "" "presentacion_iso25010_tp6.pdf"
    goto fin
)
if "%doc_opt%"=="3" (
    start "" "reporte_calidad_iso25010_tp6.docx"
    goto fin
)
if "%doc_opt%"=="4" (
    start "" "presentacion_iso25010_tp6.pptx"
    goto fin
)
if "%doc_opt%"=="5" (
    explorer .
    goto fin
)

:fin
echo.
pause
