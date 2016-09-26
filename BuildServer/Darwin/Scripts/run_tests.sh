#!/bin/bash

cd ../../../

# Performs the unit tests
cd Tests/UnitTests
nosetests --verbosity=3 -P .
cd ../..

cd Tests/FunctionalTests/Jobs
python BuildJobTests.py
nosetests --verbosity=3 --exe -P .
cd ../../..
