#!/bin/bash

#############################
# CONFIGURATION
#############################
# Debug option for py2app, if needed
export DISTUTILS_DEBUG=0
export MDANSE_DEPENDENCIES_DIR=/Users/ci/Projects/mdanse/bundle

#############################
# PREPARATION
#############################
cd ${CI_PROJECT_DIR}

export MDANSE_APP_DIR=${CI_TEMP_DIR}/dist/MDANSE.app

export PYTHONPATH=${CI_TEMP_INSTALL_DIR}/lib/python2.7/site-packages:${PYTHONPATH}

# Build API
${PYTHONEXE} setup.py build_api build_help install --prefix=${CI_TEMP_INSTALL_DIR}

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
mkdir ${CI_TEMP_DIR}/dist
mkdir ${CI_TEMP_DIR}/dist/MDANSE.app
cp -R ${MDANSE_DEPENDENCIES_DIR} ${MDANSE_APP_DIR}/Contents
cp -R ${CI_TEMP_INSTALL_DIR}/lib/python2.7/site-packages/* ${MDANSE_APP_DIR}/Contents/Resources/lib/python2.7/

# Add MDANSE version file (should read the version from the bundle with pyobjc, but will figure that out later)
echo "${VERSION_NAME}" > ${MDANSE_APP_DIR}/Contents/Resources/version

# Copy MDANSE GUI
cp ${CI_PROJECT_DIR}/Scripts/mdanse_gui ${MDANSE_APP_DIR}/Contents/Resources/

# Modify Info.plist and copy it
sed -i "" "s/<MDANSE_VERSION>/${VERSION_NAME}/" ${CI_PROJECT_DIR}/BuildServer/Unix/MacOS/Resources/Info.plist
cp ${CI_PROJECT_DIR}/BuildServer/Unix/MacOS/Resources/Info.plist ${MDANSE_APP_DIR}/Contents/

# Relink netcdf
install_name_tool -change /usr/local/opt/netcdf/lib/libnetcdf.18.dylib @executable_path/../Frameworks/libnetcdf.18.dylib ${MDANSE_APP_DIR}/Contents/Resources/lib/python2.7/Scientific/_netcdf.so

#############################
# Create DMG
#############################
MDANSE_DMG=MDANSE-${VERSION_NAME}-${DISTRO}-${ARCH}.dmg
hdiutil unmount /Volumes/MDANSE -force -quiet
sleep 5
${CI_PROJECT_DIR}/BuildServer/Unix/MacOS/create-dmg --background "${CI_PROJECT_DIR}/BuildServer/Unix/MacOS/Resources/dmg/dmg_background.jpg" --volname "MDANSE" --window-pos 200 120 --window-size 800 400 --icon MDANSE.app 200 190 --hide-extension MDANSE.app --app-drop-link 600 185 "${MDANSE_DMG}" ${CI_TEMP_DIR}/dist
