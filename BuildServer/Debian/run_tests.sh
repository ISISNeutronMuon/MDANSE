#!/bin/bash

ROUGE="\\033[1;31m"

cd $CI_PROJECT_DIR

export PYTHONPATH=${CI_PROJECT_DIR}/build/lib.linux-x86_64-2.7

# Performs the unit tests
cd Tests/UnitTests
nosetests --verbosity=3 -P .
# Exit now if unable to run tests
if [ $? -ne 0 ]; then
	status = $?
	echo -e "$ROUGE""One or several unit tests failed"
	exit $status
fi
cd ../..

# Performs the functional tests
cd Tests/FunctionalTests/Jobs
rm -rf Test_*
python BuildJobTests.py
nosetests --verbosity=3 --exe Test_*.py
if [ $? -ne 0 ]; then
	status=$?
	echo -e "$ROUGE""One or several functional tests failed"
	exit $status
fi

