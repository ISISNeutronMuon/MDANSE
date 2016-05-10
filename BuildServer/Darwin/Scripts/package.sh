#!/bin/bash

# This script is to package the nMolDyn package for Mac OS X

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
BUILD_TARGET=darwin

cd ../../../

declare -x MDANSE_VERSION=$(perl -pe '($_)=/([0-9]+([.][0-9]+)+)/' MDANSE/__pkginfo__.py)
echo ${MDANSE_VERSION}
exit

# Which version name are we appending to the final archive
TARGET_DIR=MDANSE-${MDANSE_VERSION}-${BUILD_TARGET}

# take the latest version of nmoldyn available on the forge
echo -e "$BLEU""Getting last MDANSE revision" "$NORMAL"

# Get revision number from git (without trailing newline)
# export REV_NUMBER=$(git rev-list --count HEAD)
# echo "$BLEU""Revision number is -->${REV_NUMBER}<--" "$NORMAL"

# Add current revision number to python source code (will appear in "About..." dialog)
# see http://stackoverflow.com/questions/7648328/getting-sed-error
# sed -i "" "s/__revision__ = \"undefined\"/__revision__ = \"${REV_NUMBER}\"/" MDANSE/__pkginfo__.py

# Now build last version and install it in our homebrewed python
echo -e "$BLEU""Building MDANSE" "$NORMAL"

# Clean up temporary build directories
rm -rf build
rm -rf dist

# Remove previous install of MDANSE
rm /usr/local/bin/mdanse*
rm /usr/local/lib/python2.7/site-packages/MDANSE*.egg-info
rm -rf /usr/local/lib/python2.7/site-packages/MDANSE

# Build and install MDANSE to the homebrewed python
/usr/local/bin/python setup.py build
/usr/local/bin/python setup.py install

# Performs the unit tests
cd Tests/UnitTests
nosetests --verbosity=3 -P .
cd ../..

cd Tests/FunctionalTests/Jobs
python BuildJobTests.py
nosetests --verbosity=3 --exe -P .
cd ../../..

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

#Add MDANSE version file (should read the version from the bundle with pyobjc, but will figure that out later)
echo "${MDANSE_VERSION}"> dist/MDANSE.app/Contents/Resources/version

MDANSE_DMG=MDANSE-${MDANSE_VERSION}-${BUILD_TARGET}.dmg

rm -f ./${MDANSE_DMG}
rm -f ./rw.${MDANSE_DMG}

hdiutil unmount /Volumes/MDANSE -force -quiet

sleep 5

../Tools/create-dmg/create-dmg --background "../Resources/background.jpg" --volname "MDANSE" --window-pos 200 120 --window-size 800 400 --icon MDANSE.app 200 190 --hide-extension MDANSE.app --app-drop-link 600 185 ${MDANSE_DMG} ./dist

curl -T ${MDANSE_DMG} ftp://$CI_FTP_USER_USERNAME:$CI_FTP_USER_PASSWORD@ftp.ill.fr/mdanse/
exit


