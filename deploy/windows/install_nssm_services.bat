@echo off
setlocal

call "%~dp0set_project_env.bat" || exit /b 1

if defined NSSM_EXE (
    if not exist "%NSSM_EXE%" (
        echo NSSM executable not found: "%NSSM_EXE%"
        exit /b 1
    )
    set "NSSM=%NSSM_EXE%"
) else (
    where nssm >nul 2>nul || (
        echo NSSM executable not found in PATH.
        echo Set environment variable NSSM_EXE to your nssm.exe path.
        echo Example: set NSSM_EXE=C:\tools\nssm\win64\nssm.exe
        exit /b 1
    )
    set "NSSM=nssm"
)

set "WINDOWS_LOG_DIR=%PROJECT_ROOT%\logs\windows-services"
if not exist "%WINDOWS_LOG_DIR%" mkdir "%WINDOWS_LOG_DIR%"

call "%~dp0install_one_nssm_service.bat" "%NSSM%" "sg57-backend" "%~dp0run_backend_daphne.bat" "%BACKEND_DIR%" "%WINDOWS_LOG_DIR%\backend.out.log" "%WINDOWS_LOG_DIR%\backend.err.log" || exit /b 1
call "%~dp0install_one_nssm_service.bat" "%NSSM%" "sg57-bokeh" "%~dp0run_bokeh_server.bat" "%BACKEND_DIR%" "%WINDOWS_LOG_DIR%\bokeh.out.log" "%WINDOWS_LOG_DIR%\bokeh.err.log" || exit /b 1
call "%~dp0install_one_nssm_service.bat" "%NSSM%" "sg57-celery-worker" "%~dp0run_celery_worker.bat" "%BACKEND_DIR%" "%WINDOWS_LOG_DIR%\celery-worker.out.log" "%WINDOWS_LOG_DIR%\celery-worker.err.log" || exit /b 1
call "%~dp0install_one_nssm_service.bat" "%NSSM%" "sg57-celery-beat" "%~dp0run_celery_beat.bat" "%BACKEND_DIR%" "%WINDOWS_LOG_DIR%\celery-beat.out.log" "%WINDOWS_LOG_DIR%\celery-beat.err.log" || exit /b 1

echo.
echo Services installed. Start them with:
echo   nssm start sg57-backend
echo   nssm start sg57-bokeh
echo   nssm start sg57-celery-worker
echo   nssm start sg57-celery-beat

exit /b 0
