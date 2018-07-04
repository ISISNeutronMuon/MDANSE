@echo off
rem VERSION_NAME
rem MDANSE_SOURCE_DIR
rem BUILD_TARGET
rem MDANSE_DEPENDENCIES_DIR
rem MDANSE_TEMPORARY_INSTALLATION_DIR

cd "%MDANSE_SOURCE_DIR%"

%PYTHON_EXE% setup.py build_api

set STATUS=%ERRORLEVEL%
rem Exit now if unable to build
if %STATUS% neq 0 (
    echo "Failed to build MDANSE API"
    exit %STATUS%
)

%PYTHON_EXE% setup.py build_help

set STATUS=%ERRORLEVEL%
rem Exit now if unable to build
if %STATUS% neq 0 (
    echo "Failed to build MDANSE embedded documentation"
    exit %STATUS%
)

%PYTHON_EXE% setup.py install
rem Exit now if unable to install
if %STATUS% neq 0 (
    echo "Failed to install MDANSE"
    exit %STATUS%
)

cd "%MDANSE_SOURCE_DIR%\\BuildServer\\Windows"

rem copy LICENSE
copy %MDANSE_SOURCE_DIR%\\LICENSE %MDANSE_SOURCE_DIR%\\BuildServer\\Windows\\Windows_resources\\nsis\\

rem copy CHANGELOG to CHANGELOG.txt (compulsory to be opened by nsis through an external text editor)
copy %MDANSE_SOURCE_DIR%\\CHANGELOG %MDANSE_SOURCE_DIR%\\BuildServer\\Windows\\Windows_resources\\nsis\\CHANGELOG.txt

rem Copy site.py 
copy %MDANSE_SOURCE_DIR%\\BuildServer\\Windows\\Windows_resources\\site.py %MDANSE_TEMPORARY_INSTALLATION_DIR%\\Lib\\

rem Copy Visual dll see https://stackoverflow.com/questions/214852/python-module-dlls to understand why dll copy destination folder must be the Scientific folder
copy "%MDANSE_DEPENDENCIES_DIR%\\NetCDF\\vcruntime140.dll" "%MDANSE_TEMPORARY_INSTALLATION_DIR%\\Lib\\site-packages\\Scientific\\"

rem create the MDANSE installer
echo "Creating nsis installer for target %MDANSE_TEMPORARY_INSTALLATION_DIR%..."
makensis /V4 /ONSISlog.txt /DVERSION=%VERSION_NAME% /DARCH=%BUILD_TARGET% /DTARGET_DIR=%MDANSE_TEMPORARY_INSTALLATION_DIR% %MDANSE_SOURCE_DIR%\\BuildServer\\Windows\\Windows_resources\\nsis\\MDANSE_installer.nsi

set STATUS=%ERRORLEVEL%
rem Exit now if something goes wrong
if %STATUS% neq 0 (
    echo "Failed when packaging MDANSE"
    exit %STATUS%
)

move %MDANSE_TEMPORARY_INSTALLATION_DIR%\\MDANSE*.exe %MDANSE_SOURCE_DIR%\\
rem Remove NSIS log file
del NSISlog.txt

cd %MDANSE_SOURCE_DIR%
