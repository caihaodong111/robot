@echo off
setlocal

if "%~5"=="" (
    echo Usage: install_one_nssm_service.bat ^<nssm.exe^> ^<service_name^> ^<app_path^> ^<app_dir^> ^<stdout_log^> ^<stderr_log^>
    exit /b 1
)

set "NSSM=%~1"
set "SERVICE_NAME=%~2"
set "APP_PATH=%~3"
set "APP_DIR=%~4"
set "STDOUT_LOG=%~5"
set "STDERR_LOG=%~6"

"%NSSM%" install "%SERVICE_NAME%" "%APP_PATH%" || exit /b 1
"%NSSM%" set "%SERVICE_NAME%" AppDirectory "%APP_DIR%" || exit /b 1
"%NSSM%" set "%SERVICE_NAME%" Start SERVICE_AUTO_START || exit /b 1
"%NSSM%" set "%SERVICE_NAME%" AppExit Default Restart || exit /b 1
"%NSSM%" set "%SERVICE_NAME%" AppStdout "%STDOUT_LOG%" || exit /b 1
"%NSSM%" set "%SERVICE_NAME%" AppStderr "%STDERR_LOG%" || exit /b 1
"%NSSM%" set "%SERVICE_NAME%" AppRotateFiles 1 || exit /b 1
"%NSSM%" set "%SERVICE_NAME%" AppRotateOnline 1 || exit /b 1
"%NSSM%" set "%SERVICE_NAME%" AppRotateBytes 10485760 || exit /b 1

exit /b 0
