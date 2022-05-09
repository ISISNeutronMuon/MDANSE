#!/bin/bash

#############################
# PREPARATION
#############################
export PYTHONPATH=${CI_TEMP_INSTALL_DIR}/lib/python2.7/site-packages:${PYTHONPATH}

#############################
# UNITARY TESTS
#############################
echo -e "${BLUE}""Performing unitary tests""${NORMAL}"
cd $GITHUB_WORKSPACE/Tests/UnitTests
python2 AllTests.py
status=$?
if [ $status -ne 0 ]; then
	echo -e "${RED}" "One or several unit tests failed"
	exit $status
fi

#############################
# DEPENDENCIES TESTS
#############################
echo -e "${BLUE}""Performing dependencies tests""${NORMAL}"
cd $GITHUB_WORKSPACE/Tests/DependenciesTests
python2 AllTests.py
status=$?
if [ $status -ne 0 ]; then
	echo -e "${RED}" "One or several dependencies tests failed"
	exit $status
fi

#############################
# FUCNTIONAL TESTS
#############################
echo -e "${BLUE}""Performing functional tests""${NORMAL}"
cd $GITHUB_WORKSPACE/Tests/FunctionalTests/Jobs
rm -rf Test_*
python2 BuildJobTests.py
python2 AllTests.py
status=$?
if [ $status -ne 0 ]; then
	echo -e "${RED}" "One or several functional tests failed"
	exit $status
fi
