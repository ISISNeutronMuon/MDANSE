#!/bin/bash

#############################
# CONFIGURATION
#############################
# Debug option for py2app, if needed
export DISTUTILS_DEBUG=0

#############################
# PREPARATION
#############################
cd ${MDANSE_SOURCE_DIR}
rm -rf ${MDANSE_TEMPORARY_INSTALLATION_DIR}/build
rm -rf ${MDANSE_TEMPORARY_INSTALLATION_DIR}/dist

#############################
# PACKAGING
#############################
echo -e "${BLUE}""Packaging MDANSE""${NORMAL}"
MDANSE_DMG=MDANSE-${VERSION_NAME}-${DISTRO}-${ARCH}.dmg
rm -f BuildServer/Unix/${MDANSE_DMG}
rm -f BuildServer/Unix/rw.${MDANSE_DMG}

cd BuildServer/Unix
${PYTHONEXE} MacOS_resources/build.py py2app
status=$?
if [ $status -ne 0 ]; then
	echo -e "${RED}" "Cannot build app.""${NORMAL}"
	${MDANSE_SOURCE_DIR}/BuildServer/Unix/clean.sh
	exit $status
fi

# Do some manual cleanup, e.g.
# matplotlib/tests ==> 45.2 Mb
rm -rf ${MDANSE_TEMPORARY_INSTALLATION_DIR}/dist/MDANSE.app/Contents/Resources/lib/python2.7/matplotlib/tests
rm -rf ${MDANSE_TEMPORARY_INSTALLATION_DIR}/dist/MDANSE.app/Contents/Resources/mpl-data/sample_data

#Add MDANSE version file (should read the version from the bundle with pyobjc, but will figure that out later)
echo "${VERSION_NAME}" > ${MDANSE_TEMPORARY_INSTALLATION_DIR}/dist/MDANSE.app/Contents/Resources/version

hdiutil unmount /Volumes/MDANSE -force -quiet

sleep 5

# When launching the bundle, the executable target (i.e. MDANSE) modify the python that is shipped with the bundle (si.e. package path, dylib dependencies ...)
# see http://joaoventura.net/blog/2016/embeddable-python-osx/ for technical details
# In our case we also want the user to be able to start directly python without launching the bundle executable (e.g. to run scripts in command line) which is the reason
# why we have to modify the python executable appropriately with the following commands
cp -r /Library/Frameworks/Python.framework/Versions/2.7/lib/python2.7/ ${MDANSE_TEMPORARY_INSTALLATION_DIR}/dist/MDANSE.app/Contents/Frameworks/Python.framework/Versions/2.7/lib/python2.7
rm -rf ${MDANSE_TEMPORARY_INSTALLATION_DIR}/dist/MDANSE.app/Contents/Frameworks/Python.framework/Versions/2.7/lib/python2.7/site-packages/*
cp -r ${MDANSE_TEMPORARY_INSTALLATION_DIR}/lib/python2.7/site-packages/Scientific ${MDANSE_TEMPORARY_INSTALLATION_DIR}/dist/MDANSE.app/Contents/Frameworks/Python.framework/Versions/2.7/lib/python2.7/site-packages
cp -r ${MDANSE_TEMPORARY_INSTALLATION_DIR}/lib/python2.7/site-packages/MMTK ${MDANSE_TEMPORARY_INSTALLATION_DIR}/dist/MDANSE.app/Contents/Frameworks/Python.framework/Versions/2.7/lib/python2.7/site-packages
cp /Library/Frameworks/Python.framework/Versions/2.7/Resources/Python.app/Contents/MacOS/Python ${MDANSE_TEMPORARY_INSTALLATION_DIR}/dist/MDANSE.app/Contents/MacOS/python
cp /Library/Frameworks/Python.framework/Versions/2.7/Python ${MDANSE_TEMPORARY_INSTALLATION_DIR}/dist/MDANSE.app/Contents/Frameworks/Python.framework/Versions/2.7/libpython2.7.dylib
install_name_tool -change /Library/Frameworks/Python.framework/Versions/2.7/Python @executable_path/../Frameworks/Python.framework/Versions/2.7/libpython2.7.dylib ${MDANSE_TEMPORARY_INSTALLATION_DIR}/dist/MDANSE.app/Contents/MacOS/python
chmod 777 ${MDANSE_TEMPORARY_INSTALLATION_DIR}/dist/MDANSE.app/Contents/Frameworks/Python.framework/Versions/2.7/libpython2.7.dylib
install_name_tool -id @executable_path/../Frameworks/Python.framework/Versions/2.7/libpython2.7.dylib ${MDANSE_TEMPORARY_INSTALLATION_DIR}/dist/MDANSE.app/Contents/Frameworks/Python.framework/Versions/2.7/libpython2.7.dylib

# In order that the modified python in the bundle import the zipped sitepackages located in Contents/Resources we provide a modified site.py that will
# update the sys.path accordingly

cp ${MDANSE_SOURCE_DIR}/BuildServer/Unix/MacOS_resources/site.py ${MDANSE_TEMPORARY_INSTALLATION_DIR}/dist/MDANSE.app/Contents/Frameworks/Python.framework/Versions/2.7/lib/python2.7/.

chmod 777 ${MDANSE_SOURCE_DIR}/BuildServer/Unix/MacOS_resources//change_dylib_path.sh
${MDANSE_SOURCE_DIR}/BuildServer/Unix/MacOS_resources//change_dylib_path.sh

${MDANSE_SOURCE_DIR}/BuildServer/Unix/MacOS_resources/dmg/create-dmg --background "${MDANSE_SOURCE_DIR}/BuildServer/Unix/MacOS_resources/dmg/dmg_background.jpg" --volname "MDANSE" --window-pos 200 120 --window-size 800 400 --icon MDANSE.app 200 190 --hide-extension MDANSE.app --app-drop-link 600 185 "${MDANSE_DMG}" ${MDANSE_TEMPORARY_INSTALLATION_DIR}/dist
mv ${MDANSE_SOURCE_DIR}/BuildServer/Unix/${MDANSE_DMG} ${MDANSE_SOURCE_DIR}/BuildServer

rm -rf ${MDANSE_TEMPORARY_INSTALLATION_DIR}