#!/bin/bash

#############################
# CONFIGURATION
#############################

if [ ! $1 ]; then
	echo "Need a build target ! [ win32 | win-amd64]"
	exit 1
fi

BUILD_TARGET=$1
if [ $BUILD_TARGET = "win32" ]; then
	PYTHON_SUFFIX=""
	MSVC_BUILD_TARGET="/x86"
elif [ $BUILD_TARGET = "win-amd64" ]; then
	PYTHON_SUFFIX=".amd64"
	MSVC_BUILD_TARGET="/x64"
else
	echo "Unrecognized build target ! [ win32 | win-amd64]"
	exit 1 # signal error
fi

# Test for an optional second parameter
DO_CLEAN_UP="1"
if [ $2 -a $2 = "no_cleanup" ]; then
	DO_CLEAN_UP="0"
fi

##Which versions of external programs to use
PYTHON_VERSION=2.7.6

# Change working directory to the directory the script is in
# http://stackoverflow.com/a/246128
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
#echo "SCRIPT_DIR : $SCRIPT_DIR"

# Remove the log file created at the previous build
rm -f NSISlog.txt

# This is the directory that will contain the temporary installation
TARGET_DIR="C:\nmoldyn_temp_${BUILD_TARGET}"
TARGET_DIR_CYGWIN=$(cygpath -u $TARGET_DIR)

if [ -e $TARGET_DIR_CYGWIN ]; then
	echo "Removing previous target dir : $TARGET_DIR_CYGWIN"
	rm -rf ${TARGET_DIR_CYGWIN}
fi

#############################
# Support functions
#############################
function checkTool
{
	if [ -z "`which $1`" ]; then
		echo "The $1 command must be somewhere in your \$PATH."
		echo "Fix your \$PATH or install $2"
		exit 1
	fi
}

function downloadURL
{
	filename=`basename "$1"`
	echo "Checking for $filename"
	if [ ! -f "$filename" ]; then
		echo "Downloading $1"
		curl -L -O "$1"
		if [ $? != 0 ]; then
			echo "Failed to download $1"
			exit 1
		fi
	fi
}

function extract
{
	echo "Extracting $*"
	echo "7z x -y $*" >> log.txt
	7z x -y $* >> log.txt
}


checkTool curl "curl: http://curl.haxx.se/"
if [ $BUILD_TARGET = "win32" ] || [ $BUILD_TARGET = "win-amd64" ] ; then
	#Check if we have 7zip, needed to extract and packup a bunch of packages for windows.
	checkTool 7z "7zip: http://www.7-zip.org/"
fi

#For building under MacOS we need gnutar instead of tar
if [ -z `which gnutar >/dev/null 2>&1` ]; then
	TAR=tar
else
	TAR=gnutar
fi

#############################
# Build the packages
#############################

cd "$SCRIPT_DIR"

