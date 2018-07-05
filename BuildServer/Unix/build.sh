#!/bin/bash

cd ${CI_TEMP_DIR}

#############################
# BUILDING DEPENDENCIES
#############################
# Build ILL version of ScientificPython
echo -e "${BLUE}""Building ScientificPython""${NORMAL}"
rm -rf scientific-python
git clone https://code.ill.fr/scientific-software/scientific-python.git
cd scientific-python
git checkout master

${PYTHONEXE} setup.py build --build-base=${CI_TEMP_BUILD_DIR} install --prefix=${CI_TEMP_INSTALL_DIR}
status=$?
if [ $status -ne 0 ]; then
	echo -e "${RED}" "Failed to build/install Scientific""${NORMAL}"
	exit $status
fi

cp ${CI_TEMP_INSTALL_DIR}/include/python2.7/Scientific/netcdf.h ${CI_TEMP_INSTALL_DIR}/include/python2.7/

cd ${CI_TEMP_DIR}

# Build ILL version of MMTK
echo -e "${BLUE}""Building MMTK""${NORMAL}"
rm -rf mmtk
git clone https://code.ill.fr/scientific-software/mmtk.git
cd mmtk
git checkout master

# Env var needed by MMTK
export NETCDF_HEADER_FILE_PATH=${CI_TEMP_INSTALL_DIR}/include/python2.7/

${PYTHONEXE} setup.py build --build-base=${CI_TEMP_BUILD_DIR} install --prefix=${CI_TEMP_INSTALL_DIR}
status=$?
if [ $status -ne 0 ]; then
	echo -e "${RED}" "Failed to build/install MMTK""${NORMAL}"
	exit $status
fi

#############################
# MDANSE Building
#############################
echo -e "${BLUE}""Building MDANSE""${NORMAL}"

cd ${CI_PROJECT_DIR}

# Now build last version and install it
${PYTHONEXE} setup.py build --build-base=${CI_TEMP_BUILD_DIR} install --prefix=${CI_TEMP_INSTALL_DIR}

status=$?
if [ $status -ne 0 ]; then
	echo -e "${RED}" "Failed to build/install MDANSE""${NORMAL}"
	exit $status
fi

PKG_INFO=${CI_TEMP_INSTALL_DIR}/lib/python2.7/site-packages/MDANSE/__pkginfo__.py

# Update the __pkginfo__ file with the current commit
$SED_I_COMMAND "s/.*__commit__.*/__commit__ = \"${CI_COMMIT_ID}\"/" ${PKG_INFO}

# Get MDANSE version
MDANSE_VERSION=`sed -n 's/__version__.*=.*\"\(.*\)\"/\1/p' ${PKG_INFO}`

# Check if branch is master
if [[ ${CI_COMMIT_REF_NAME} == "master" ]]
then
    VERSION_NAME=${MDANSE_VERSION}
    ${SED_I_COMMAND} "s/.*__beta__.*/__beta__ = None/" ${PKG_INFO}
else
    # Check if branch is release*
	if [[ ${CI_COMMIT_REF_NAME::7} == "release" ]]
	then
	    VERSION_NAME=${MDANSE_VERSION}-rc-${CI_COMMIT_ID}
	    ${SED_I_COMMAND} "s/.*__beta__.*/__beta__ = \"rc\"/" ${PKG_INFO}
	else
	    VERSION_NAME=${MDANSE_VERSION}-beta-${CI_COMMIT_ID}
	    ${SED_I_COMMAND} "s/.*__beta__.*/__beta__ = \"beta\"/" ${PKG_INFO}
	fi
fi
export VERSION_NAME
