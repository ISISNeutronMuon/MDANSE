#!/bin/bash

# This script is to package the MDANSE package for Mac OS X

#############################
# CONFIGURATION
#############################

## Add some colors
ROUGE="\\033[1;31m"
BLEU="\\033[1;34m"

##Select the build target
BUILD_TARGET=darwin

cd ../../../

# take the latest version of nmoldyn available on the forge
echo -e "$BLEU""Getting last MDANSE revision" "$NORMAL"

# Get revision number from git (without trailing newline)
REV_NUMBER=$(git rev-list --count HEAD)
echo -e "$BLEU""Revision number = ${REV_NUMBER}" "$NORMAL"

# Now build last version and install it in our homebrewed python
echo -e "$BLEU""Building MDANSE" "$NORMAL"

# Clean up temporary build directories
rm -rf build
rm -rf dist

# Remove previous install of MDANSE
rm /usr/local/bin/mdanse*
rm /usr/local/lib/python2.7/site-packages/MDANSE*.egg-info
rm -rf /usr/local/lib/python2.7/site-packages/MDANSE

# Build and install MDANSE to the homebrewed python
/usr/local/bin/python setup.py build >> BuildServer/Darwin/Scripts/build_log.txt 2>&1
/usr/local/bin/python setup.py install >> BuildServer/Darwin/Scripts/build_log.txt 2>&1
