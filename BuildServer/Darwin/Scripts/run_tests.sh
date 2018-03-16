#!/bin/bash

ROUGE="\\033[1;31m"

cd $CI_PROJECT_DIR

export PYTHONPATH=${CI_PROJECT_DIR}/build/lib.macosx-10.6-intel-2.7

# Performs the unit tests
cd Tests/UnitTests
/Library/Frameworks/Python.framework/Versions/2.7/bin/nosetests --verbosity=3 -P .
# Exit now if unable to run tests
status=$?
if [ $status -ne 0 ]; then
	echo -e "$ROUGE""One or several unit tests failed"
	exit $status
fi
cd ../..

# Performs the functional tests
cd Tests/FunctionalTests/Jobs
rm -rf Test_*
/Library/Frameworks/Python.framework/Versions/2.7/bin/python BuildJobTests.py
/Library/Frameworks/Python.framework/Versions/2.7/bin/nosetests --verbosity=3 --exe Test_*.py

status=$?
if [ $status -ne 0 ]; then
	echo -e "$ROUGE""One or several functional tests failed"
	exit $status
fi

exit 0