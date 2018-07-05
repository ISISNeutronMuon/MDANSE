#!/bin/bash

#############################
# CONFIGURATION
#############################
# Debug option for py2app, if needed
export DISTUTILS_DEBUG=0

#############################
# PREPARATION
#############################
cd ${CI_PROJECT_DIR}

MDANSE_APP_DIR=${CI_TEMP_DIR}/dist/MDANSE.app

#############################
# PACKAGING
#############################
echo -e "${BLUE}""Packaging MDANSE""${NORMAL}"
MDANSE_DMG=MDANSE-${VERSION_NAME}-${DISTRO}-${ARCH}.dmg

cd ${CI_PROJECT_DIR}/BuildServer/Unix/MacOS
${PYTHONEXE} build.py py2app
status=$?
if [ $status -ne 0 ]; then
	echo -e "${RED}" "Cannot build app.""${NORMAL}"
	exit $status
fi

# Add MDANSE version file (should read the version from the bundle with pyobjc, but will figure that out later)
echo "${VERSION_NAME}" > ${MDANSE_APP_DIR}/Contents/Resources/version

#############################
# Copying Python
#############################

### When launching the bundle, the executable target (i.e. MDANSE) modify the python that is shipped with the bundle (si.e. package path, dylib dependencies ...)
### see http://joaoventura.net/blog/2016/embeddable-python-osx/ for technical details
### In our case we also want the user to be able to start directly python without launching the bundle executable (e.g. to run scripts in command line) which is the reason
### why we have to modify the python executable appropriately with the following commands
rm ${MDANSE_APP_DIR}/Contents/MacOS/python
mkdir ${MDANSE_APP_DIR}/Contents/Resources/bin
cp /System/Library/Frameworks/Python.framework/Versions/2.7/Resources/Python.app/Contents/MacOS/Python ${MDANSE_APP_DIR}/Contents/Resources/bin/python

cp -r /System/Library/Frameworks/Python.framework/Versions/2.7/lib/python2.7/* ${MDANSE_APP_DIR}/Contents/Resources/lib/python2.7/
cp /System/Library/Frameworks/Python.framework/Versions/2.7/Python ${MDANSE_APP_DIR}/Contents/Resources/lib/libpython2.7.dylib
chmod 777 ${MDANSE_APP_DIR}/Contents/Resources/lib/libpython2.7.dylib

install_name_tool -change /System/Library/Frameworks/Python.framework/Versions/2.7/Python @executable_path/../lib/libpython2.7.dylib ${MDANSE_APP_DIR}/Contents/Resources/bin/python
install_name_tool -id @loader_path/libpython2.7.dylib ${MDANSE_APP_DIR}/Contents/Resources/lib/libpython2.7.dylib

ln -s ../Resources/bin/python ${MDANSE_APP_DIR}/Contents/MacOS/python

# Do some manual cleanup, e.g.
rm ${MDANSE_APP_DIR}/Contents/Resources/lib/python2.7/MDANSE/__pkginfo__.py\"\"
# matplotlib/tests ==> 45.2 Mb
#rm -rf ${MDANSE_APP_DIR}/Contents/Resources/lib/python2.7/matplotlib/tests
#rm -rf ${MDANSE_APP_DIR}/Contents/Resources/mpl-data/sample_data
#rm -rf ${MDANSE_APP_DIR}/Contents/Resources/lib/python2.7/scipy
#rm -rf ${MDANSE_APP_DIR}/Contents/Resources/lib/python2.7/zmq

#mkdir ${MDANSE_APP_DIR}/Contents/Frameworks/Python.framework
#mkdir ${MDANSE_APP_DIR}/Contents/Frameworks/Python.framework/Versions
#mkdir ${MDANSE_APP_DIR}/Contents/Frameworks/Python.framework/Versions/2.7
#mkdir ${MDANSE_APP_DIR}/Contents/Frameworks/Python.framework/Versions/2.7/lib
#cp -r /System/Library/Frameworks/Python.framework/Versions/2.7/lib/python2.7/ ${MDANSE_APP_DIR}/Contents/Frameworks/Python.framework/Versions/2.7/lib/python2.7
#rm -rf ${MDANSE_APP_DIR}/Contents/Frameworks/Python.framework/Versions/2.7/lib/python2.7/site-packages/*

#rm ${MDANSE_APP_DIR}/Contents/MacOS/python
#cp /System/Library/Frameworks/Python.framework/Versions/2.7/Resources/Python.app/Contents/MacOS/Python ${MDANSE_APP_DIR}/Contents/MacOS/python
#cp /System/Library/Frameworks/Python.framework/Versions/2.7/Python ${MDANSE_APP_DIR}/Contents/Frameworks/Python.framework/Versions/2.7/libpython2.7.dylib

#install_name_tool -change /System/Library/Frameworks/Python.framework/Versions/2.7/Python @executable_path/../Frameworks/Python.framework/Versions/2.7/libpython2.7.dylib ${MDANSE_APP_DIR}/Contents/MacOS/python
#chmod 777 ${MDANSE_APP_DIR}/Contents/Frameworks/Python.framework/Versions/2.7/libpython2.7.dylib
#install_name_tool -id @executable_path/../Frameworks/Python.framework/Versions/2.7/libpython2.7.dylib ${MDANSE_APP_DIR}/Contents/Frameworks/Python.framework/Versions/2.7/libpython2.7.dylib

## In order that the modified python in the bundle import the zipped sitepackages located in Contents/Resources we provide a modified site.py that will
## update the sys.path accordingly

#cp ${CI_PROJECT_DIR}/BuildServer/Unix/MacOS/site.py ${MDANSE_APP_DIR}/Contents/Frameworks/Python.framework/Versions/2.7/lib/python2.7/.

chmod 777 ${CI_PROJECT_DIR}/BuildServer/Unix/MacOS/change_dylib_path.sh
${CI_PROJECT_DIR}/BuildServer/Unix/MacOS/change_dylib_path.sh

#############################
# Create DMG
#############################
hdiutil unmount /Volumes/MDANSE -force -quiet
sleep 5

${CI_PROJECT_DIR}/BuildServer/Unix/MacOS/dmg/create-dmg --background "${CI_PROJECT_DIR}/BuildServer/Unix/MacOS/dmg/dmg_background.jpg" --volname "MDANSE" --window-pos 200 120 --window-size 800 400 --icon MDANSE.app 200 190 --hide-extension MDANSE.app --app-drop-link 600 185 "${MDANSE_DMG}" ${CI_PROJECT_DIR}