if [ $BUILD_TARGET = "win32" ] || [ $BUILD_TARGET = "win-amd64" ]; then

	DEPENDENCIES_DIR=dependencies/${BUILD_TARGET}
	PYTHON_MSI_WIN=$(cygpath -a -w ${DEPENDENCIES_DIR}/python-${PYTHON_VERSION}${PYTHON_SUFFIX}.msi)
	
	echo DEPENDENCIES_DIR $DEPENDENCIES_DIR
	echo PYTHON_MSI_WIN $PYTHON_MSI_WIN
	echo TARGET_DIR $TARGET_DIR
	
	echo "Extracting clean python <${PYTHON_MSI_WIN}> in <${TARGET_DIR}>"
    cmd /c "msiexec  /L* pythonlog.txt /qn /a ${PYTHON_MSI_WIN} TARGETDIR=${TARGET_DIR}"
	
	# Exit now if something goes wrong
	if [ $? -ne 0 ]; then
		status = $?
		echo "Failed to extract python"
		exit status
	fi


    #Clean up python a bit, to keep the package size down
	echo "Cleaning up Python"
	rm -rf ${TARGET_DIR_CYGWIN}/Doc
	rm -rf ${TARGET_DIR_CYGWIN}/Lib/site-packages
	rm -rf ${TARGET_DIR_CYGWIN}/Lib/test
	rm -rf ${TARGET_DIR_CYGWIN}/locale
	rm -rf ${TARGET_DIR_CYGWIN}/Logs
	rm -rf ${TARGET_DIR_CYGWIN}/share
	rm -rf ${TARGET_DIR_CYGWIN}/Scripts
	rm -rf ${TARGET_DIR_CYGWIN}/tcl

	mkdir -p ${TARGET_DIR_CYGWIN}/Lib/site-packages
	mkdir -p ${TARGET_DIR_CYGWIN}/Scripts
				
	cd ${DEPENDENCIES_DIR}
	echo "Extracting dependencies"
	# extract numpy
	extract numpy-MKL-1.8.0.${BUILD_TARGET}-py2.7.exe PLATLIB
	# extract matplotlib and its dependencies
	extract pyparsing-2.0.1.${BUILD_TARGET}-py2.7.exe PURELIB
	extract python-dateutil-2.2.${BUILD_TARGET}-py2.7.exe PURELIB
	extract pytz-2013.9.${BUILD_TARGET}-py2.7.exe PURELIB
	extract six-1.5.2.${BUILD_TARGET}-py2.7.exe PURELIB
	extract matplotlib-1.3.1.${BUILD_TARGET}-py2.7.exe PLATLIB
	#extract Cython
	extract Cython-0.19.2.${BUILD_TARGET}-py2.7.exe PLATLIB
	extract Cython-0.19.2.${BUILD_TARGET}-py2.7.exe SCRIPTS
	# extract Pyro
	extract Pyro-3.16.${BUILD_TARGET}.exe PURELIB	
	# extract VTK
	extract VTK-5.10.1.${BUILD_TARGET}-py2.7.exe PURELIB
    # extract wxPython and its dependencies
	extract wxPython-common-2.8.12.1.${BUILD_TARGET}-py2.7.exe PURELIB    
	extract wxPython-2.8.12.1.${BUILD_TARGET}-py2.7.exe PLATLIB
	# extract ScientificPython
	extract ScientificPython-2.9.2.${BUILD_TARGET}-py2.7.exe DATA
	extract ScientificPython-2.9.2.${BUILD_TARGET}-py2.7.exe PLATLIB
	extract ScientificPython-2.9.2.${BUILD_TARGET}-py2.7.exe SCRIPTS
	# extract MMTK
	extract MMTK-2.7.6.${BUILD_TARGET}-py2.7.exe PLATLIB
			
	cd ${SCRIPT_DIR}
	
	# move the packages to the target directory
	echo "Moving deps to target"
	mv ${DEPENDENCIES_DIR}/PLATLIB/numpy ${TARGET_DIR_CYGWIN}/Lib/site-packages/numpy
	mv ${DEPENDENCIES_DIR}/PURELIB/dateutil ${TARGET_DIR_CYGWIN}/Lib/site-packages/dateutil
	mv ${DEPENDENCIES_DIR}/PURELIB/pyparsing.py ${TARGET_DIR_CYGWIN}/Lib/site-packages/pyparsing.py
	mv ${DEPENDENCIES_DIR}/PURELIB/pytz ${TARGET_DIR_CYGWIN}/Lib/site-packages/pytz
	mv ${DEPENDENCIES_DIR}/PURELIB/six.py ${TARGET_DIR_CYGWIN}/Lib/site-packages/six.py
	mv ${DEPENDENCIES_DIR}/PLATLIB/matplotlib ${TARGET_DIR_CYGWIN}/Lib/site-packages/matplotlib
	mv ${DEPENDENCIES_DIR}/PLATLIB/Cython ${TARGET_DIR_CYGWIN}/Lib/site-packages/Cython
	mv ${DEPENDENCIES_DIR}/SCRIPTS/cython.py ${TARGET_DIR_CYGWIN}/Scripts/cython.py
	cp ${TARGET_DIR}/Scripts/cython.py ${TARGET_DIR_CYGWIN}/Lib/site-packages/
	mv ${DEPENDENCIES_DIR}/PURELIB/Pyro ${TARGET_DIR_CYGWIN}/Lib/site-packages/Pyro
	mv ${DEPENDENCIES_DIR}/PURELIB/vtk ${TARGET_DIR_CYGWIN}/Lib/site-packages/vtk
    mv ${DEPENDENCIES_DIR}/PURELIB/wx.pth ${TARGET_DIR_CYGWIN}/Lib/site-packages/
    mv ${DEPENDENCIES_DIR}/PURELIB/wxversion.py ${TARGET_DIR_CYGWIN}/Lib/site-packages/
    mv ${DEPENDENCIES_DIR}/PLATLIB/wx-2.8-msw-unicode ${TARGET_DIR_CYGWIN}/Lib/site-packages/wx-2.8-msw-unicode
    mv ${DEPENDENCIES_DIR}/PLATLIB/Scientific ${TARGET_DIR_CYGWIN}/Lib/site-packages/Scientific
    # this is a hack due to a bug introduced by Konrad in version 2.9.2 of Scientific: the N.package is not defined anymore 
    # which triggers erros for modules that used N.package (e.g. MMTK.Random)
    echo "package='NumPy'" >> ${TARGET_DIR_CYGWIN}/Lib/site-packages/Scientific/N.py
	mv ${DEPENDENCIES_DIR}/DATA/Lib/site-packages/Scientific/netcdf3.dll ${TARGET_DIR_CYGWIN}/Lib/site-packages/Scientific
    mv ${DEPENDENCIES_DIR}/SCRIPTS/task_manager ${TARGET_DIR_CYGWIN}/Scripts/task_manager
	mv ${DEPENDENCIES_DIR}/PLATLIB/MMTK ${TARGET_DIR_CYGWIN}/Lib/site-packages/MMTK

