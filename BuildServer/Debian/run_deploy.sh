#!/bin/bash

export ARCH=$1
export DISTRO=$2

#############################
# CONFIGURATION
#############################

## Add some colors
ROUGE="\\033[1;31m"
BLEU="\\033[1;34m"

COMMIT_ID=$(git rev-parse --long HEAD)
VERSION_NAME=`sed -n 's/__version__.*=.*\"\(.*\)\"/\1/p' MDANSE/__pkginfo__.py`

if [[ ${CI_BUILD_REF_NAME} =~ develop ]]
then
    if [ -n "${WEEKLY_BUILD}" ]
    then
        VERSION_NAME=${VERSION_NAME}-"weekly-"`date +%Y-%m-%d`
    fi
    VERSION_NAME=${VERSION_NAME}-${COMMIT_ID}
fi

##Select the build target
BUILD_TARGET=debian

cd
cd $CI_PROJECT_DIR

echo "$BLEU""Build debian tree" "$NORMAL"

# Set automatically the good version number for the Debian control file
sed -i "s/Version:.*/Version: ${VERSION_NAME}/g" BuildServer/Debian/DEBIAN/control

DEBIAN_ROOT_DIR=BuildServer/Debian/Build

# Copy all the debian files (e.g. control, copyright, md5sum ...) into DEBIAN directory
mkdir ${DEBIAN_ROOT_DIR}
cp -r BuildServer/Debian/DEBIAN ${DEBIAN_ROOT_DIR}/
chmod -R 755 ${DEBIAN_ROOT_DIR}/DEBIAN

# Build the /usr/share/applications directory inside the debian root directory and copy the mdanse desktop file inside
DEBIAN_APP_DIR=${DEBIAN_ROOT_DIR}/usr/share/applications
mkdir -p ${DEBIAN_APP_DIR}
cp BuildServer/Debian/MDANSE.desktop ${DEBIAN_APP_DIR}/

# Build the /usr/share/pixmaps directory inside the debian root directory and copy the mdanse icon file inside
DEBIAN_PIXMAPS_DIR=${DEBIAN_ROOT_DIR}/usr/share/pixmaps
mkdir -p ${DEBIAN_PIXMAPS_DIR}
cp MDANSE/GUI/Icons/mdanse.png ${DEBIAN_PIXMAPS_DIR}/

# Build the /usr/local/bin directory inside the debian root directory and copy the mdanse scripts inside
DEBIAN_BIN_DIR=${DEBIAN_ROOT_DIR}/usr/local/bin
mkdir -p ${DEBIAN_BIN_DIR}
cp build/scripts-2.7/* ${DEBIAN_BIN_DIR}/
dos2unix ${DEBIAN_BIN_DIR}/mdanse_*

# Build the usr/local/lib/python2.7/dist-packages directory inside the debian root directory and copy the MDANSE package inside
DEBIAN_DIST_DIR=${DEBIAN_ROOT_DIR}/usr/local/lib/python2.7/dist-packages
mkdir -p ${DEBIAN_DIST_DIR}
cp -r build/lib.linux-x86_64-2.7/MDANSE ${DEBIAN_DIST_DIR}
# also copy the localy installed ScientificPython and MMTK
cp -r /usr/local/lib/python2.7/dist-packages/Scientific* ${DEBIAN_DIST_DIR}
cp -r /usr/local/lib/python2.7/dist-packages/MMTK* ${DEBIAN_DIST_DIR}

# Compute the Installed-Size field for the debian package
instSize=$(du ${DEBIAN_ROOT_DIR} -b -s | cut -f1)
sed -i "s/Installed-Size:.*/Installed-Size: $((1+(instSize/1024)))/g" ${DEBIAN_ROOT_DIR}/DEBIAN/control

export TMPDIR=.
fakeroot dpkg-deb -b ${DEBIAN_ROOT_DIR} ${DEBIAN_ROOT_DIR}/MDANSE-${VERSION_NAME}-${DISTRO}-${ARCH}.deb
