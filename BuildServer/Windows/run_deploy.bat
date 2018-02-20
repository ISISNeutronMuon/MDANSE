@echo off

set BUILD_TARGET=%1%

set MDANSE_SOURCE_DIR=%cd%

rem Set the location of this script
set BUILD_SCRIPT_DIR=%MDANSE_SOURCE_DIR%\\BuildServer\\Windows

rem Set the location where the temporary Python will be installed
set PYTHON_DIR=%MDANSE_SOURCE_DIR%\\BuildServer\\Windows\\Build

rem Set the script dir of the temporary Python
set PYTHON_SCRIPT_DIR=%MDANSE_SOURCE_DIR%\\BuildServer\\Windows\\Build\\Scripts

for /f %%i in ('git rev-parse --short HEAD') do set MDANSE_GIT_CURRENT_COMMIT=%%i
for /f %%i in ('sed -n 's/__version__.*=.*\"\(.*\)\"/\1/p' MDANSE/__pkginfo__.py') do set MDANSE_VERSION=%%i

if defined CI_BUILD_REF_NAME (
    if "%CI_BUILD_REF_NAME%" == "develop" (
        set MDANSE_VERSION=%VERSION_NAME%-%MDANSE_GIT_CURRENT_COMMIT%
    )
) else (
    set MDANSE_VERSION=%MDANSE_VERSION%-%MDANSE_GIT_CURRENT_COMMIT%
)

rem create the MDANSE installer
echo "Creating nsis installer for target %PYTHON_BUILD_DIR%..."

cd "%BUILD_SCRIPT_DIR%"

makensis /V4 /ONSISlog.txt /DVERSION=%MDANSE_VERSION% /DARCH=%BUILD_TARGET% /DTARGET_DIR=%PYTHON_DIR% MDANSE_installer.nsi

rem Exit now if something goes wrong
if %ERRORLEVEL% neq 0 (
    echo "Failed when packaging MDANSE"
    exit %ERRORLEVEL%
)

rem Remove NSIS log file
rm NSISlog.txt

exit %ERRORLEVEL%

