@echo off

:: %1 --> the build target
set BUILD_TARGET=%1%
if "%BUILD_TARGET%"=="win32" (
	set MSVC_BUILD_TARGET=x86
) else (
	set BUILD_TARGET=win-amd64
	set MSVC_BUILD_TARGET=x64
)