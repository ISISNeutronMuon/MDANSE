#!/bin/bash

#############################
# CONFIGURATION
#############################
# Debug option for py2app, if needed
export DISTUTILS_DEBUG=0
export MDANSE_DEPENDENCIES_DIR=$HOME/Contents

#############################
# PREPARATION
#############################
cd $GITHUB_WORKSPACE

export MDANSE_APP_DIR=${CI_TEMP_DIR}/dist/MDANSE.app

export PYTHONPATH=$HOME/Contents/Resources/lib/python2.7/site-packages:${PYTHONPATH}

export PYTHONEXE=$HOME/Contents/Resources/bin/python

# Build API
sudo $PYTHONEXE setup.py build build_api build_help install

status=$?
if [ $status -ne 0 ]; then
	echo -e "${RED}" "Failed to build MDANSE Documentation""${NORMAL}"
	exit $status
fi

#############################
# PACKAGING
#############################
echo -e "${BLUE}""Packaging MDANSE""${NORMAL}"

# Copy the bundle
echo $CI_TEMP_DIR
mkdir -p $CI_TEMP_DIR/dist/MDANSE.app
cp -R ${MDANSE_DEPENDENCIES_DIR} ${MDANSE_APP_DIR}
mkdir -p $MDANSE_APP_DIR/Contents/Framework
cp $MDANSE_APP_DIR/Contents/Resources/lib/lib* $MDANSE_APP_DIR/Contents/Framework
cp $HOME/Contents/Resources/lib/python2.7/site-packages/wx/libwx* ${MDANSE_APP_DIR}/Contents/Frameworks

# Add MDANSE version file (should read the version from the bundle with pyobjc, but will figure that out later)
echo "${VERSION_NAME}" > ${MDANSE_APP_DIR}/Contents/Resources/version

# Copy MDANSE GUI
cp $GITHUB_WORKSPACE/Scripts/mdanse_gui ${MDANSE_APP_DIR}/Contents/Resources/

# Modify Info.plist and copy it
sed -i "" "s/<MDANSE_VERSION>/${VERSION_NAME}/" $GITHUB_WORKSPACE/BuildServer/Unix/MacOS/Resources/Info.plist
cp $GITHUB_WORKSPACE/BuildServer/Unix/MacOS/Resources/Info.plist ${MDANSE_APP_DIR}/Contents/

# Copy over other files
cp $GITHUB_WORKSPACE/BuildServer/Unix/MacOS/Resources/mdanse_gui ${MDANSE_APP_DIR}/Contents/
mkdir -p ${MDANSE_APP_DIR}/Contents/MacOS
cp $GITHUB_WORKSPACE/BuildServer/Unix/MacOS/Resources/MDANSE ${MDANSE_APP_DIR}/Contents/MacOS/
cp $GITHUB_WORKSPACE/BuildServer/Unix/MacOS/Resources/python ${MDANSE_APP_DIR}/Contents/MacOS/

echo "Starting installation"
# Relink netcdf
install_name_tool -change /usr/local/opt/netcdf/lib/libnetcdf.18.dylib @executable_path/../Frameworks/libnetcdf.18.dylib ${MDANSE_APP_DIR}/Contents/Resources/lib/python2.7/site-packages/Scientific/_netcdf.so
echo "start dmg creation"
#############################
# Create DMG
#############################
MDANSE_DMG=MDANSE-${VERSION_NAME}-${DISTRO}-${ARCH}.dmg
hdiutil unmount /Volumes/MDANSE -force -quiet
echo "Finish unmounting"
sleep 5
echo "Execute create-dmg"
"$GITHUB_WORKSPACE/BuildServer/Unix/MacOS/create-dmg" --background "$GITHUB_WORKSPACE/BuildServer/Unix/MacOS/Resources/dmg/dmg_background.jpg" --volname "MDANSE" --window-pos 200 120 --window-size 800 400 --icon MDANSE.app 200 190 --hide-extension MDANSE.app --app-drop-link 600 185 "${MDANSE_DMG}" ${CI_TEMP_DIR}/dist
