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

# take the latest version of nmoldyn available on the forge
echo -e "$BLEU""Getting last MDANSE revision" "$NORMAL"

# Update the __pkginfo__ file with the current commit. The sed -i "" is compulsory other crashes on macos
COMMIT_ID=$(git rev-parse --long HEAD)
sed -i "" "s/.*__commit__.*/__commit__ = \"${COMMIT_ID}\"/" MDANSE/__pkginfo__.py

# Get revision number from git (without trailing newline)
echo -e "$BLEU""Commit id = ${COMMIT_ID}" "$NORMAL"

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
