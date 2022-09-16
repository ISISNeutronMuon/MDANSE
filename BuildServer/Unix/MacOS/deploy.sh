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
cd ${GITHUB_WORKSPACE} || exit

export MDANSE_APP_DIR=${CI_TEMP_DIR}/dist/MDANSE.app

export PYTHONPATH=${CI_TEMP_INSTALL_DIR}/lib/python2.7/site-packages:${PYTHONPATH}

# Build API
sudo install_name_tool -change /Users/runner/hostedtoolcache/Python/3.9.13/x64/lib/libpython3.9.dylib /Users/runner/Contents/Resources/lib/libpython3.9.dylib /Users/runner/Contents/Resources/bin/python3.9
sudo install_name_tool -change /Users/runner/hostedtoolcache/Python/3.9.13/x64/lib/libpython3.9.dylib /Users/runner/Contents/Resources/lib/libpython3.9.dylib /Users/runner/Contents/Resources/bin/python
#sudo ${PYTHONEXE} setup.py build build_api build_help install

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

echo "Uninstall sphinx and its dependencies"
sudo ${PYTHONEXE} -m pip uninstall -y sphinx Jinja2 MarkupSafe Pygments alabaster babel chardet colorama docutils idna imagesize requests snowballstemmer sphinxcontrib-websupport typing urllib3

echo "Building mdanse app"
cd "${GITHUB_WORKSPACE}/BuildServer/Unix/MacOS" || exit
sudo ${PYTHONEXE} build.py py2app --argv-inject "$GITHUB_WORKSPACE" --argv-inject "$VERSION_NAME" --argv-inject "$CI_TEMP_BUILD_DIR" --argv-inject "$CI_TEMP_DIR"
status=$?
if [ $status -ne 0 ]; then
	echo -e "${RED}" "Cannot build app.""${NORMAL}"
	exit $status
fi

# Add MDANSE version file (should read the version from the bundle with pyobjc, but will figure that out later)
echo "Add mdanse version file"
echo "${VERSION_NAME}" | sudo tee "${MDANSE_APP_DIR}/Contents/Resources/version"

# Copy over instruction for using bundled python
sudo cp -fv "$GITHUB_WORKSPACE/BuildServer/Unix/MacOS/Resources/How to use the bundled python.txt" "$MDANSE_APP_DIR/Contents/MacOS"

#############################
# Copying Python
#############################
### When launching the bundle, the executable target (i.e. MDANSE) modify the python that is shipped with the bundle (si.e. package path, dylib dependencies ...)
### see http://joaoventura.net/blog/2016/embeddable-python-osx/ for technical details
### In our case we also want the user to be able to start directly python without launching the bundle executable (e.g. to run scripts in command line) which is the reason
### why we have to modify the python executable appropriately with the following commands
echo -e "${BLUE}""Copying python""${NORMAL}"
sudo mkdir -p ${MDANSE_APP_DIR}/Contents/Resources/bin

echo "Copy lib"
sudo cp -r $HOME/Contents/Resources/lib ${MDANSE_APP_DIR}/Contents/Resources

echo "Copy dependency dylibs"
sudo mv -v ${MDANSE_APP_DIR}/Contents/Resources/lib/lib* ${MDANSE_APP_DIR}/Contents/Frameworks
#sudo cp -v /usr/lib/libz.* ${MDANSE_APP_DIR}/Contents/Frameworks
#sudo cp -v /usr/lib/libc++* ${MDANSE_APP_DIR}/Contents/Frameworks
sudo cp /usr/local/lib/libint*.dylib ${MDANSE_APP_DIR}/Contents/Frameworks

