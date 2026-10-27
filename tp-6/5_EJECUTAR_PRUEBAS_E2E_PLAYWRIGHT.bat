@echo off
chcp 65001 >nul
title [5/6] Pruebas E2E de Interfaz y Accesibilidad (Playwright + axe-core)
cls

echo ===============================================================================
echo   DEMOSTRACION 5: PRUEBAS E2E Y ACCESIBILIDAD (PLAYWRIGHT + AXE-CORE)
echo   ESTANDARES: WCAG 2.1 AA (Accesibilidad Web) y Protocolo de 3 Corridas
echo ===============================================================================
echo.

set PLAYWRIGHT_DIR=%~dp0..\..\tests_playwright
if not exist "%PLAYWRIGHT_DIR%\run_consecutive_tests.js" (
    echo [ERROR] No se encontro el directorio de Playwright en: %PLAYWRIGHT_DIR%
    pause
    exit /b 1
)

cd /d "%PLAYWRIGHT_DIR%"
echo Directorio de pruebas E2E: %CD%
echo.

echo [Paso 1/2] Verificando que la aplicacion Streamlit este activa en http://localhost:8501 ...
powershell -Command "$client = New-Object System.Net.Sockets.TcpClient; try { $client.Connect('127.0.0.1', 8501); Write-Host '[OK] Servidor Streamlit detectado en puerto 8501.' -ForegroundColor Green } catch { Write-Host '[ALERTA] No se detecto Streamlit en el puerto 8501. Por favor inicie primero: 1_EJECUTAR_APP_STREAMLIT.bat' -ForegroundColor Yellow } finally { $client.Close() }"

echo.
echo [Paso 2/2] Ejecutando protocolo de 3 corridas consecutivas con Playwright y axe-core...
echo.

where node >nul 2>nul
if %ERRORLEVEL% equ 0 (
    node run_consecutive_tests.js
    goto fin
)

where npx >nul 2>nul
if %ERRORLEVEL% equ 0 (
    npx playwright test
    goto fin
)

echo [ERROR] Se requiere Node.js instalado en el sistema para ejecutar Playwright.
pause
exit /b 1

:fin
echo.
echo ===============================================================================
echo   EVALUACION E2E FINALIZADA (Resumen en execution_summary_3runs.json)
echo ===============================================================================
echo.
pause
