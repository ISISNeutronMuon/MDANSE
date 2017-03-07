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
COMMIT_ID=$(git rev-parse --long HEAD)
echo -e "$BLEU""Commit id = ${COMMIT_ID}<--" "$NORMAL"

# Now build last version
echo "$BLEU""Building MDANSE" "$NORMAL"
python setup.py build