# It is necessary to interlink the following dylibs for them to work properly
echo "Change dylib links"
sudo install_name_tool -change @executable_path/../Frameworks/libpython3.9.dylib /Users/runner/Contents/Resources/lib/libpython3.9.dylib /Users/runner/Contents/Resources/bin/python3.9
sudo install_name_tool -change @executable_path/../Frameworks/libpython3.9.dylib /Users/runner/Contents/Resources/lib/libpython3.9.dylib /Users/runner/Contents/Resources/bin/python
# libpython
sudo install_name_tool -id @executable_path/../Frameworks/libpython3.9.dylib ${MDANSE_APP_DIR}/Contents/Frameworks/libpython3.9.dylib
sudo install_name_tool -change /usr/local/opt/gettext/lib/libintl.8.dylib @executable_path/../Frameworks/libintl.8.dylib ${MDANSE_APP_DIR}/Contents/Frameworks/libpython3.9.dylib
sudo install_name_tool -change /Users/runner/hostedtoolcache/Python/3.9.13/x64/lib/libpython3.9.dylib  @executable_path/../Frameworks/libpython3.9.dylib ${MDANSE_APP_DIR}/Contents/Frameworks/libpython3.9.dylib
# libintl
sudo install_name_tool -change /usr/local/opt/gettext/lib/libintl.8.dylib @executable_path/../Frameworks/libintl.8.dylib ${MDANSE_APP_DIR}/Contents/Frameworks/libintl.8.dylib
sudo install_name_tool -change /usr/lib/libiconv.2.dylib @executable_path/../Frameworks/libiconv.2.dylib ${MDANSE_APP_DIR}/Contents/Frameworks/libintl.8.dylib

echo "Copy site.py"
#sudo cp ${GITHUB_WORKSPACE}/BuildServer/Unix/MacOS/site.py ${MDANSE_APP_DIR}/Contents/Resources/.
#sudo cp ${GITHUB_WORKSPACE}/BuildServer/Unix/MacOS/site.py ${MDANSE_APP_DIR}/Contents/Resources/lib/python2.7/.

echo -e "${BLUE}""Changing wx and vtk dylib links""${NORMAL}"
chmod 777 ${GITHUB_WORKSPACE}/BuildServer/Unix/MacOS/change_dylib_path.sh
"${GITHUB_WORKSPACE}/BuildServer/Unix/MacOS/change_dylib_path.sh"
sudo ${PYTHONEXE} ${GITHUB_WORKSPACE}/BuildServer/Unix/MacOS/relink-vtk.py
cd $GITHUB_WORKSPACE || exit

# Replace __boot__.py with a custom script that simply launches mdanse_gui script in a new shell
echo "Replace __boot__.py"
sudo cp -fv ${GITHUB_WORKSPACE}/BuildServer/Unix/MacOS/__boot__.py ${MDANSE_APP_DIR}/Contents/Resources
echo "./python3 ../Resources/mdanse_gui"  | sudo tee  ${MDANSE_APP_DIR}/Contents/MacOS/launch_mdanse
sudo chmod 755 ${MDANSE_APP_DIR}/Contents/MacOS/launch_mdanse

# Create a bash script that will run the bundled python with $PYTHONHOME set
echo "#!/bin/bash" > ~/python3
{
echo 'SCRIPT_DIR="$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"'
echo 'PARENT_DIR="$(dirname "$SCRIPT_DIR")"'
echo 'export PYTHONHOME=$PARENT_DIR:$PARENT_DIR/Resources'
echo 'export PYTHONPATH=$PARENT_DIR/Resources/lib/python3.9:$PARENT_DIR/Resources:$PARENT_DIR/Resources/lib/python3.9/site-packages'
echo '$SCRIPT_DIR/python "${@:1}"'
} >> ~/python3
sudo cp -v ~/python3 "${MDANSE_APP_DIR}/Contents/MacOS"
sudo chmod 755 "${MDANSE_APP_DIR}/Contents/MacOS/python3"

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
#Remove py2app
sudo rm -rf ${MDANSE_APP_DIR}/Contents/Resources/lib/python2.7/site-packages/py2app

sudo rm -rf ${MDANSE_APP_DIR}/Contents/Resources/conf_
#############################
# Create DMG
#############################
sleep 5
echo "Create dmg"
"$GITHUB_WORKSPACE/BuildServer/Unix/MacOS/create-dmg" --background "${GITHUB_WORKSPACE}/BuildServer/Unix/MacOS/Resources/dmg/dmg_background.jpg" --volname "MDANSE" --window-pos 200 120 --window-size 800 400 --icon MDANSE.app 200 190 --hide-extension MDANSE.app --app-drop-link 600 185 "${MDANSE_DMG}" ${CI_TEMP_DIR}/dist
#sudo mv ${GITHUB_WORKSPACE}/BuildServer/Unix/MacOS/${MDANSE_DMG} ${GITHUB_WORKSPACE}