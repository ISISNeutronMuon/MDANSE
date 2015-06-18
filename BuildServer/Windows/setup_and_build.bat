@echo off

:: %1 --> the python base directory
:: %2 --> the msvc build target (/x86 for win32, /x64 for win-amd64)

setlocal EnableDelayedExpansion

:: This is the Miscrosoft SDF version needed for the build of python 2.7 extensions
call "C:\Program Files\Microsoft SDKs\Windows\v7.0\Bin\SetEnv.cmd" /release %2

set DISTUTILS_USE_SDK=1

%1\python.exe setup.py build
%1\python.exe setup.py install

exit

