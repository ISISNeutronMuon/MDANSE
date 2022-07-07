@ECHO OFF

:: set white on gray background
COLOR B

:: set the title of the MDANSE shell
TITLE MDANSE command shell

:: append python path to the PATH
set dirname=%~dp0
set PATH=%dirname%\Library;%dirname%\Library\bin;%dirname%\Library\include;%dirname%\Library\lib;%dirname%DLLs;%dirname%Include;%dirname%libs;%PATH%

:: get rid of any third-party program that may alter the PYTHONHOME and PYTHONPATH
SET PYTHONHOME=
SET PYTHONPATH=
