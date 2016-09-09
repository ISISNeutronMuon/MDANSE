#!/bin/bash

CI_PROJECT_DIR_WIN=$(cygpath -a -w ${CI_PROJECT_DIR})

# Change working directory to the directory the script is in
# http://stackoverflow.com/a/246128
SCRIPT_DIR="${CI_PROJECT_DIR}/BuildServer/Windows"

# This is the directory that will contain the temporary installation
TARGET_DIR="${CI_PROJECT_DIR_WIN}\\BuildServer\\Windows\\Build"

#############################
# Build the packages
#############################

cd "${SCRIPT_DIR}"

echo "Running tests"
cmd /V:ON /E:ON /C "run_tests.bat" "${TARGET_DIR}" "${CI_PROJECT_DIR_WIN}"

# Exit now if unable to run tests
if [ $? -ne 0 ]; then
	status = $?
	echo "One or several unit tests failed"
	exit status
fi

