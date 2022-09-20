#!/bin/bash

#############################
# CONFIGURATION
#############################
# Debug option for py2app, if needed
export DISTUTILS_DEBUG=0
export PYTHONEXE=$RUNNER_TOOL_CACHE/Python/$PYTHON_VER/x64
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
cp -r $PYTHONEXE/bin/* ${DEBIAN_BIN_DIR}/

# Replace the shebang in mdanse scripts to point to the correct python location, and also edit them
# so that if LD_LIBRARY_PATH is not set up by bash, it the script sets it up for itself.
cd ${DEBIAN_BIN_DIR}/ || exit
files=(mdanse*)
for f in ${files[*]}
do
  sudo sed -i '1s%.*%#!/usr/local/bin/python%' $f

  sudo sed -i '20s|from|try: from|' $f
  sudo sed -i '21i \ \ \ \ except ImportError:' $f
  sudo sed -i '22i \ \ \ \ \ \ \ \ import os, subprocess' $f
  sudo sed -i "23i \ \ \ \ \ \ \ \ os.environ['LD_LIBRARY_PATH'] = f'/usr/local/lib:/usr/local/lib/python3.$PYTHON_MINOR_VER/site-packages/wx:{os.environ.get(\\'LD_LIBRARY_PATH\\', \\'/usr/local\\')}'" $f
  sudo sed -i '24i \ \ \ \ \ \ \ \ subprocess.check_call(str(os.path.abspath(__file__)), env=os.environ, shell=True)' $f

  sudo sed -i "s|python3.9|python3.$PYTHON_MINOR_VER|" $f
done

cd $GITHUB_WORKSPACE || exit

# Build API
# sudo $PYTHONEXE/bin/python setup.py build build_api build_help install
sudo $PYTHONEXE/bin/python setup.py build install

status=$?
if [ $status -ne 0 ]; then
	echo -e "${RED}" "Failed to build MDANSE Documentation""${NORMAL}"
	exit $status
fi

# Copy python packages
cp -r $PYTHONEXE/lib $DEBIAN_ROOT_DIR/usr/local
cp -r $PYTHONEXE/include $DEBIAN_ROOT_DIR/usr/local

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
