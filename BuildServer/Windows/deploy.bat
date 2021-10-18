@echo off

cd %MDANSE_SOURCE_DIR%

rem Set the path to python executable
set PYTHON_EXE=%HOME%\python\python.exe

rem This is the env var used by distutils to find the MSVC framework to be used for compiling extension
rem see https://stackoverflow.com/questions/2817869/error-unable-to-find-vcvarsall-bat for more info
rem For the sake of code safety, this should be the same framework used to build Python itself
rem see http://p-nand-q.com/python/building-python-27-with-vs2010.html for more info
set VS90COMNTOOLS="C:\Program Files (x86)\Microsoft Visual Studio 9.0\Common7\Tools"
echo "Starting MDANSE build"
%PYTHON_EXE% setup.py build build_api build_help install

set STATUS=%ERRORLEVEL%
rem Exit now if unable to build
if %STATUS% neq 0 (
    echo "Failed to build MDANSE Documentation"
    exit %STATUS%
)
echo "Finished MDANSE build"
cd "%MDANSE_SOURCE_DIR%\BuildServer\Windows"

rem copy LICENSE
copy %MDANSE_SOURCE_DIR%\\LICENSE %MDANSE_SOURCE_DIR%\\BuildServer\\Windows\\Resources\\nsis\\

rem copy CHANGELOG to CHANGELOG.txt (compulsory to be opened by nsis through an external text editor)
copy %MDANSE_SOURCE_DIR%\\CHANGELOG %MDANSE_SOURCE_DIR%\\BuildServer\\Windows\\Resources\\nsis\\CHANGELOG.txt

rem Copy site.py 
copy %MDANSE_SOURCE_DIR%\\BuildServer\\Windows\\Resources\\site.py %MDANSE_TEMPORARY_INSTALLATION_DIR%\\Lib\\

rem Copy Visual dll see https://stackoverflow.com/questions/214852/python-module-dlls to understand why dll copy destination folder must be the Scientific folder
copy "%MDANSE_DEPENDENCIES_DIR%\\NetCDF\\vcruntime140.dll" "%MDANSE_TEMPORARY_INSTALLATION_DIR%\\Lib\\site-packages\\Scientific\\"

rem create the MDANSE installer
echo "Creating nsis installer for target %MDANSE_TEMPORARY_INSTALLATION_DIR%..."
makensis /V4 /ONSISlog.txt /DVERSION=%VERSION_NAME% /DARCH=%BUILD_TARGET% /DTARGET_DIR=%MDANSE_TEMPORARY_INSTALLATION_DIR% %MDANSE_SOURCE_DIR%\\BuildServer\\Windows\\Resources\\nsis\\MDANSE_installer.nsi

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
