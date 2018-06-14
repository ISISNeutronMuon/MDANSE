#!/bin/bash

cd $MDANSE_SOURCE_DIR

# Update the __pkginfo__ file with the current commit
echo -e "${BLUE}""Commit id = ${MDANSE_GIT_CURRENT_COMMIT}<--""${NORMAL}"
echo -e "${BLUE}""Branch name = ${MDANSE_GIT_BRANCH_NAME}<--""${NORMAL}"
$SED_I_COMMAND "s/.*__commit__.*/__commit__ = \"${MDANSE_GIT_CURRENT_COMMIT}\"/" MDANSE/__pkginfo__.py

# Get MDANSE version
MDANSE_VERSION=`sed -n 's/__version__.*=.*\"\(.*\)\"/\1/p' MDANSE/__pkginfo__.py`

# Check if branch is master
if [[ ${MDANSE_GIT_BRANCH_NAME} == "master" ]]
then
    VERSION_NAME=${MDANSE_VERSION}
    $SED_I_COMMAND "s/.*__beta__.*/__beta__ = None/" MDANSE/__pkginfo__.py
else
    # Check if branch is release*
	if [[ ${MDANSE_GIT_BRANCH_NAME::7} == "release" ]]
	then
	    VERSION_NAME=${MDANSE_VERSION}-rc-${MDANSE_GIT_CURRENT_COMMIT}
	    $SED_I_COMMAND "s/.*__beta__.*/__beta__ = \"rc\"/" MDANSE/__pkginfo__.py
	else
	    VERSION_NAME=${MDANSE_VERSION}-beta-${MDANSE_GIT_CURRENT_COMMIT}
	    $SED_I_COMMAND "s/.*__beta__.*/__beta__ = \"beta\"/" MDANSE/__pkginfo__.py
	fi
fi
export VERSION_NAME