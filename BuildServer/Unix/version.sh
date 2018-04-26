#!/bin/bash

cd $MDANSE_SOURCE_DIR

# Get revision number from GIT and update the __pkginfo__ file with the current commit
MDANSE_GIT_CURRENT_COMMIT=$(git rev-parse --short HEAD)
echo -e "${BLUE}""Commit id = ${MDANSE_GIT_CURRENT_COMMIT}<--""${NORMAL}"
$SED_I_COMMAND "s/.*__commit__.*/__commit__ = \"${MDANSE_GIT_CURRENT_COMMIT}\"/" MDANSE/__pkginfo__.py

# Get MDANSE version
MDANSE_VERSION=`sed -n 's/__version__.*=.*\"\(.*\)\"/\1/p' MDANSE/__pkginfo__.py`

# Check if branch is master, tag as draft otherwise
if [[ ${CI_COMMIT_REF_NAME} == "master" ]]
then
    VERSION_NAME=${MDANSE_VERSION}
    $SED_I_COMMAND "s/.*__commit__.*/__commit__ = \"${MDANSE_GIT_CURRENT_COMMIT}\"/" MDANSE/__pkginfo__.py
    $SED_I_COMMAND "s/.*__beta__.*/__beta__ = False/" MDANSE/__pkginfo__.py
else
    VERSION_NAME=${MDANSE_VERSION}-"beta"-${MDANSE_GIT_CURRENT_COMMIT}
    $SED_I_COMMAND "s/.*__beta__.*/__beta__ = True/" MDANSE/__pkginfo__.py
fi
export VERSION_NAME