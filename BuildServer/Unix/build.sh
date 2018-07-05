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

cp ${CI_TEMP_DIR}/include/python2.7/Scientific/netcdf.h ${CI_TEMP_DIR}/include/python2.7/

cd ${CI_TEMP_DIR}

# Build ILL version of MMTK
echo -e "${BLUE}""Building MMTK""${NORMAL}"
rm -rf mmtk
git clone https://code.ill.fr/scientific-software/mmtk.git
cd mmtk
git checkout master

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

