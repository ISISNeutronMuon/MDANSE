#!/bin/bash

#############################
# CONFIGURATION
#############################
# Debug option for py2app, if needed
export DISTUTILS_DEBUG=0

#############################
# PREPARATION
#############################
# SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
SCRIPT_DIR=$GITHUB_WORKSPACE/BuildServer/Unix/Debian/

DEBIAN_ROOT_DIR=$GITHUB_WORKSPACE/temp

rm -rf ${DEBIAN_ROOT_DIR}
mkdir -p ${DEBIAN_ROOT_DIR}

#############################
# PACKAGING
#############################
echo -e "${BLUE}""Build debian tree""${NORMAL}"

# Copy all the debian files (e.g. control, copyright, md5sum ...) into DEBIAN directory
cp -r ${SCRIPT_DIR}/Resources/DEBIAN ${DEBIAN_ROOT_DIR}/
# Set automatically the good version number for the Debian control file
sed -i "s/Version:.*/Version: ${VERSION_NAME}/g" ${DEBIAN_ROOT_DIR}/DEBIAN/control
chmod -R 755 ${DEBIAN_ROOT_DIR}/DEBIAN

# Build the /usr/share/applications directory inside the debian root directory and copy the mdanse desktop file inside
DEBIAN_APP_DIR=${DEBIAN_ROOT_DIR}/usr/share/applications
mkdir -p ${DEBIAN_APP_DIR}
cp ${SCRIPT_DIR}/Resources/MDANSE.desktop ${DEBIAN_APP_DIR}/

# Build the /usr/share/pixmaps directory inside the debian root directory and copy the mdanse icon file inside
DEBIAN_PIXMAPS_DIR=${DEBIAN_ROOT_DIR}/usr/share/pixmaps
mkdir -p ${DEBIAN_PIXMAPS_DIR}
cp $GITHUB_WORKSPACE/Src/GUI/Icons/mdanse.png ${DEBIAN_PIXMAPS_DIR}/

# Build the /usr/local/bin directory inside the debian root directory and copy the mdanse scripts inside
DEBIAN_BIN_DIR=${DEBIAN_ROOT_DIR}/usr/local/bin
mkdir -p ${DEBIAN_BIN_DIR}
cp $GITHUB_WORKSPACE/Scripts/* ${DEBIAN_BIN_DIR}/
dos2unix ${DEBIAN_BIN_DIR}/mdanse_*

# Build the usr/local/lib/python2.7/dist-packages directory inside the debian root directory and copy the MDANSE package inside
DEBIAN_DIST_DIR=${DEBIAN_ROOT_DIR}/usr/local/lib/python2.7/dist-packages
mkdir -p ${DEBIAN_DIST_DIR}

cd $GITHUB_WORKSPACE

# Build API
export PYTHONEXE=$HOME/Python
$PYTHONEXE setup.py build_api build_help install --prefix=/opt/hostedtoolcache/Python/2.7.18/x64

status=$?
if [ $status -ne 0 ]; then
	echo -e "${RED}" "Failed to build MDANSE Documentation""${NORMAL}"
	exit $status
fi

# Copy the localy installed ScientificPython, MMTK and MDANSE
cp -r /opt/hostedtoolcache/Python/2.7.18/x64/lib/python2.7/site-packages/Scientific ${DEBIAN_DIST_DIR}
cp -r /opt/hostedtoolcache/Python/2.7.18/x64/lib/python2.7/site-packages/MMTK ${DEBIAN_DIST_DIR}
cp -r /opt/hostedtoolcache/Python/2.7.18/x64/lib/python2.7/site-packages/MDANSE ${DEBIAN_DIST_DIR}

# Compute the Installed-Size field for the debian package
instSize=$(du ${DEBIAN_ROOT_DIR} -b -s | cut -f1)
sed -i "s/Installed-Size:.*/Installed-Size: $((1+(instSize/1024)))/g" ${DEBIAN_ROOT_DIR}/DEBIAN/control

export TMPDIR=.
fakeroot dpkg-deb -b ${DEBIAN_ROOT_DIR} $GITHUB_WORKSPACE/MDANSE-${VERSION_NAME}-${DISTRO}-${ARCH}.deb
status=$?
if [ $status -ne 0 ]; then
	echo -e "${RED}" "Cannot build app.""${NORMAL}"
	exit $status
fi
