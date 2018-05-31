#!/bin/bash

#############################
# PREPARATION
#############################
cd ${MDANSE_SOURCE_DIR}

#############################
# UNITARY TESTS
#############################
echo -e "${BLUE}""Performing unitary tests""${NORMAL}"
cd Tests/UnitTests
${PYTHONEXE} AllTests.py
status=$?
if [ $status -ne 0 ]; then
	echo -e "${RED}" "One or several unit tests failed"
	${MDANSE_SOURCE_DIR}/BuildServer/Unix/clean.sh
	exit $status
fi
cd ${MDANSE_SOURCE_DIR}

#############################
# DEPENDENCIES TESTS
#############################
echo -e "${BLUE}""Performing dependencies tests""${NORMAL}"
cd Tests/DependenciesTests
${PYTHONEXE} AllTests.py
status=$?
if [ $status -ne 0 ]; then
	echo -e "${RED}" "One or several dependencies tests failed"
	${MDANSE_SOURCE_DIR}/BuildServer/Unix/clean.sh
	exit $status
fi
cd ${MDANSE_SOURCE_DIR}

#############################
# FUCNTIONAL TESTS
#############################
echo -e "${BLUE}""Performing functional tests""${NORMAL}"
cd Tests/FunctionalTests/Jobs
rm -rf Test_*
${PYTHONEXE} BuildJobTests.py
${PYTHONEXE} AllTests.py
status=$?
if [ $status -ne 0 ]; then
	echo -e "${RED}" "One or several functional tests failed"
	${MDANSE_SOURCE_DIR}/BuildServer/Unix/clean.sh
	exit $status
fi
cd ${MDANSE_SOURCE_DIR}