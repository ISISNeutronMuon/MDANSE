#!/bin/bash

#############################
# PREPARATION
#############################
rm -rf build

# Create the temporary directory where ScientificPython, MMTK and MDANSE will be installed
rm -rf ${MDANSE_TEMPORARY_INSTALLATION_DIR}
mkdir ${MDANSE_TEMPORARY_INSTALLATION_DIR}

#############################
# BUILDING DEPENDENCIES
#############################
# Build ILL version of ScientificPython
echo -e "${BLUE}""Building ScientificPython""${NORMAL}"
cd /tmp
rm -rf scientific-python
git clone https://code.ill.fr/scientific-software/scientific-python.git
cd scientific-python
git checkout master
${PYTHONEXE} setup.py build
status=$?
if [ $status -ne 0 ]; then
	echo -e "${RED}" "Failed to build Scientific""${NORMAL}"
	exit $status
fi
${PYTHONEXE} setup.py install --prefix=${MDANSE_TEMPORARY_INSTALLATION_DIR}
status=$?
if [ $status -ne 0 ]; then
	echo -e "${RED}" "Failed to install Scientific""${NORMAL}"
	exit $status
fi
export NETCDF_HEADER_FILE_PATH=${MDANSE_TEMPORARY_INSTALLATION_DIR}/include/python2.7/
cp ${NETCDF_HEADER_FILE_PATH}/Scientific/netcdf.h ${NETCDF_HEADER_FILE_PATH}

# Build ILL version of MMTK
echo -e "${BLUE}""Building MMTK""${NORMAL}"
cd /tmp
rm -rf mmtk
git clone https://code.ill.fr/scientific-software/mmtk.git
cd mmtk
git checkout master
${PYTHONEXE} setup.py build
status=$?
if [ $status -ne 0 ]; then
	echo -e "${RED}" "Failed to build MMTK""${NORMAL}"
	exit $status
fi
${PYTHONEXE} setup.py install --prefix=${MDANSE_TEMPORARY_INSTALLATION_DIR}
status=$?
if [ $status -ne 0 ]; then
	echo -e "${RED}" "Failed to install MMTK""${NORMAL}"
	exit $status
fi

#############################
# MDANSE Building
#############################
echo -e "${BLUE}""Building MDANSE""${NORMAL}"
cd $MDANSE_SOURCE_DIR

# Now build last version and install it
${PYTHONEXE} setup.py build
${PYTHONEXE} setup.py build_api
${PYTHONEXE} setup.py build_help

status=$?
if [ $status -ne 0 ]; then
	echo -e "${RED}" "Failed to build MDANSE""${NORMAL}"
	exit $status
fi
${PYTHONEXE} setup.py install --prefix=${MDANSE_TEMPORARY_INSTALLATION_DIR}
status=$?
if [ $status -ne 0 ]; then
	echo -e "${RED}" "Failed to install MDANSE""${NORMAL}"
	exit $status
fi

rm -rf build
