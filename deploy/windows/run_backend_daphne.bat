@echo off
setlocal

call "%~dp0set_project_env.bat" || exit /b 1

pushd "%BACKEND_DIR%" || exit /b 1
"%PYTHON_EXE%" -m daphne -b 0.0.0.0 -p %DJANGO_PORT% iot_monitor.asgi:application
set "EXIT_CODE=%ERRORLEVEL%"
popd

exit /b %EXIT_CODE%
