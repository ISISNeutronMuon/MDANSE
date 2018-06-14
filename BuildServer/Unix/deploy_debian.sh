#!/bin/bash

#############################
# CONFIGURATION
#############################
# Debug option for py2app, if needed
export DISTUTILS_DEBUG=0

#############################
# PREPARATION
#############################
cd ${MDANSE_SOURCE_DIR}
DEBIAN_ROOT_DIR=${MDANSE_SOURCE_DIR}/BuildServer/Build_Debian
rm -rf ${DEBIAN_ROOT_DIR}
mkdir ${DEBIAN_ROOT_DIR}

#############################
# PACKAGING
#############################
echo -e "${BLUE}""Build debian tree""${NORMAL}"

# Set automatically the good version number for the Debian control file
sed -i "s/Version:.*/Version: ${VERSION_NAME}/g" BuildServer/Unix/Debian_resources/DEBIAN/control

# Copy all the debian files (e.g. control, copyright, md5sum ...) into DEBIAN directory
cp -r BuildServer/Unix/Debian_resources/DEBIAN ${DEBIAN_ROOT_DIR}/
chmod -R 755 ${DEBIAN_ROOT_DIR}/DEBIAN

# Build the /usr/share/applications directory inside the debian root directory and copy the mdanse desktop file inside
DEBIAN_APP_DIR=${DEBIAN_ROOT_DIR}/usr/share/applications
mkdir -p ${DEBIAN_APP_DIR}
cp BuildServer/Unix/Debian_resources/MDANSE.desktop ${DEBIAN_APP_DIR}/

# Build the /usr/share/pixmaps directory inside the debian root directory and copy the mdanse icon file inside
DEBIAN_PIXMAPS_DIR=${DEBIAN_ROOT_DIR}/usr/share/pixmaps
mkdir -p ${DEBIAN_PIXMAPS_DIR}
cp MDANSE/GUI/Icons/mdanse.png ${DEBIAN_PIXMAPS_DIR}/

# Build the /usr/local/bin directory inside the debian root directory and copy the mdanse scripts inside
DEBIAN_BIN_DIR=${DEBIAN_ROOT_DIR}/usr/local/bin
mkdir -p ${DEBIAN_BIN_DIR}
cp Scripts/* ${DEBIAN_BIN_DIR}/
dos2unix ${DEBIAN_BIN_DIR}/mdanse_*

# Build the usr/local/lib/python2.7/dist-packages directory inside the debian root directory and copy the MDANSE package inside
DEBIAN_DIST_DIR=${DEBIAN_ROOT_DIR}/usr/local/lib/python2.7/dist-packages
mkdir -p ${DEBIAN_DIST_DIR}

# Copy the localy installed ScientificPython, MMTK and MDANSE
cp -r ${MDANSE_TEMPORARY_INSTALLATION_DIR}/lib/python2.7/site-packages/Scientific ${DEBIAN_DIST_DIR}
cp -r ${MDANSE_TEMPORARY_INSTALLATION_DIR}/lib/python2.7/site-packages/MMTK ${DEBIAN_DIST_DIR}
cp -r ${MDANSE_TEMPORARY_INSTALLATION_DIR}/lib/python2.7/site-packages/MDANSE ${DEBIAN_DIST_DIR}

# Compute the Installed-Size field for the debian package
instSize=$(du ${DEBIAN_ROOT_DIR} -b -s | cut -f1)
sed -i "s/Installed-Size:.*/Installed-Size: $((1+(instSize/1024)))/g" ${DEBIAN_ROOT_DIR}/DEBIAN/control

export TMPDIR=.
fakeroot dpkg-deb -b ${DEBIAN_ROOT_DIR} ${MDANSE_SOURCE_DIR}/MDANSE-${VERSION_NAME}-${DISTRO}-${ARCH}.deb
status=$?
if [ $status -ne 0 ]; then
	echo -e "${RED}" "Cannot build app.""${NORMAL}"
	exit $status
fi

rm -rf ${MDANSE_TEMPORARY_INSTALLATION_DIR}