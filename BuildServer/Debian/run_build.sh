#!/bin/bash

export ARCH=$1
export DISTRO=$2

#############################
# CONFIGURATION
#############################

echo "BUID REF NAME --> ${CI_BUILD_REF_NAME}""

## Add some colors
ROUGE="\\033[1;31m"
BLEU="\\033[1;34m"

##Select the build target
BUILD_TARGET=debian

cd
cd $CI_PROJECT_DIR

VERSION_NAME=`python -c "execfile('MDANSE/__pkginfo__.py') ; print __version__`

# Get revision number from git (without trailing newline)
REV_NUMBER=$(git rev-list --count HEAD)
echo -e "$BLEU""Revision number = ${REV_NUMBER}<--" "$NORMAL"

# Now build last version
echo "$BLEU""Building MDANSE" "$NORMAL"
python setup.py build

