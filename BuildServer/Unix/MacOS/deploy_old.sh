#!/bin/bash

#############################
# CONFIGURATION
#############################
# Debug option for py2app, if needed
export DISTUTILS_DEBUG=0
export PYTHONEXE=$HOME/Contents/Resources/bin/python
#############################
# PREPARATION
#############################
cd ${GITHUB_WORKSPACE}

export MDANSE_APP_DIR=${CI_TEMP_DIR}/dist/MDANSE.app

export PYTHONPATH=${CI_TEMP_INSTALL_DIR}/lib/python2.7/site-packages:${PYTHONPATH}

# Build API
sudo ${PYTHONEXE} setup.py build build_api build_help install

status=$?
if [ $status -ne 0 ]; then
	echo -e "${RED}" "Failed to build MDANSE Documentation""${NORMAL}"
	exit $status
fi

# Create directories
mkdir -p ${MDANSE_APP_DIR}/Contents/Resources/bin
mkdir -p ${MDANSE_APP_DIR}/Contents/MacOS
mkdir -p ${MDANSE_APP_DIR}/Contents/Frameworks
#############################
# PACKAGING
#############################
echo -e "${BLUE}""Packaging MDANSE""${NORMAL}"
MDANSE_DMG=MDANSE-${VERSION_NAME}-${DISTRO}-${ARCH}.dmg

# Replace buggy py2app files
echo "Replacing buggy python2 files"
sudo cp -fv "$GITHUB_WORKSPACE/BuildServer/Unix/MacOS/py2app/qt5.py" "$HOME/Contents/Resources/lib/python2.7/site-packages/py2app/recipes"
sudo cp -fv "$GITHUB_WORKSPACE/BuildServer/Unix/MacOS/py2app/qt6.py" "$HOME/Contents/Resources/lib/python2.7/site-packages/py2app/recipes"

echo "Moving dirs"
cd "${GITHUB_WORKSPACE}/BuildServer/Unix/MacOS"
echo "Building mdanse app"
sudo ${PYTHONEXE} build.py py2app --argv-inject "$GITHUB_WORKSPACE" --argv-inject "$VERSION_NAME" --argv-inject "$CI_TEMP_BUILD_DIR" --argv-inject "$CI_TEMP_DIR"
status=$?
if [ $status -ne 0 ]; then
	echo -e "${RED}" "Cannot build app.""${NORMAL}"
	exit $status
fi
ls ${MDANSE_APP_DIR}/*
# Add MDANSE version file (should read the version from the bundle with pyobjc, but will figure that out later)
echo "Add mdanse version file"
echo "${VERSION_NAME}" | sudo tee "${MDANSE_APP_DIR}/Contents/Resources/version"

#############################
# Copying Python
#############################
### When launching the bundle, the executable target (i.e. MDANSE) modify the python that is shipped with the bundle (si.e. package path, dylib dependencies ...)
### see http://joaoventura.net/blog/2016/embeddable-python-osx/ for technical details
### In our case we also want the user to be able to start directly python without launching the bundle executable (e.g. to run scripts in command line) which is the reason
### why we have to modify the python executable appropriately with the following commands
echo -e "${BLUE}""Copying python""${NORMAL}"
mkdir -p ${MDANSE_APP_DIR}/Contents/Resources/bin
sudo cp /System/Library/Frameworks/Python.framework/Versions/2.7/Resources/Python.app/Contents/MacOS/Python ${MDANSE_APP_DIR}/Contents/Resources/bin/python

echo "Copy lib"
sudo cp -r $HOME/Contents/Resources/lib ${MDANSE_APP_DIR}/Contents/Resources

echo "Copy Python as dylib"
sudo cp /System/Library/Frameworks/Python.framework/Versions/2.7/Python ${MDANSE_APP_DIR}/Contents/Resources/lib/libpython2.7.dylib
chmod 777 ${MDANSE_APP_DIR}/Contents/Resources/lib/libpython2.7.dylib

install_name_tool -change /System/Library/Frameworks/Python.framework/Versions/2.7/Python @executable_path/../Resources/lib/libpython2.7.dylib ${MDANSE_APP_DIR}/Contents/Resources/bin/python
install_name_tool -id @loader_path/libpython2.7.dylib ${MDANSE_APP_DIR}/Contents/Resources/lib/libpython2.7.dylib

ln -s ../Resources/bin/python ${MDANSE_APP_DIR}/Contents/MacOS/python

sudo cp ${GITHUB_WORKSPACE}/BuildServer/Unix/MacOS/site.py ${MDANSE_APP_DIR}/Contents/Resources/.
sudo cp ${GITHUB_WORKSPACE}/BuildServer/Unix/MacOS/site.py ${MDANSE_APP_DIR}/Contents/Resources/lib/python2.7/.

chmod 777 ${GITHUB_WORKSPACE}/BuildServer/Unix/MacOS/change_dylib_path.sh

echo -e "${BLUE}""Changing dyilib paths""${NORMAL}"
sudo cp $HOME/Contents/Resources/lib/lib* ${MDANSE_APP_DIR}/Contents/Frameworks
sudo cp $HOME/Contents/Resources/lib/python2.7/site-packages/wx/libwx* ${MDANSE_APP_DIR}/Contents/Frameworks
"${GITHUB_WORKSPACE}/BuildServer/Unix/MacOS/change_dylib_path.sh"

# Comment the 'add_system_python_extras' call that add some System path to the sys.path

"${SED_I_COMMAND[@]}" "s/^add_system_python_extras()$/#add_system_python_extras()/" ${MDANSE_APP_DIR}/Contents/Resources/__boot__.py

#############################
# Cleanup
#############################
# Removing matplotlib/tests ==> 45.2 Mb
rm -rf ${MDANSE_APP_DIR}/Contents/Resources/lib/python2.7/matplotlib/tests
# Sample data for matplotlib is useless
rm -rf ${MDANSE_APP_DIR}/Contents/Resources/lib/python2.7/matplotlib/mpl-data/sample_data
rm -rf ${MDANSE_APP_DIR}/Contents/Resources/mpl-data/sample_data
# Scipy package is useless
rm -rf ${MDANSE_APP_DIR}/Contents/Resources/lib/python2.7/scipy
# ZMQ package is useless
rm -rf ${MDANSE_APP_DIR}/Contents/Resources/lib/python2.7/zmq

#############################
# Create DMG
#############################
hdiutil unmount /Volumes/MDANSE -force -quiet
sleep 5

"${GITHUB_WORKSPACE}/BuildServer/Unix/MacOS/Resources/dmg/create-dmg" --background "${GITHUB_WORKSPACE}/BuildServer/Unix/MacOS/Resources/dmg/dmg_background.jpg" --volname "MDANSE" --window-pos 200 120 --window-size 800 400 --icon MDANSE.app 200 190 --hide-extension MDANSE.app --app-drop-link 600 185 "${MDANSE_DMG}" ${CI_TEMP_DIR}/dist
mv ${GITHUB_WORKSPACE}/BuildServer/Unix/MacOS/${MDANSE_DMG} ${GITHUB_WORKSPACE}
