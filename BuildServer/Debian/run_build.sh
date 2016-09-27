#!/bin/bash

export ARCH=$1
export DISTRO=$2

#############################
# CONFIGURATION
#############################

## Add some colors
BLEU="\\033[1;34m"

cd
cd $CI_PROJECT_DIR

# Get revision number from git (without trailing newline)
REV_NUMBER=$(git rev-list --count HEAD)
echo -e "$BLEU""Revision number = ${REV_NUMBER}<--" "$NORMAL"

# Now build last version
echo "$BLEU""Building MDANSE" "$NORMAL"
python setup.py build

