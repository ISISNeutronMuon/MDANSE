@echo off

:: Set PYTHONHOME and PYTHONPATH to empty strings to avoid any side-effects due to third-party 
:: programs (e.g. Scienomics) that may set these variables to fulfill their needs 
set PYTHONHOME=
set PYTHONPATH=

set dirname="%~dp0"

set PATH=%dirname%\DLLs;%dirname%\Include;%dirname%\libs;%PATH%

start /B /D %dirname% pythonw.exe Scripts\mdanse_gui