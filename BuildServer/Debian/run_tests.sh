#!/bin/bash

cd $CI_PROJECT_DIR

export PYTHONPATH=${CI_PROJECT_DIR}/build/lib.linux-x86_64-2.7

# Performs the unit tests
cd Tests/UnitTests
nosetests --verbosity=3 -P .
cd ../..

# Performs the functional tests
cd Tests/FunctionalTests/Jobs
python BuildJobTests.py
nosetests --verbosity=3 --exe -P .

