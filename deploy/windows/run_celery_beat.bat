@echo off
setlocal

call "%~dp0set_project_env.bat" || exit /b 1

if not exist "%RUN_DIR%" mkdir "%RUN_DIR%"

pushd "%BACKEND_DIR%" || exit /b 1
"%PYTHON_EXE%" -m celery -A iot_monitor beat -l info --schedule "%RUN_DIR%\celerybeat-schedule" --pidfile "%RUN_DIR%\celerybeat.pid"
set "EXIT_CODE=%ERRORLEVEL%"
popd

exit /b %EXIT_CODE%
