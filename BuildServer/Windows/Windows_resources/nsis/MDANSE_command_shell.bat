@ECHO OFF

:: set white on gray background
COLOR B

:: set the title of the MDANSE shell
TITLE MDANSE command shell

:: append python path to the PATH
SET PATH="%~dp0";%PATH%

:: get rid of any third-party program that may alter the PYTHONHOME and PYTHONPATH
SET PYTHONHOME=
SET PYTHONPATH=
