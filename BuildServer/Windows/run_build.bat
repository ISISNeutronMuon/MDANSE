@echo off

:: %1 --> the build target

set MDANSE_SOURCE_DIR=%cd%

rem Set the location of the MDANSE CI scripts
set BUILD_SCRIPT_DIR=%MDANSE_SOURCE_DIR%\\BuildServer\\Windows

rem Set the location where the temporary Python will be installed
set PYTHON_DIR=%MDANSE_SOURCE_DIR%\\BuildServer\\Windows\\Build

rem Set the site-packages of the temporary Python
set PYTHON_SCRIPT_DIR=%MDANSE_SOURCE_DIR%\\BuildServer\\Windows\\Build\\Scripts

rem Set the site-packages of the temporary Python
set PYTHON_SITE_PACKAGES_DIR=%MDANSE_SOURCE_DIR%\\BuildServer\\Windows\\Build\\Lib\\site-packages

rem Set the path to python executable
set PYTHON_EXE=%PYTHON_DIR%\\python.exe

set PATH="C:\Program Files (x86)\\Graphviz2.38\\bin";%PATH%

set BUILD_TARGET=%1%

if "%BUILD_TARGET%"=="win32" (
	set MSVC_BUILD_TARGET=x86
) else (
	set BUILD_TARGET=win-amd64
	set MSVC_BUILD_TARGET=x64
)

rem This is the env var used by distutils to find the MSVC framework to be used for compiling extension
rem see https://stackoverflow.com/questions/2817869/error-unable-to-find-vcvarsall-bat for more info
rem For the sake of code safety, this should be the same framework used to build Python itself
rem see http://p-nand-q.com/python/building-python-27-with-vs2010.html for more info
set VS90COMNTOOLS=C:\Users\ci\AppData\Local\Programs\Common\Microsoft\Visual C++ for Python\9.0\\Common7\\Tools

rem Set th directory where the MDANSE dependencies are stored
set MDANSE_DEPENDENCIES_DIR=C:\\Projects\\mdanse\\resources\\dependencies\\%BUILD_TARGET%

echo "Removing temporary Python dir: %PYTHON_DIR%"
rmdir /S /Q "%PYTHON_DIR%"

rem Set the path to python installer
set PYTHON_VERSION=2.7.6.%BUILD_TARGET%
set PYTHON_INSTALLER=%MDANSE_DEPENDENCIES_DIR%\\python-%PYTHON_VERSION%.msi

echo "Extracting python %PYTHON_INSTALLER% in %PYTHON_DIR%"
cmd /c msiexec  /L* pythonlog.txt /qn /a "%PYTHON_INSTALLER%" TARGETDIR="%PYTHON_DIR%"

rem Exit now if something goes wrong
if %ERRORLEVEL% neq 0 (
    echo "Failed to extract python"
    exit %ERRORLEVEL%
)

rm pythonlog.txt

set ERRORLEVEL=0

rem Clean up python a bit, to keep the package size down
echo "Cleaning up Python"
rmdir /S /Q "%PYTHON_DIR%\\%PYTHON_INSTALLER%"
rmdir /S /Q "%PYTHON_DIR%\\Doc"
rmdir /S /Q "%PYTHON_DIR%\\Lib\\site-packages"
rmdir /S /Q "%PYTHON_DIR%\\Lib\\test"
rmdir /S /Q "%PYTHON_DIR%\\Tools\\Scripts"
rmdir /S /Q "%PYTHON_DIR%\\tcl"
rmdir /S /Q "%PYTHON_DIR%\\NEWS.txt"
rmdir /S /Q "%PYTHON_DIR%\\Doc"

mkdir "%PYTHON_DIR%\\Lib\\site-packages"
mkdir "%PYTHON_DIR%\\Scripts"

cd "%MDANSE_DEPENDENCIES_DIR%"

echo "Extracting dependencies"

rem extract setuptools
7z x -y setuptools-28.7.1.%BUILD_TARGET%.exe PURELIB

rem extract numpy
7z x -y numpy-MKL-1.8.0.%BUILD_TARGET%-py2.7.exe PLATLIB

