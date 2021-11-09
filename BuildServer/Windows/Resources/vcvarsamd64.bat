@SET VSINSTALLDIR=C:\Program Files (x86)\Microsoft Visual Studio 9.0
@SET VCINSTALLDIR=C:\Program Files (x86)\Microsoft Visual Studio 9.0\VC
@SET FrameworkDir=C:\WINDOWS\Microsoft.NET\Framework64
@SET FrameworkVersion=v2.0.50727
@SET Framework35Version=v3.5
@if "%VSINSTALLDIR%"=="" goto error_no_VSINSTALLDIR
@if "%VCINSTALLDIR%"=="" goto error_no_VCINSTALLDIR

@echo Setting environment for using Microsoft Visual Studio 2008 Beta2 x64 tools.

@set WindowsSdkDir="C:\Program Files\Microsoft SDKs\Windows\v6.0A\"

@if not "%WindowsSdkDir%" == "" (
	set "PATH=%WindowsSdkDir%bin\x64;%WindowsSdkDir%bin\win64\x64;%WindowsSdkDir%bin;%PATH%"
	set "INCLUDE=%WindowsSdkDir%include;%INCLUDE%"
	set "LIB=%WindowsSdkDir%lib\x64;%LIB%"
)

@set PATH=%VCINSTALLDIR%\BIN\amd64;%FrameworkDir%\%Framework35Version%;%FrameworkDir%\%Framework35Version%\Microsoft .NET Framework 3.5 (Pre-Release Version);%FrameworkDir%\%FrameworkVersion%;%VCINSTALLDIR%\VCPackages;%VSINSTALLDIR%\Common7\IDE;%VSINSTALLDIR%\Common7\Tools;%VSINSTALLDIR%\Common7\Tools\bin;%PATH%
@set INCLUDE=%VCINSTALLDIR%\ATLMFC\INCLUDE;%VCINSTALLDIR%\INCLUDE;%INCLUDE%
@set LIB=%VCINSTALLDIR%\ATLMFC\LIB\amd64;%VCINSTALLDIR%\LIB\amd64;%LIB%

@set LIBPATH=%FrameworkDir%\%Framework35Version%;%FrameworkDir%\%FrameworkVersion%;%FrameworkDir%\%Framework35Version%;%FrameworkDir%\%FrameworkVersion%;%VCINSTALLDIR%\ATLMFC\LIB\amd64;%VCINSTALLDIR%\LIB\amd64;%LIBPATH%

@goto end

:error_no_VSINSTALLDIR
@echo ERROR: VSINSTALLDIR variable is not set. 
@goto end

:error_no_VCINSTALLDIR
@echo ERROR: VCINSTALLDIR variable is not set. 
@goto end

:end
