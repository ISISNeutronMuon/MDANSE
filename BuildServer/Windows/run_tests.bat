@echo off

set MDANSE_SOURCE_DIR=%cd%

rem Set the site-packages of the temporary Python
set PYTHON_SCRIPT_DIR=%MDANSE_SOURCE_DIR%\\BuildServer\\Windows\\Build\\Scripts

rem Set the path to python executable
set PYTHON_EXE=%PYTHON_DIR%\\python.exe

set MDANSE_UNIT_TESTS_DIR=%MDANSE_SOURCE_DIR%\\Tests\\UnitTests

cd "%MDANSE_UNIT_TESTS_DIR%"

"%PYTHON_EXE%" "%PYTHON_SCRIPT_DIR%\nosetests" --verbosity=3  -P "%MDANSE_UNIT_TESTS_DIR%"

rem Exit now if something goes wrong
set STATUS=%ERRORLEVEL%
if %STATUS% neq 0 (
    echo "Failed when running unitary tests"
    exit %STATUS%
)

set MDANSE_FUNCTIONAL_TESTS_DIR=%MDANSE_SOURCE_DIR%\\Tests\\FunctionalTests\\Jobs

cd "%MDANSE_FUNCTIONAL_TESTS_DIR%"

rem Generate the functional test Python files (one for each job)
:: Remove actual Test files (if any) and the test_BuildJobTests.py file
del AllTests*
del Build*
%1\python.exe -m nose
::"%PYTHON_EXE%" "%PYTHON_SCRIPT_DIR%\nosetests" --verbosity=3 -P "%MDANSE_FUNCTIONAL_TESTS_DIR%"

rem Exit now if something goes wrong
set STATUS=%ERRORLEVEL%
if %STATUS% neq 0 (
    echo "Failed when running functional tests"
    exit %STATUS%
)

cd %MDANSE_SOURCE_DIR%

exit 0
