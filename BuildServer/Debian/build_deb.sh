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

cd
cd $CI_PROJECT_DIR

# Get revision number from git (without trailing newline)
# REV_NUMBER=$(git rev-list --count HEAD)
# echo "$BLEU""Revision number is -->${REV_NUMBER}<--" "$NORMAL"

# Add current revision number to python source code (will appear in "About..." dialog)
# see http://stackoverflow.com/questions/7648328/getting-sed-error
# sed -i "s/__revision__ = \"undefined\"/__revision__ = \"${REV_NUMBER}\"/" MDANSE/__pkginfo__.py

MDANSE_VERSION=$(grep -Po '(?<=__version__ = \")\d.\d.\d' MDANSE/__pkginfo__.py)

# Now build last version
echo "$BLEU""Building MDANSE" "$NORMAL"
python setup.py build 

export PYTHONPATH=${PWD}/build/lib.linux-x86_64-2.7

# Performs the unit tests
cd Tests/UnitTests
nosetests --verbosity=3 -P .
cd ../..

cd Tests/FunctionalTests/Jobs
python BuildJobTests.py
nosetests --verbosity=3 --exe -P .
cd ../../..

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
cp build/scripts-2.7/* ${DEBIAN_BIN_DIR}/
dos2unix ${DEBIAN_BIN_DIR}/mdanse_*

# Build the usr/local/lib/python2.7/dist-packages directory inside the debian root directory and copy the MDANSE package inside
DEBIAN_DIST_DIR=${DEBIAN_ROOT_DIR}/usr/local/lib/python2.7/dist-packages
mkdir -p ${DEBIAN_DIST_DIR}
cp -r build/lib.linux-x86_64-2.7/MDANSE ${DEBIAN_DIST_DIR}
# also copy the localy installed ScientificPython and MMTK
cp -r /usr/local/lib/python2.7/dist-packages/Scientific* ${DEBIAN_DIST_DIR}
cp -r /usr/local/lib/python2.7/dist-packages/MMTK* ${DEBIAN_DIST_DIR}

export TMPDIR=.
fakeroot dpkg-deb -b ${DEBIAN_ROOT_DIR} MDANSE-${MDANSE_VERSION}-${DISTRO}-${ARCH}.deb
scp MDANSE-${MDANSE_VERSION}-${DISTRO}-${ARCH}.deb gitlabci-nsxtool@mdanse.ill.fr:/mnt/data/software/mdanse/uploads

curl -T MDANSE-${MDANSE_VERSION}-${DISTRO}-${ARCH}.deb ftp://$CI_FTP_USER_USERNAME:$CI_FTP_USER_PASSWORD@ftp.ill.fr/mdanse/
