@echo off

rem Set the location of the MDANSE CI scripts
set BUILD_SCRIPT_DIR=%GITHUB_WORKSPACE%\\BuildServer\\Windows

rem Set the path to NetCDF resources
set NETCDF_RESOURCES_PATH="%HOME%\netcdf\"

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
python setup.py build --netcdf_prefix="%NETCDF_RESOURCES_PATH%" --netcdf_dll="%NETCDF_RESOURCES_PATH%" install
set STATUS=%ERRORLEVEL%
rem Exit now if unable to build
if %STATUS% neq 0 (
    echo "Failed to build Scientific"
    exit %STATUS%
)

rem Copy netcdf dependencies
copy "%NETCDF_RESOURCES_PATH%\\netcdf.dll" "%MDANSE_TEMPORARY_INSTALLATION_DIR%\\Lib\\site-packages\\Scientific\\"
copy "%NETCDF_RESOURCES_PATH%\\netcdf.h" "%MDANSE_TEMPORARY_INSTALLATION_DIR%\\include\\Scientific\\"
cd ..
rmdir /S /Q scientific-python

rem build the ILL version of MMTK
cd %MDANSE_TEMPORARY_INSTALLATION_DIR%
rmdir /S /Q mmtk
git clone https://code.ill.fr/scientific-software/mmtk.git
cd mmtk
git checkout master
python setup.py build install
set STATUS=%ERRORLEVEL%
rem Exit now if unable to build
if %STATUS% neq 0 (
    echo "Failed to build MMTK"
    exit %STATUS%
)

cd ..
rmdir /S /Q mmtk

rem Go back to the MDANSE source directory and build and install it
cd "%MDANSE_SOURCE_DIR%"
python setup.py build install
set STATUS=%ERRORLEVEL%
rem Exit now if unable to build
if %STATUS% neq 0 (
    echo "Failed to build MDANSE"
    exit %STATUS%
)

cd %MDANSE_SOURCE_DIR%
