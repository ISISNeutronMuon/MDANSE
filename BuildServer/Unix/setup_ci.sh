#!/bin/bash

if [ -z $GITHUB_WORKSPACE ]; then
    export GITHUB_WORKSPACE="$( cd "$( dirname "${BASH_SOURCE[0]}" )/../.." && pwd )"
fi

export CI_TEMP_DIR=$GITHUB_WORKSPACE/temp

export CI_TEMP_BUILD_DIR=$GITHUB_WORKSPACE/temp/build
export CI_TEMP_BUILD_DIR=$GITHUB_WORKSPACE/build

export CI_TEMP_INSTALL_DIR=$GITHUB_WORKSPACE/temp/install

export PYTHONPATH=${CI_TEMP_INSTALL_DIR}/lib/python2.7/site-packages/:${PYTHONPATH}

export NETCDF_HEADER_FILE_PATH=/usr/include/

mkdir -p ${CI_TEMP_DIR}

cd $GITHUB_WORKSPACE

## Get revision number from Git
CI_COMMIT_ID=${GITHUB_SHA::8}
#if [ -z ${CI_COMMIT_SHA} ]; then
#    export CI_COMMIT_ID=$(git rev-parse HEAD)
#else
#    export CI_COMMIT_ID=${CI_COMMIT_SHA}
#fi
#export CI_COMMIT_ID=${CI_COMMIT_ID:0:8}
#
## Get commit branch from Gitlab
#if [ -z ${CI_COMMIT_REF_NAME} ]; then
#    CI_COMMIT_REF_NAME=$(git show -s --pretty=%d HEAD)
#    CI_COMMIT_REF_NAME=$(echo ${CI_COMMIT_REF_NAME} | rev | cut -d, -f1 | cut -c2- | cut -d/ -f1 | rev)
#    export CI_COMMIT_REF_NAME
#fi
#

echo -e "${BLUE}""Commit id = ${CI_COMMIT_ID}""${NORMAL}"
echo -e "${BLUE}""Branch name = $GITHUB_REF""${NORMAL}"

PKG_INFO=$GITHUB_WORKSPACE/Src/__pkginfo__.py

# Update the __pkginfo__ file with the current commit
"${SED_I_COMMAND[@]}" "s/.*__commit__.*/__commit__ = \"${CI_COMMIT_ID}\"/" ${PKG_INFO}

# Get MDANSE version
MDANSE_VERSION=`sed -n 's/__version__.*=.*\"\(.*\)\"/\1/p' ${PKG_INFO}`

# Check if branch is master
if [[ $GITHUB_REF == "master" ]]
then
    VERSION_NAME=${MDANSE_VERSION}
    "${SED_I_COMMAND[@]}" "s/.*__beta__.*/__beta__ = None/" ${PKG_INFO}
else
    # Check if branch is release*
	if [[ ${$GITHUB_REF::7} == "release" ]]
	then
	    VERSION_NAME=${MDANSE_VERSION}-rc-${CI_COMMIT_ID}
	    "${SED_I_COMMAND[@]}" "s/.*__beta__.*/__beta__ = \"rc\"/" ${PKG_INFO}
	else
	    VERSION_NAME=${MDANSE_VERSION}-beta-${CI_COMMIT_ID}
	    "${SED_I_COMMAND[@]}" "s/.*__beta__.*/__beta__ = \"beta\"/" ${PKG_INFO}
	fi
fi
export VERSION_NAME
