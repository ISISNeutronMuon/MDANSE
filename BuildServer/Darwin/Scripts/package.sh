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

##Do we need to create the final archive
ARCHIVE_FOR_DISTRIBUTION=1
##Which version name are we appending to the final archive
export BUILD_NAME=1.0
TARGET_DIR=MDANSE-${BUILD_NAME}-${BUILD_TARGET}

#############################
# Darwin
#############################

if [ "$BUILD_TARGET" = "darwin" ]; then
	
	
	cd ../../../
	
	# take the latest version of nmoldyn available on the forge
	echo -e "$BLEU""Getting last MDANSE revision" "$NORMAL"

	# Get revision number from git (without trailing newline)
	export REV_NUMBER=$(git rev-list --count HEAD)
	echo "$BLEU""Revision number is -->${REV_NUMBER}<--" "$NORMAL"

	# Add current revision number to python source code (will appear in "About..." dialog)
	# see http://stackoverflow.com/questions/7648328/getting-sed-error
	sed -i "" "s/__revision__ = \"undefined\"/__revision__ = \"${REV_NUMBER}\"/" MDANSE/__pkginfo__.py
	
	# Now build last version and install it in our homebrewed python
	echo -e "$BLEU""Building MDANSE" "$NORMAL"
	/usr/local/bin/python setup.py build
	/usr/local/bin/python setup.py install
	
	TARGET_DIR=MDANSE-${BUILD_NAME}-b${REV_NUMBER}-MacOS
	
	echo -e "$BLEU""Packaging MDANSE" "$NORMAL"
	rm -rf build_darwin/build
	rm -rf build_darwin/dist
	
	# debug option for py2app, if needed
	export DISTUTILS_DEBUG=0

        cd BuildServer/Darwin/Scripts

	/usr/local/bin/python build.py py2app
	rc=$?
	if [[ $rc != 0 ]]; then
		echo -e "$ROUGE""Cannot build app." "$NORMAL"
		exit 1
	fi

        cd ../..

	# Do some manual cleanup, e.g.
	# matplotlib/tests ==> 45.2 Mb
	rm -rf build_darwin/dist/MDANSE.app/Contents/Resources/lib/python2.7/matplotlib/tests
	rm -rf build_darwin/dist/MDANSE.app/Contents/Resources/mpl-data/sample_data 


	#Add MDANSE version file (should read the version from the bundle with pyobjc, but will figure that out later)
	echo "$BUILD_NAME b$REV_NUMBER"> build_darwin/dist/MDANSE.app/Contents/Resources/version

	cd build_darwin
	
        # Archive app
	echo -e "$BLEU" "Archiving ${TARGET_DIR}.tar.gz ..." "$NORMAL"
	cd dist
	gnutar cfp - MDANSE.app | gzip --best -c > ../../../${TARGET_DIR}.tar.gz
	cd ..
	exit;
	TODAY=$(date +"%m-%d-%y-%Hh%Mm%S")
	# Create sparse image for distribution
	echo -e "$BLEU" "Creating new MDANSE.dmg.sparseimage ..." "$NORMAL"
	hdiutil detach /Volumes/MDANSE/ -quiet
	# Keep previous build, in case of
	mv -f MDANSE.dmg.sparseimage MDANSE.dmg.sparseimage.${TODAY}.old
	hdiutil convert DmgTemplateCompressed.dmg -format UDSP -o MDANSE.dmg.sparseimage
	hdiutil resize -size 1024m MDANSE.dmg.sparseimage
	hdiutil attach MDANSE.dmg.sparseimage
	echo -e "$BLEU" "Copying MDANSE.app on dmg ..." "$NORMAL"
	cp -a dist/MDANSE.app /Volumes/MDANSE/MDANSE/
	# Reset Custom icon on MDANSE folder
	SetFile -a C /Volumes/MDANSE/MDANSE/
	hdiutil detach /Volumes/MDANSE
	hdiutil convert MDANSE.dmg.sparseimage -format UDZO -imagekey zlib-level=9 -ov -o ../../${TARGET_DIR}.dmg
	echo -e "$VERT" "Done." "$NORMAL"
	exit
fi


