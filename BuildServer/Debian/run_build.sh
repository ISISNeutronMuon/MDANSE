#!/bin/bash

export ARCH=$1
export DISTRO=$2

#############################
# CONFIGURATION
#############################

## Add some colors
VERT="\\033[1;32m"
NORMAL="\\033[0;39m"
ROUGE="\\033[1;31m"
ROSE="\\033[1;35m"
BLEU="\\033[1;34m"
BLANC="\\033[0;02m"
BLANCLAIR="\\033[1;08m"
JAUNE="\\033[1;33m"
CYAN="\\033[1;36m"

if [ -n "${RUN_NIGHTLY_BUILD}" ]
then
    VERSION_NAME="devel"
else
    if [[ $CI_BUILD_TAG =~ ^v([0-9]+\.[0-9]+\.[0-9]+)$ ]]; then
        VERSION_NAME=${BASH_REMATCH[1]}
    else
        echo -e "$ROUGE""Invalid version number ${CI_BUILD_TAG}" "$NORMAL"
        exit
    fi
fi

##Select the build target
BUILD_TARGET=debian

cd
cd $CI_PROJECT_DIR

# Get revision number from git (without trailing newline)
REV_NUMBER=$(git rev-list --count HEAD)
echo -e "$BLEU""Revision number = ${REV_NUMBER}<--" "$NORMAL"

# Now build last version
echo "$BLEU""Building MDANSE" "$NORMAL"
python setup.py build

