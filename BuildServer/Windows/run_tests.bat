@echo off

:: %1 --> the python base directory
:: %2 --> the MDANSE source directory

set testsPath=%2\Tests\UnitTests
cd %testsPath%

%1\python.exe %1\Scripts\nosetests --verbosity=3  -P %testsPath%

set testsPath=%2\Tests\FunctionalTests\Jobs
cd %testsPath%

:: Remove actual Test files (if any) and the test_BuildJobTests.py file
del Test_*
%1\python.exe BuildJobTests.py

del AllTests*
del Build*
%1\python.exe -m nose

exit %errorlevel%