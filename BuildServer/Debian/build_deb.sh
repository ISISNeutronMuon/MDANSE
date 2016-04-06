#!/bin/sh

export ARCH=$1
export DISTRO=$2

#############################
# CONFIGURATION
#############################

## Add some colors
VERT="\\033[1;32m"
NORMAL="\\033[0;39m"
ROUGE="\\033[1;31m"
ROSE="\\033[1;35m"
BLEU="\\033[1;34m"
BLANC="\\033[0;02m"
BLANCLAIR="\\033[1;08m"
JAUNE="\\033[1;33m"
CYAN="\\033[1;36m"

##Select the build target
BUILD_TARGET=debian

##Do we need to create the final archive
ARCHIVE_FOR_DISTRIBUTION=1
##Which version name are we appending to the final archive
export BUILD_NAME=1.0.0

export REV_NUMBER="undefined"

cd
cd $CI_PROJECT_DIR

# Get revision number from git (without trailing newline)
REV_NUMBER=$(git rev-list --count HEAD)
echo "$BLEU""Revision number is -->${REV_NUMBER}<--" "$NORMAL"

# Add current revision number to python source code (will appear in "About..." dialog)
# see http://stackoverflow.com/questions/7648328/getting-sed-error
sed -i "s/__revision__ = \"undefined\"/__revision__ = \"${REV_NUMBER}\"/" MDANSE/__pkginfo__.py

# Now build last version
echo "$BLEU""Building MDANSE" "$NORMAL"
python setup.py build 

echo "$BLEU""Build debian tree" "$NORMAL"

DEBIAN_ROOT_DIR=debian_${DISTRO}-${ARCH}

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
cp ./mdanse/build/scripts-2.7/* ${DEBIAN_BIN_DIR}/
dos2unix ${DEBIAN_BIN_DIR}/mdanse_*

# Build the usr/local/lib/python2.7/dist-packages directory inside the debian root directory and copy the MDANSE package inside
DEBIAN_DIST_DIR=${DEBIAN_ROOT_DIR}/usr/local/lib/python2.7/dist-packages
mkdir -p ${DEBIAN_DIST_DIR}
cp -r ./mdanse/build/lib.linux-x86_64-2.7/MDANSE ${DEBIAN_DIST_DIR}
# also copy the localy installed ScientificPython and MMTK
cp -r /usr/local/lib/python2.7/dist-packages/Scientific* ${DEBIAN_DIST_DIR}
cp -r /usr/local/lib/python2.7/dist-packages/MMTK* ${DEBIAN_DIST_DIR}

fakeroot dpkg-deb -b ${DEBIAN_ROOT_DIR} MDANSE-${BUILD_NAME}-${DISTRO}-${ARCH}.deb

#export BUILD_PATH=build-chroot-${DISTRO}-${ARCH}

# Create a basic debian disto
#rm -rf ${BUILD_PATH}
#debootstrap --arch $ARCH $DISTRO ${BUILD_PATH}

#mkdir -p "${BUILD_PATH}/build"
#cp debcreate.sh "${BUILD_PATH}/build"

#ROOT=./${BUILD_PATH}/build/MDANSE-${BUILD_NAME}-${DISTRO}-${ARCH}

#mkdir -p ${ROOT}/usr/local/lib/python2.7/dist-packages/
#mkdir -p ${ROOT}/usr/local/bin
#mkdir -p ${ROOT}/usr/share/pixmaps/
#mkdir -p ${ROOT}/usr/share/applications/

#cp -R DEBIAN ${ROOT}

# copy build things to debian tree
#cp -r ./mdanse/build/lib.linux-x86_64-2.7/MDANSE ${ROOT}/usr/local/lib/python2.7/dist-packages/
# also copy the localy installed MMTK (not package available)
# NOTE : This suppose that MDANSE dependencies are up to date on build machine...
#cp -r /usr/local/lib/python2.7/dist-packages/Scientific* ${ROOT}/usr/local/lib/python2.7/dist-packages/
#cp -r /usr/local/lib/python2.7/dist-packages/MMTK* ${ROOT}/usr/local/lib/python2.7/dist-packages/
# and the MDANSE scripts
#cp ./mdanse/build/scripts-2.7/* ${ROOT}/usr/local/bin
# secure "linux end of line"
#cd ${ROOT}/usr/local/bin
#dos2unix mdanse_*
#cd -
# Icon (in case of change)
#cp ./mdanse/MDANSE/GUI/Icons/mdanse.png ${ROOT}/usr/share/pixmaps/
#cp MDANSE.desktop ${ROOT}/usr/share/applications/.

#echo "$BLEU""Ready to chroot and debcreate" "$NORMAL"
# Then, to create a debian package :
#chroot ./${BUILD_PATH} /bin/bash -c "cd /build ; ./debcreate.sh"

#mv ${BUILD_PATH}/build/MDANSE-${BUILD_NAME}-${DISTRO}-${ARCH}.deb .