fi

# take the latest version of nmoldyn available on the forge
echo "Getting last nMolDyn revision (devel)"

svn co http://forge.epn-campus.eu/svn/nmoldyn/devel

# Get revision number from svn
REV_NUMBER=$(svnversion devel)
echo "Revision number is $REV_NUMBER"

# go the nmoldyn base directory
cd devel

# Add current revision number to python source code (will appear in "About..." dialog)
sed -i "s/__revision__ = \"undefined\"/__revision__ = \"${REV_NUMBER}\"/" nMOLDYN/__pkginfo__.py

# setup the environment for a visual studio build of nmoldyn using microsoft SDK 7.0 and build nmoldyn
echo "nMolDyn setup and build"
cmd /V:ON /E:ON /C start /WAIT "..\setup_and_build.bat" "${TARGET_DIR}" ${MSVC_BUILD_TARGET}

# Exit now if unable to build
if [ $? -ne 0 ]; then
	status = $?
	echo "Failed to build nMolDyn"
	exit status
fi


# go back to the installation base directory
cd "${SCRIPT_DIR}"

# fetching the current version of nMoldyn from the repository
##VERSION=`${TARGET_DIR}/python.exe -c "d={};execfile('devel/nMOLDYN/__pkginfo__.py',d);print d['__version__']"`
##VERSION=$(echo $VERSION|tr -d '\r')

# Other way to fetch the current version without python 
VERSION=$(grep -Po '(?<=__version__ = \")\d.\d.\d' devel/nMOLDYN/__pkginfo__.py)


# create the nmoldyn installer
echo "Creating nsis installer for target ${BUILD_TARGET}..."
makensis /V4 /ONSISlog.txt /DVERSION=${VERSION} /DARCH=${BUILD_TARGET} /DPYTHON_INST="${TARGET_DIR}" /DREVISION=${REV_NUMBER}  nmoldyn_installer.nsi

# delete devel and dependencies....
if [ ${DO_CLEAN_UP} = "1" ]; then 
	echo "Cleaning up temporary repository"
	rm -rf devel
	rm -rf "${TARGET_DIR}"
	#remove the temporary directories used for package extraction
	rm -rf ${DEPENDENCIES_DIR}/DATA
	rm -rf ${DEPENDENCIES_DIR}/PLATLIB
	rm -rf ${DEPENDENCIES_DIR}/PURELIB
	rm -rf ${DEPENDENCIES_DIR}/SCRIPTS
	rm -f ${DEPENDENCIES_DIR}/log.txt
fi
echo "Done"