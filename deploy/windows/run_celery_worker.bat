@echo off
setlocal

call "%~dp0set_project_env.bat" || exit /b 1

pushd "%BACKEND_DIR%" || exit /b 1
"%PYTHON_EXE%" -m celery -A iot_monitor worker -l info --pool=solo
set "EXIT_CODE=%ERRORLEVEL%"
popd

exit /b %EXIT_CODE%
