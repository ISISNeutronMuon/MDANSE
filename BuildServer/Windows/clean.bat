@echo off
rem VERSION_NAME
rem MDANSE_SOURCE_DIR
rem BUILD_TARGET
rem MDANSE_DEPENDENCIES_DIR
rem MDANSE_TEMPORARY_INSTALLATION_DIR

rmdir /S /Q build
rmdir /S /Q BuildServer\\Windows\\Build

rmdir /S /Q %MDANSE_TEMPORARY_INSTALLATION_DIR%\\scientific-python
rmdir /S /Q %MDANSE_TEMPORARY_INSTALLATION_DIR%\\mmtk