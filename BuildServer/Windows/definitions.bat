@echo off

:: %1 --> the build target
set BUILD_TARGET=%1%
if "%BUILD_TARGET%"=="win32" (
	set MSVC_BUILD_TARGET=x86
) else (
	set BUILD_TARGET=win-amd64
	set MSVC_BUILD_TARGET=x64
)

rem Set the source directory
set MDANSE_SOURCE_DIR=%cd%

rem Set th directory where the MDANSE dependencies are stored
set MDANSE_DEPENDENCIES_DIR=C:\\Projects\\mdanse\\resources\\dependencies\\%BUILD_TARGET%

rem Set the location where the temporary Python will be installed
set MDANSE_TEMPORARY_INSTALLATION_DIR=%MDANSE_SOURCE_DIR%\\BuildServer\\Windows\\Build