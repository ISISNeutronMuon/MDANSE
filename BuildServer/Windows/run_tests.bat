@echo off

:: %1 --> the python base directory
:: %2 --> the MDANSE source directory

set testsPath=%2\Tests\UnitTests
cd %testsPath%

%1\python.exe %1\Scripts\nosetests --verbosity=3  -P %testsPath%

set testsPath=%2\Tests\FunctionalTests\Jobs
cd %testsPath%

del Test_*
%1\python.exe BuildJobTests.py

%1\python.exe %1\Scripts\nosetests --verbosity=3 %testsPath%\Test_*.py

exit %errorlevel%