rem extract matplotlib and its dependencies
7z x -y pyparsing-2.0.1.%BUILD_TARGET%-py2.7.exe PURELIB
7z x -y python-dateutil-2.2.%BUILD_TARGET%-py2.7.exe PURELIB
7z x -y pytz-2013.9.%BUILD_TARGET%-py2.7.exe PURELIB
7z x -y six-1.5.2.%BUILD_TARGET%-py2.7.exe PURELIB
7z x -y matplotlib-1.3.1.%BUILD_TARGET%-py2.7.exe PLATLIB

rem Cython
7z x -y Cython-0.19.2.%BUILD_TARGET%-py2.7.exe PLATLIB
7z x -y Cython-0.19.2.%BUILD_TARGET%-py2.7.exe SCRIPTS

rem extract Pyro
7z x -y Pyro-3.16.%BUILD_TARGET%.exe PURELIB

rem extract Sphinx and its dependencies
7z x -y alabaster-0.7.5.%BUILD_TARGET%.exe PURELIB
7z x -y Pygments-2.0.2.%BUILD_TARGET%.exe PURELIB
7z x -y Pygments-2.0.2.%BUILD_TARGET%.exe SCRIPTS
7z x -y Babel-1.3.%BUILD_TARGET%.exe PURELIB
7z x -y Babel-1.3.%BUILD_TARGET%.exe SCRIPTS
7z x -y MarkupSafe-0.23.%BUILD_TARGET%-py2.7.exe PLATLIB
7z x -y Jinja2-2.7.3.%BUILD_TARGET%.exe PURELIB
7z x -y docutils-0.12.%BUILD_TARGET%.exe PURELIB
7z x -y docutils-0.12.%BUILD_TARGET%.exe SCRIPTS
7z x -y Sphinx-1.3.1.%BUILD_TARGET%.exe PURELIB
7z x -y sphinx_rtd_theme-0.1.8.%BUILD_TARGET%.exe PURELIB

rem extract nose
7z x -y nose-1.3.7.%BUILD_TARGET%.exe PURELIB
7z x -y nose-1.3.7.%BUILD_TARGET%.exe SCRIPTS

rem extract VTK
7z x -y VTK-5.10.1.%BUILD_TARGET%-py2.7.exe PURELIB

rem extract wxPython and its dependencies
7z x -y wxPython-common-2.8.12.1.%BUILD_TARGET%-py2.7.exe PURELIB
7z x -y wxPython-2.8.12.1.%BUILD_TARGET%-py2.7.exe PLATLIB

rem extract netcdf
7z x -y netCDF4.6.0.%BUILD_TARGET%.exe $_OUTDIR

rem move the packages to the target directory
echo "Moving dependencies to %BUILD_TARGET%"

mv PURELIB\\pkg_resources "%PYTHON_SITE_PACKAGES_DIR%\\pkg_resources"

mv PLATLIB\\numpy "%PYTHON_SITE_PACKAGES_DIR%\\numpy"

mv PURELIB\\dateutil "%PYTHON_SITE_PACKAGES_DIR%\\dateutil"
mv PURELIB\\pyparsing.py "%PYTHON_SITE_PACKAGES_DIR%\\pyparsing.py"
mv PURELIB\\pytz "%PYTHON_SITE_PACKAGES_DIR%\\pytz"
mv PURELIB\\six.py "%PYTHON_SITE_PACKAGES_DIR%\\six.py"
mv PLATLIB\\matplotlib "%PYTHON_SITE_PACKAGES_DIR%\\matplotlib"

mv PLATLIB\\Cython "%PYTHON_SITE_PACKAGES_DIR%\\Cython"
mv SCRIPTS\\cython.py "%PYTHON_SCRIPT_DIR%\\cython.py"
cp "%PYTHON_SCRIPT_DIR%\\cython.py" "%PYTHON_SITE_PACKAGES_DIR%\\cython.py"
mv PURELIB\\Pyro "%PYTHON_SITE_PACKAGES_DIR%\\Pyro"

