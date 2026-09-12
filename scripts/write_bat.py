from pathlib import Path

bat_text = """@echo off
cls
echo ===============================================================================
echo   SISTEMA DE VIGILANCIA Y MONITOREO EPIDEMIOLOGICO IRA - PERU (2000-2023)
echo   TRABAJO INTRODUCTORIO - CURSO: CALIDAD DE SOFTWARE
echo   CONFORME A NORMAS ISO 9241-11, ISO 9241-210, ISO 9241-110, ISO 9241-12
echo ===============================================================================
echo.

set BASE_DIR=%~dp0
if exist "%BASE_DIR%ISPySA-Pneumonia-main\\ISPySA-Pneumonia-main\\app.py" (
    cd /d "%BASE_DIR%ISPySA-Pneumonia-main\\ISPySA-Pneumonia-main"
) else (
    cd /d "%BASE_DIR%"
)

echo Directorio de trabajo: %CD%
echo.

echo [1/3] Verificando entorno uv / Python...
where uv >nul 2>nul
if %ERRORLEVEL% equ 0 (
    echo [OK] Se detecto motor 'uv' de alto rendimiento.
    echo.
    echo [2/3] Levantando servidor web Streamlit en puerto 8501...
    echo [3/3] Abriendo automaticamente http://localhost:8501 en el navegador...
    echo.
    echo ===============================================================================
    echo Para detener la aplicacion presione Ctrl+C en esta consola.
    echo ===============================================================================
    echo.
    start "" http://localhost:8501
    uv run --with streamlit --with pandas --with plotly --with numpy --with openpyxl python -m streamlit run app.py --server.port 8501 --server.headless true
    goto fin
)

where python >nul 2>nul
if %ERRORLEVEL% equ 0 (
    echo [OK] Se detecto Python.
    echo.
    echo [2/3] Verificando dependencias...
    python -m pip install streamlit plotly pandas numpy openpyxl
    echo.
    echo [3/3] Abriendo http://localhost:8501 en su navegador...
    start "" http://localhost:8501
    python -m streamlit run app.py --server.port 8501 --server.headless true
    goto fin
)

echo [ERROR] No se encontro ni 'uv' ni 'python' en el sistema.
pause

:fin
pause
"""

crlf_bytes = bat_text.replace("\r\n", "\n").replace("\n", "\r\n").encode("ascii")

paths = [
    Path(r"c:\Users\marco\OneDrive\Desktop\TEO-CS\SEMANA 1\ejecutar_aplicativo.bat"),
    Path(r"c:\Users\marco\OneDrive\Desktop\TEO-CS\SEMANA 1\ISPySA-Pneumonia-main\ISPySA-Pneumonia-main\ejecutar_aplicativo.bat")
]

for p in paths:
    with open(p, "wb") as f:
        f.write(crlf_bytes)
    print(f"[OK] Generado exitosamente: {p}")
