@echo off

cd %MDANSE_SOURCE_DIR%

set MDANSE_TEMPORARY_INSTALLATION_DIR="%CONDA%\envs\mdanse"
rem Set the path to python executable
set PYTHON_EXE=%MDANSE_TEMPORARY_INSTALLATION_DIR%\python.exe


rem Prepare the environment for building MDANSE
set PATH=%MDANSE_TEMPORARY_INSTALLATION_DIR%;%MDANSE_TEMPORARY_INSTALLATION_DIR%\Scripts\;%PATH%
rem "%PYTHON_EXE%" setup.py build build_api build_help install
"%PYTHON_EXE%" setup.py install

set STATUS=%ERRORLEVEL%
rem Exit now if unable to build
if %STATUS% neq 0 (
    echo "Failed to build MDANSE Documentation"
    exit %STATUS%
)

rem remove unneeded packages
cd /D %MDANSE_TEMPORARY_INSTALLATION_DIR%\Lib\site-packages
rmdir /s /q PyQT4
rmdir /s /q PyQT4-4.11.4.dist-info
rmdir /s /q matplotlib\mpl-data\sample_data
"%PYTHON_EXE%" -m pip uninstall sphinx Jinja2 MarkupSafe Pygments alabaster babel chardet colorama docutils idna imagesize requests snowballstemmer sphinxcontrib-websupport typing urllib3 -y


cd /D "%GITHUB_WORKSPACE%\BuildServer\Windows"

rem copy LICENSE
copy "%GITHUB_WORKSPACE%\\LICENSE" "%GITHUB_WORKSPACE%\\BuildServer\\Windows\\Resources\\nsis\\"

rem copy CHANGELOG to CHANGELOG.txt (compulsory to be opened by nsis through an external text editor)
copy "%GITHUB_WORKSPACE%\CHANGELOG" "%GITHUB_WORKSPACE%\BuildServer\Windows\Resources\nsis\CHANGELOG.txt"

rem Copy mdanse.pth
copy "%GITHUB_WORKSPACE%\\BuildServer\\Windows\\Resources\\mdanse.pth" "%MDANSE_TEMPORARY_INSTALLATION_DIR%\\Lib\\site-packages"

rem create the MDANSE installer
echo "Creating nsis installer for target %MDANSE_TEMPORARY_INSTALLATION_DIR%..."
makensis /V4 /ONSISlog.txt /DVERSION=%VERSION_NAME% /DARCH=%BUILD_TARGET% /DTARGET_DIR=%MDANSE_TEMPORARY_INSTALLATION_DIR% %GITHUB_WORKSPACE%\\BuildServer\\Windows\\Resources\\nsis\\MDANSE_installer.nsi

set STATUS=%ERRORLEVEL%
rem Exit now if something goes wrong
if %STATUS% neq 0 (
    echo "Failed when packaging MDANSE"
    exit %STATUS%
)

move %MDANSE_TEMPORARY_INSTALLATION_DIR%\\MDANSE*.exe %MDANSE_SOURCE_DIR%\\

cd %MDANSE_SOURCE_DIR%
