#!/bin/bash

ROUGE="\\033[1;31m"

# Performs the unit tests
cd Tests/UnitTests
/Library/Frameworks/Python.framework/Versions/2.7/bin/nosetests --verbosity=3 -P .
# Exit now if unable to run tests
if [ $? -ne 0 ]; then
	status = $?
	echo -e "$ROUGE""One or several unit tests failed"
	exit status
fi
cd ../..

cd Tests/FunctionalTests/Jobs
/Library/Frameworks/Python.framework/Versions/2.7/bin/python BuildJobTests.py
/Library/Frameworks/Python.framework/Versions/2.7/bin/nosetests --verbosity=3 --exe -P .
if [ $? -ne 0 ]; then
	status=$?
	echo -e "$ROUGE""One or several functional tests failed"
	exit status
fi
cd ../../..
