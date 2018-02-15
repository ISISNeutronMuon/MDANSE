@echo off

:: %1 --> the source directory
:: %2 --> the python base directory
:: %3 --> the msvc build target (/x86 for win32, /x64 for win-amd64)
:: %4 --> the build options

setlocal EnableDelayedExpansion

cd %1

set PATH=%PATH%;C:\Program Files (x86)\Graphviz2.38\bin

:: This is the Miscrosoft SDK version needed for the build of python 2.7 extensions
call "C:\Program Files\Microsoft SDKs\Windows\v7.0\Bin\SetEnv.cmd" /release %3

set DISTUTILS_USE_SDK=1
set MSsdk=1

%2\python.exe setup.py build %4
%2\python.exe setup.py install

exit %errorlevel%
