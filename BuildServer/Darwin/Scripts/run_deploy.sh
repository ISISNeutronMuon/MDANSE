#!/bin/bash

# This script is to package the MDANSE package for Mac OS X

#############################
# CONFIGURATION
#############################

## Add some colors
ROUGE="\\033[1;31m"
BLEU="\\033[1;34m"

COMMIT_ID=$(git rev-parse --short HEAD)
VERSION_NAME=`sed -n 's/__version__.*=.*\"\(.*\)\"/\1/p' MDANSE/__pkginfo__.py`

if [[ ${CI_BUILD_REF_NAME} =~ develop ]]
then
    if [ -n "${WEEKLY_BUILD}" ]
    then
        VERSION_NAME=${VERSION_NAME}-"weekly-"`date +%Y-%m-%d`
    fi
    VERSION_NAME=${VERSION_NAME}-${COMMIT_ID}
fi

export VERSION_NAME

##Select the build target
BUILD_TARGET=darwin

echo -e "$BLEU""Packaging MDANSE" "$NORMAL"
rm -rf BuildServer/Darwin/Build
mkdir BuildServer/Darwin/Build

# debug option for py2app, if needed
export DISTUTILS_DEBUG=0

cd BuildServer/Darwin/Scripts

/usr/local/bin/python build.py py2app

rc=$?
if [[ $rc != 0 ]]; then
	echo -e "$ROUGE""Cannot build app." "$NORMAL"
	exit 1
fi

cd ../Build

# Do some manual cleanup, e.g.
# matplotlib/tests ==> 45.2 Mb
rm -rf dist/MDANSE.app/Contents/Resources/lib/python2.7/matplotlib/tests
rm -rf dist/MDANSE.app/Contents/Resources/mpl-data/sample_data

MDANSE_DMG=MDANSE-${VERSION_NAME}-${BUILD_TARGET}.dmg

#Add MDANSE version file (should read the version from the bundle with pyobjc, but will figure that out later)
echo "${VERSION_NAME}" > dist/MDANSE.app/Contents/Resources/version

rm -f ./${MDANSE_DMG}
rm -f ./rw.${MDANSE_DMG}

hdiutil unmount /Volumes/MDANSE -force -quiet

sleep 5

# When launching the bundle, the executable target (i.e. MDANSE) modify the python that is shipped with the bundle (si.e. package path, dylib dependencies ...)
# see http://joaoventura.net/blog/2016/embeddable-python-osx/ for technical details
# In our case we also want the user to be able to start directly python without launching the bundle executable (e.g. to run scripts in command line) which is the reason
# why we have to modify the python executable appropriately with the following commands
cp -r /Library/Frameworks/Python.framework/Versions/2.7/lib/python2.7/ ./dist/MDANSE.app/Contents/Frameworks/Python.framework/Versions/2.7/lib/python2.7
rm -rf ./dist/MDANSE.app/Contents/Frameworks/Python.framework/Versions/2.7/lib/python2.7/site-packages/*
cp /Library/Frameworks/Python.framework/Versions/2.7/Resources/Python.app/Contents/MacOS/Python ./dist/MDANSE.app/Contents/MacOS/python
cp /Library/Frameworks/Python.framework/Versions/2.7/Python ./dist/MDANSE.app/Contents/Frameworks/Python.framework/Versions/2.7/libpython2.7.dylib
install_name_tool -change /Library/Frameworks/Python.framework/Versions/2.7/Python @executable_path/../Frameworks/Python.framework/Versions/2.7/libpython2.7.dylib ./dist/MDANSE.app/Contents/MacOS/python
chmod 777 ./dist/MDANSE.app/Contents/Frameworks/Python.framework/Versions/2.7/libpython2.7.dylib
install_name_tool -id @executable_path/../Frameworks/Python.framework/Versions/2.7/libpython2.7.dylib ./dist/MDANSE.app/Contents/Frameworks/Python.framework/Versions/2.7/libpython2.7.dylib

# In order that the modified python in the bundle import the zipped sitepackages located in Contents/Resources we provide a modified site.py that will
# update the sys.path accordingly
cp ../Scripts/site.py ./dist/MDANSE.app/Contents/Frameworks/Python.framework/Versions/2.7/lib/python2.7/.

chmod 777 ../Scripts/change_dylib_path.sh
../Scripts/change_dylib_path.sh

../Tools/create-dmg/create-dmg --background "../Resources/background.jpg" --volname "MDANSE" --window-pos 200 120 --window-size 800 400 --icon MDANSE.app 200 190 --hide-extension MDANSE.app --app-drop-link 600 185 "${MDANSE_DMG}" ./dist

exit
