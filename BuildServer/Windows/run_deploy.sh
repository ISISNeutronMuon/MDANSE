#!/bin/bash

# RUN FROM c:\cygwin64\bin\bash c:\Users\Administrateur\Desktop\BUILD\package.sh

#############################
# CONFIGURATION
#############################

if [ ! $1 ]; then
    BUILD_TARGET="win-amd64"
else
    BUILD_TARGET=$1
fi

VERSION_NAME=`sed -n 's/__version__.*=.*\"\(.*\)\"/\1/p' MDANSE/__pkginfo__.py`

if [[ ${CI_BUILD_REF_NAME} =~ develop ]]
then
    if [ -n "${WEEKLY_BUILD}" ]
    then
        VERSION_NAME=${VERSION_NAME}-"weekly-"`date +%Y-%m-%d`
    fi
    VERSION_NAME=${VERSION_NAME}-`git rev-parse --short HEAD`
fi



##Which versions of external programs to use
PYTHON_VERSION=2.7.6

CI_PROJECT_DIR_WIN=$(cygpath -a -w ${CI_PROJECT_DIR})

# Change working directory to the directory the script is in
# http://stackoverflow.com/a/246128
SCRIPT_DIR="${CI_PROJECT_DIR}/BuildServer/Windows"

# This is the directory that will contain the temporary installation
TARGET_DIR="${CI_PROJECT_DIR_WIN}\\BuildServer\\Windows\\Build"
TARGET_DIR_CYGWIN=$(cygpath -u $TARGET_DIR)

cd ${SCRIPT_DIR}

echo "Packaging"

# create the MDANSE installer
echo "Creating nsis installer for target ${BUILD_TARGET}..."

makensis /V4 /ONSISlog.txt /DVERSION=${VERSION_NAME} /DARCH=${BUILD_TARGET} /DTARGET_DIR="${TARGET_DIR}" MDANSE_installer.nsi

