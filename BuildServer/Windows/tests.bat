@echo off
rem VERSION_NAME
rem MDANSE_SOURCE_DIR
rem BUILD_TARGET
rem MDANSE_DEPENDENCIES_DIR
rem MDANSE_TEMPORARY_INSTALLATION_DIR

:: %1 --> the build target

if "%1%"=="win32" (
	set BUILD_TARGET=x86
) else (
	set BUILD_TARGET=win-amd64
)

set MDANSE_SOURCE_DIR=%cd%
rem Set the site-packages of the temporary Python
set PYTHON_SCRIPT_DIR=%MDANSE_SOURCE_DIR%\\BuildServer\\Windows\\Build\\Scripts
rem Set the location where the temporary Python will be installed
set MDANSE_TEMPORARY_INSTALLATION_DIR=%MDANSE_SOURCE_DIR%\\BuildServer\\Windows\\Build
rem Set the path to python executable
set PYTHON_EXE=%MDANSE_TEMPORARY_INSTALLATION_DIR%\\python.exe
rem Set the path to MDANSE target
set PYTHONPATH=%MDANSE_SOURCE_DIR%\\build\\lib.%BUILD_TARGET%-2.7;%PYTHONPATH%

rem Perform unitary tests
set MDANSE_UNIT_TESTS_DIR=%MDANSE_SOURCE_DIR%\\Tests\\UnitTests
cd "%MDANSE_UNIT_TESTS_DIR%"
"%PYTHON_EXE%" AllTests.py
rem Exit now if something goes wrong
set STATUS=%ERRORLEVEL%
if %STATUS% neq 0 (
    echo "Failed when running unitary tests"
    exit %STATUS%
)

rem Perform dependencies tests
set MDANSE_UNIT_TESTS_DIR=%MDANSE_SOURCE_DIR%\\Tests\\DependenciesTests
cd "%MDANSE_UNIT_TESTS_DIR%"
"%PYTHON_EXE%" AllTests.py
rem Exit now if something goes wrong
set STATUS=%ERRORLEVEL%
if %STATUS% neq 0 (
    echo "Failed when running dependencies tests"
    exit %STATUS%
)

rem Perform functional tests
set MDANSE_FUNCTIONAL_TESTS_DIR=%MDANSE_SOURCE_DIR%\\Tests\\FunctionalTests\\Jobs
cd "%MDANSE_FUNCTIONAL_TESTS_DIR%"
rem Generate the functional test Python files (one for each job)
rem Remove actual Test files (if any) and the test_BuildJobTests.py file
del Test_*
"%PYTHON_EXE%" BuildJobTests.py
"%PYTHON_EXE%" AllTests.py
::"%PYTHON_EXE%" "%PYTHON_SCRIPT_DIR%\nosetests" --verbosity=3 -P "%MDANSE_FUNCTIONAL_TESTS_DIR%"
rem Exit now if something goes wrong
set STATUS=%ERRORLEVEL%
if %STATUS% neq 0 (
    echo "Failed when running functional tests"
    exit %STATUS%
)

cd %MDANSE_SOURCE_DIR%