mv PURELIB\\alabaster "%PYTHON_SITE_PACKAGES_DIR%\\alabaster"
mv PURELIB\\pygments "%PYTHON_SITE_PACKAGES_DIR%\\pygments"
move /Y SCRIPTS\\pygment* "%PYTHON_SCRIPT_DIR%"
mv PURELIB\\babel "%PYTHON_SITE_PACKAGES_DIR%\\babel"
move /Y SCRIPTS\\pybabel* "%PYTHON_SCRIPT_DIR%"
mv PLATLIB\\markupsafe "%PYTHON_SITE_PACKAGES_DIR%\\markupsafe"
mv PURELIB\\jinja2 "%PYTHON_SITE_PACKAGES_DIR%\\jinja2"
mv PURELIB\\docutils "%PYTHON_SITE_PACKAGES_DIR%\\docutils"
move /Y SCRIPTS\\rst* "%PYTHON_SCRIPT_DIR%"
mv PURELIB\\sphinx "%PYTHON_SITE_PACKAGES_DIR%\\sphinx"
mv PURELIB\\sphinx_rtd_theme "%PYTHON_SITE_PACKAGES_DIR%\\sphinx_rtd_theme"

mv PURELIB\\nose "%PYTHON_SITE_PACKAGES_DIR%\\nose"
mv SCRIPTS\\nosetests "%PYTHON_SCRIPT_DIR%"

mv PURELIB\\vtk "%PYTHON_SITE_PACKAGES_DIR%\\vtk"

mv PURELIB\\wx.pth "%PYTHON_SITE_PACKAGES_DIR%"
mv PURELIB\\wxversion.py "%PYTHON_SITE_PACKAGES_DIR%"
mv PLATLIB\\wx-2.8-msw-unicode "%PYTHON_SITE_PACKAGES_DIR%\\wx-2.8-msw-unicode"

move /Y $_OUTDIR\\bin\\netcdf.dll .
move /Y $_OUTDIR\\include\\netcdf.h .
move /Y $_OUTDIR\\lib\\netcdf.lib .

rmdir /S /Q $_OUTDIR

rem build the ILL version of ScientificPython
rmdir /S /Q scientific-python
git clone https://code.ill.fr/scientific-software/scientific-python.git
cd scientific-python
git checkout master
%PYTHON_EXE% setup.py build --netcdf_prefix="%MDANSE_DEPENDENCIES_DIR%" --netcdf_dll="%MDANSE_DEPENDENCIES_DIR%"
%PYTHON_EXE% setup.py install
rmdir /S /Q scientific-python
cd ..

rem move the netcdf library and header files  prior building MMTK
mv netcdf.h "%PYTHON_DIR%\\include\\Scientific"
mv netcdf.dll "%PYTHON_DIR%\\Lib\\site-packages\\Scientific"
rm netcdf.lib

rem build the ILL version of MMTK
rmdir /S /Q mmtk
git clone https://code.ill.fr/scientific-software/mmtk.git
cd mmtk
git checkout master
%PYTHON_EXE% setup.py build
%PYTHON_EXE% setup.py install
rmdir /S /Q mmtk
cd ..

rmdir /S /Q DATA
rmdir /S /Q PLATLIB
rmdir /S /Q PURELIB
rmdir /S /Q SCRIPTS

cd "%MDANSE_SOURCE_DIR%"

rem Update the __pkginfo__ file with the current commit
for /f %%i in ('git rev-parse --short HEAD') do set COMMIT_ID=%%i
sed -i "s/.*__commit__.*/__commit__ = \"%COMMIT_ID%\"/" MDANSE/__pkginfo__.py

rem Get revision number from GIT
echo "Commit id %COMMIT_ID%"

rem Go back to the MDANSE source directory and build and install it
cd "%MDANSE_SOURCE_DIR%"
%PYTHON_EXE% setup.py build
%PYTHON_EXE% setup.py install

rem Exit now if unable to build
if %ERRORLEVEL% neq 0 (
    echo "Failed to build MDANSE"
    exit %ERRORLEVEL%
)

exit 0
