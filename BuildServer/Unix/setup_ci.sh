#!/bin/bash

if [ -z ${CI_PROJECT_DIR} ]; then
    export CI_PROJECT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )/../.." && pwd )"
fi

export CI_TEMP_DIR=${CI_PROJECT_DIR}/temp

export CI_TEMP_BUILD_DIR=${CI_PROJECT_DIR}/temp/build

export CI_TEMP_INSTALL_DIR=${CI_PROJECT_DIR}/temp/install

export PYTHONPATH=${CI_TEMP_INSTALL_DIR}/lib/python2.7/site-packages:${PYTHONPATH}

mkdir -p ${CI_TEMP_DIR}

cd ${CI_PROJECT_DIR}

# Get revision number from Git
if [ -z ${CI_COMMIT_SHA} ]; then
    export CI_COMMIT_ID=$(git rev-parse HEAD)
fi
export CI_COMMIT_ID=${CI_COMMIT_ID:0:8}

# Get commit branch from Gitlab
if [ -z ${CI_COMMIT_REF_NAME} ]; then
    CI_COMMIT_REF_NAME=$(git show -s --pretty=%d HEAD)
    CI_COMMIT_REF_NAME=$(echo ${CI_COMMIT_REF_NAME} | rev | cut -d, -f1 | cut -c2- | cut -d/ -f1 | rev)
    export CI_COMMIT_REF_NAME
fi

export RED="\\033[1;31m"
export BLUE="\\033[1;34m"
export NORMAL="\\033[0m"

echo -e "${BLUE}""Commit id = ${CI_COMMIT_ID}""${NORMAL}"
echo -e "${BLUE}""Branch name = ${CI_COMMIT_REF_NAME}""${NORMAL}"

