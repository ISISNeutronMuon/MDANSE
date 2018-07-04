@echo off
rem VERSION_NAME
rem MDANSE_SOURCE_DIR
rem BUILD_TARGET
rem MDANSE_DEPENDENCIES_DIR
rem MDANSE_TEMPORARY_INSTALLATION_DIR

rem Set the location of the MDANSE CI scripts
set BUILD_SCRIPT_DIR=%MDANSE_SOURCE_DIR%\\BuildServer\\Windows

rem Set the path to python executable
set PYTHON_EXE=%MDANSE_TEMPORARY_INSTALLATION_DIR%\\python.exe

rem Set the path to NetCDF resources
set NETCDF_RESOURCES_PATH=%MDANSE_DEPENDENCIES_DIR%\\NetCDF

rem This is the env var used by distutils to find the MSVC framework to be used for compiling extension
rem see https://stackoverflow.com/questions/2817869/error-unable-to-find-vcvarsall-bat for more info
rem For the sake of code safety, this should be the same framework used to build Python itself
rem see http://p-nand-q.com/python/building-python-27-with-vs2010.html for more info
set VS90COMNTOOLS=C:\Users\\ci\\AppData\\Local\\Programs\\Common\\Microsoft\\Visual C++ for Python\\9.0\\Common7\\Tools

rem copy target Python
rmdir /S /Q %MDANSE_TEMPORARY_INSTALLATION_DIR%
mkdir %MDANSE_TEMPORARY_INSTALLATION_DIR%
xcopy /E /Y /Q %MDANSE_DEPENDENCIES_DIR%\\Python %MDANSE_TEMPORARY_INSTALLATION_DIR%
rem move %MDANSE_TEMPORARY_INSTALLATION_DIR%\\..\\Python %MDANSE_TEMPORARY_INSTALLATION_DIR%

rem build the ILL version of ScientificPython
cd %MDANSE_TEMPORARY_INSTALLATION_DIR%
rmdir /S /Q scientific-python
git clone https://code.ill.fr/scientific-software/scientific-python.git
cd scientific-python
git checkout master
%PYTHON_EXE% setup.py build --netcdf_prefix="%MDANSE_DEPENDENCIES_DIR%\\NetCDF" --netcdf_dll="%MDANSE_DEPENDENCIES_DIR%\\NetCDF"
set STATUS=%ERRORLEVEL%
rem Exit now if unable to build
if %STATUS% neq 0 (
    echo "Failed to build Scientific"
    exit %STATUS%
)
%PYTHON_EXE% setup.py install
rem Exit now if unable to install
if %STATUS% neq 0 (
    echo "Failed to install Scientific"
    exit %STATUS%
)
rem Copy netcdf dependencies
copy "%MDANSE_DEPENDENCIES_DIR%\\NetCDF\\netcdf.dll" "%MDANSE_TEMPORARY_INSTALLATION_DIR%\\Lib\\site-packages\\Scientific\\"
copy "%MDANSE_DEPENDENCIES_DIR%\\NetCDF\\netcdf.h" "%MDANSE_TEMPORARY_INSTALLATION_DIR%\\include\\Scientific\\"
cd ..
rmdir /S /Q scientific-python

rem build the ILL version of MMTK
cd %MDANSE_TEMPORARY_INSTALLATION_DIR%
rmdir /S /Q mmtk
git clone https://code.ill.fr/scientific-software/mmtk.git
cd mmtk
git checkout master
%PYTHON_EXE% setup.py build
set STATUS=%ERRORLEVEL%
rem Exit now if unable to build
if %STATUS% neq 0 (
    echo "Failed to build MMTK"
    exit %STATUS%
)
%PYTHON_EXE% setup.py install
rem Exit now if unable to install
if %STATUS% neq 0 (
    echo "Failed to install MMTK"
    exit %STATUS%
)
cd ..
rmdir /S /Q mmtk

rem Go back to the MDANSE source directory and build and install it
cd "%MDANSE_SOURCE_DIR%"
%PYTHON_EXE% setup.py build
set STATUS=%ERRORLEVEL%
rem Exit now if unable to build
if %STATUS% neq 0 (
    echo "Failed to build MDANSE"
    exit %STATUS%
)

cd %MDANSE_SOURCE_DIR%
