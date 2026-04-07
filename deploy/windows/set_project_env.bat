@echo off
setlocal

set "SCRIPT_DIR=%~dp0"
for %%I in ("%SCRIPT_DIR%..\..") do set "PROJECT_ROOT=%%~fI"
set "BACKEND_DIR=%PROJECT_ROOT%\backend"
set "RUN_DIR=%PROJECT_ROOT%\run"

if defined SG57_PYTHON (
    set "PYTHON_EXE=%SG57_PYTHON%"
) else (
    set "PYTHON_EXE=C:\RobotUI\venv57\Scripts\python.exe"
)

if not exist "%PYTHON_EXE%" (
    echo Python executable not found: "%PYTHON_EXE%"
    echo Set environment variable SG57_PYTHON to your venv python.exe path.
    exit /b 1
)

if not defined DJANGO_PORT set "DJANGO_PORT=8001"
if not defined BOKEH_PORT set "BOKEH_PORT=5008"

endlocal & (
    set "PROJECT_ROOT=%PROJECT_ROOT%"
    set "BACKEND_DIR=%BACKEND_DIR%"
    set "RUN_DIR=%RUN_DIR%"
    set "PYTHON_EXE=%PYTHON_EXE%"
    set "DJANGO_PORT=%DJANGO_PORT%"
    set "BOKEH_PORT=%BOKEH_PORT%"
)

exit /b 0
