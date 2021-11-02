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
sudo mkdir -p ${MDANSE_APP_DIR}/Contents/Resources/bin
sudo cp /System/Library/Frameworks/Python.framework/Versions/2.7/Resources/Python.app/Contents/MacOS/Python ${MDANSE_APP_DIR}/Contents/Resources/bin/python

echo "Copy lib"
sudo cp -r $HOME/Contents/Resources/lib ${MDANSE_APP_DIR}/Contents/Resources

echo "Copy dependency dylibs"
sudo mv -v ${MDANSE_APP_DIR}/Contents/Resources/lib/lib* ${MDANSE_APP_DIR}/Contents/Frameworks
sudo cp -v $HOME/Contents/Resources/lib/python2.7/site-packages/wx/libwx* ${MDANSE_APP_DIR}/Contents/Frameworks

echo "Copy Python as dylib"
sudo cp /System/Library/Frameworks/Python.framework/Versions/2.7/Python ${MDANSE_APP_DIR}/Contents/Resources/lib/libpython2.7.dylib
sudo chmod 777 ${MDANSE_APP_DIR}/Contents/Resources/lib/libpython2.7.dylib
sudo cp /usr/local/lib/libint*.dylib ${MDANSE_APP_DIR}/Contents/Frameworks

echo "Change dylib links"
sudo install_name_tool -change /System/Library/Frameworks/Python.framework/Versions/2.7/Python @executable_path/../Resources/lib/libpython2.7.dylib ${MDANSE_APP_DIR}/Contents/Resources/bin/python
sudo install_name_tool -id @loader_path/libpython2.7.dylib ${MDANSE_APP_DIR}/Contents/Resources/lib/libpython2.7.dylib
sudo install_name_tool -change /usr/local/opt/gettext/lib/libintl.8.dylib @executable_path/../Frameworks/libintl.8.dylib ${MDANSE_APP_DIR}/Contents/Frameworks/libpython2.7.dylib
sudo install_name_tool -change $RUNNER_TOOL_CACHE/Python/2.7.18/x64/lib/libpython2.7.dylib  @executable_path/../Resources/lib/libpython2.7.dylib ${MDANSE_APP_DIR}/Contents/Frameworks/libpython2.7.dylib
sudo install_name_tool -change /usr/local/opt/gettext/lib/libintl.8.dylib @executable_path/../Frameworks/libintl.8.dylib ${MDANSE_APP_DIR}/Contents/Frameworks/libintl.8.dylib
sudo install_name_tool -change /usr/lib/liconv.2.dylib @executable_path/../Frameworks/liconv.2.dylib ${MDANSE_APP_DIR}/Contents/Frameworks/libintl.8.dylib

sudo ln -s ../Resources/bin/python ${MDANSE_APP_DIR}/Contents/MacOS/python27

sudo cp ${GITHUB_WORKSPACE}/BuildServer/Unix/MacOS/site.py ${MDANSE_APP_DIR}/Contents/Resources/.
sudo cp ${GITHUB_WORKSPACE}/BuildServer/Unix/MacOS/site.py ${MDANSE_APP_DIR}/Contents/Resources/lib/python2.7/.

chmod 777 ${GITHUB_WORKSPACE}/BuildServer/Unix/MacOS/change_dylib_path.sh

echo -e "${BLUE}""Changing dyilib paths""${NORMAL}"
"${GITHUB_WORKSPACE}/BuildServer/Unix/MacOS/change_dylib_path.sh"

# Comment the 'add_system_python_extras' call that add some System path to the sys.path
echo "Comment out in __boot__.py"
sudo "${SED_I_COMMAND[@]}" "s/^add_system_python_extras()$/#add_system_python_extras()/" ${MDANSE_APP_DIR}/Contents/Resources/__boot__.py
sudo "${SED_I_COMMAND[@]}" "s/^_boot_multiprocessing()$/#_boot_multiprocessing()/" ${MDANSE_APP_DIR}/Contents/Resources/__boot__.py

#############################
# Cleanup
#############################
# Removing matplotlib/tests ==> 45.2 Mb
echo "Remove files"
sudo rm -rf ${MDANSE_APP_DIR}/Contents/Resources/lib/python2.7/site-packages/matplotlib/tests
# Sample data for matplotlib is useless
sudo rm -rf ${MDANSE_APP_DIR}/Contents/Resources/lib/python2.7/site-packages/matplotlib/mpl-data/sample_data
sudo rm -rf ${MDANSE_APP_DIR}/Contents/Resources/mpl-data/sample_data
# Scipy package is useless
sudo rm -rf ${MDANSE_APP_DIR}/Contents/Resources/lib/python2.7/site-packages/scipy
# ZMQ package is useless
sudo rm -rf ${MDANSE_APP_DIR}/Contents/Resources/lib/python2.7/site-packages/zmq
# Remove python
sudo rm -rf $HOME/Contents
#Uninstall Sphinx and py2app
sudo rm -rf ${MDANSE_APP_DIR}/Contents/Resources/lib/python2.7/site-packages/sphinx*
sudo rm -rf ${MDANSE_APP_DIR}/Contents/Resources/lib/python2.7/site-packages/Sphinx
sudo rm -rf ${MDANSE_APP_DIR}/Contents/Resources/lib/python2.7/site-packages/alabaster*
sudo rm -rf ${MDANSE_APP_DIR}/Contents/Resources/lib/python2.7/site-packages/py2app*

sudo rm -rf ${MDANSE_APP_DIR}/Contents/Resources/conf_
#############################
# Create DMG
#############################
sleep 5
echo "Create dmg"
"$GITHUB_WORKSPACE/BuildServer/Unix/MacOS/create-dmg" --background "${GITHUB_WORKSPACE}/BuildServer/Unix/MacOS/Resources/dmg/dmg_background.jpg" --volname "MDANSE" --window-pos 200 120 --window-size 800 400 --icon MDANSE.app 200 190 --hide-extension MDANSE.app --app-drop-link 600 185 "${MDANSE_DMG}" ${CI_TEMP_DIR}/dist
sudo mv ${GITHUB_WORKSPACE}/BuildServer/Unix/MacOS/${MDANSE_DMG} ${GITHUB_WORKSPACE}

cd /usr/local/opt
ls