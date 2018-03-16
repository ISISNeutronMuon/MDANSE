#!/bin/bash

#############################
# CONFIGURATION
#############################

echo $PATH

if [ ! $1 ]; then
    BUILD_TARGET="win-amd64"
else
    BUILD_TARGET=$1
fi

if [ "$BUILD_TARGET" = "win32" ]; then
	PYTHON_SUFFIX=""
	MSVC_BUILD_TARGET="/x86"
elif [ "$BUILD_TARGET" = "win-amd64" ]; then
	PYTHON_SUFFIX=".amd64"
	MSVC_BUILD_TARGET="/x64"
else
	echo "Unrecognized build target ! [ win32 | win-amd64]"
	exit 1 # signal error
fi

##Which versions of external programs to use
PYTHON_VERSION=2.7.6

CI_PROJECT_DIR_WIN=$(cygpath -a -w ${CI_PROJECT_DIR})

# Change working directory to the directory the script is in
# http://stackoverflow.com/a/246128
SCRIPT_DIR="${CI_PROJECT_DIR}/BuildServer/Windows"

# This is the directory that will contain the temporary installation
TARGET_DIR="${CI_PROJECT_DIR_WIN}\\BuildServer\\Windows\\Build"
TARGET_DIR_CYGWIN=$(cygpath -u $TARGET_DIR)

function extract
{
	echo "Extracting $*"
	echo "7z x -y $*" >> log.txt
	7z x -y $* >> log.txt
}

#############################
# Build the packages
#############################

cd "${SCRIPT_DIR}"

if [ -e "$TARGET_DIR_CYGWIN" ]; then
	echo "Removing previous target dir : $TARGET_DIR_CYGWIN"
	rm -rf ${TARGET_DIR_CYGWIN}
fi

DEPENDENCIES_DIR=${CI_WINDOWS_DEPENDENCIES_PATH_UNIX}/${BUILD_TARGET}

PYTHON_MSI=python-${PYTHON_VERSION}${PYTHON_SUFFIX}.msi
PYTHON_MSI_WIN=${CI_WINDOWS_DEPENDENCIES_PATH}\\${BUILD_TARGET}\\${PYTHON_MSI}

echo "Extracting python ${PYTHON_MSI_WIN} in ${TARGET_DIR}"
cmd /c "msiexec  /L* pythonlog.txt /qn /a ${PYTHON_MSI_WIN} TARGETDIR=${TARGET_DIR}"

# Exit now if something goes wrong
if [ $? -ne 0 ]; then
	status=$?
	echo "Failed to extract python"
	exit status
fi

#Clean up python a bit, to keep the package size down
echo "Cleaning up Python"
rm -rf ${TARGET_DIR_CYGWIN}/Doc
rm -rf ${TARGET_DIR_CYGWIN}/Lib/site-packages
rm -rf ${TARGET_DIR_CYGWIN}/Lib/test
rm -rf ${TARGET_DIR_CYGWIN}/Tools/Scripts
rm -rf ${TARGET_DIR_CYGWIN}/tcl
rm -f ${TARGET_DIR_CYGWIN}/NEWS.txt
rm -f ${TARGET_DIR_CYGWIN}/${PYTHON_MSI}

mkdir -p ${TARGET_DIR_CYGWIN}/Lib/site-packages
mkdir -p ${TARGET_DIR_CYGWIN}/Scripts

cd ${DEPENDENCIES_DIR}

echo "Extracting dependencies"

# extract setuptools
extract setuptools-28.7.1.${BUILD_TARGET}.exe PURELIB

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

# extract Sphinx and its dependencies
extract alabaster-0.7.5.${BUILD_TARGET}.exe PURELIB
extract Pygments-2.0.2.${BUILD_TARGET}.exe PURELIB
extract Pygments-2.0.2.${BUILD_TARGET}.exe SCRIPTS
extract Babel-1.3.${BUILD_TARGET}.exe PURELIB
extract Babel-1.3.${BUILD_TARGET}.exe SCRIPTS
extract MarkupSafe-0.23.${BUILD_TARGET}-py2.7.exe PLATLIB
extract Jinja2-2.7.3.${BUILD_TARGET}.exe PURELIB
extract docutils-0.12.${BUILD_TARGET}.exe PURELIB
extract docutils-0.12.${BUILD_TARGET}.exe SCRIPTS
extract Sphinx-1.3.1.${BUILD_TARGET}.exe PURELIB
extract sphinx_rtd_theme-0.1.8.${BUILD_TARGET}.exe PURELIB

extract nose-1.3.7.${BUILD_TARGET}.exe PURELIB
extract nose-1.3.7.${BUILD_TARGET}.exe SCRIPTS

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

# move the packages to the target directory
echo "Moving dependencies to ${BUILD_TARGET}"

mv PURELIB/pkg_resources ${TARGET_DIR_CYGWIN}/Lib/site-packages/pkg_resources

mv PLATLIB/numpy ${TARGET_DIR_CYGWIN}/Lib/site-packages/numpy

mv PURELIB/dateutil ${TARGET_DIR_CYGWIN}/Lib/site-packages/dateutil
mv PURELIB/pyparsing.py ${TARGET_DIR_CYGWIN}/Lib/site-packages/pyparsing.py
mv PURELIB/pytz ${TARGET_DIR_CYGWIN}/Lib/site-packages/pytz
mv PURELIB/six.py ${TARGET_DIR_CYGWIN}/Lib/site-packages/six.py
mv PLATLIB/matplotlib ${TARGET_DIR_CYGWIN}/Lib/site-packages/matplotlib

mv PLATLIB/Cython ${TARGET_DIR_CYGWIN}/Lib/site-packages/Cython
mv SCRIPTS/cython.py ${TARGET_DIR_CYGWIN}/Scripts/cython.py
cp ${TARGET_DIR}/Scripts/cython.py ${TARGET_DIR_CYGWIN}/Lib/site-packages/
mv PURELIB/Pyro ${TARGET_DIR_CYGWIN}/Lib/site-packages/Pyro

mv PURELIB/alabaster ${TARGET_DIR_CYGWIN}/Lib/site-packages/alabaster
mv PURELIB/pygments ${TARGET_DIR_CYGWIN}/Lib/site-packages/pygments
mv SCRIPTS/pygment* ${TARGET_DIR_CYGWIN}/Scripts/
mv PURELIB/babel ${TARGET_DIR_CYGWIN}/Lib/site-packages/babel
mv SCRIPTS/pybabel* ${TARGET_DIR_CYGWIN}/Scripts/
mv PLATLIB/markupsafe ${TARGET_DIR_CYGWIN}/Lib/site-packages/markupsafe
mv PURELIB/jinja2 ${TARGET_DIR_CYGWIN}/Lib/site-packages/jinja2
mv PURELIB/docutils ${TARGET_DIR_CYGWIN}/Lib/site-packages/docutils
mv SCRIPTS/rst* ${TARGET_DIR_CYGWIN}/Scripts/
mv PURELIB/sphinx ${TARGET_DIR_CYGWIN}/Lib/site-packages/sphinx
mv PURELIB/sphinx_rtd_theme ${TARGET_DIR_CYGWIN}/Lib/site-packages/sphinx_rtd_theme

mv PURELIB/nose ${TARGET_DIR_CYGWIN}/Lib/site-packages/nose
mv SCRIPTS/nosetests ${TARGET_DIR_CYGWIN}/Scripts/

mv PURELIB/vtk ${TARGET_DIR_CYGWIN}/Lib/site-packages/vtk

mv PURELIB/wx.pth ${TARGET_DIR_CYGWIN}/Lib/site-packages/
mv PURELIB/wxversion.py ${TARGET_DIR_CYGWIN}/Lib/site-packages/
mv PLATLIB/wx-2.8-msw-unicode ${TARGET_DIR_CYGWIN}/Lib/site-packages/wx-2.8-msw-unicode

echo "package='NumPy'" >> PLATLIB/Scientific/N.py
mv PLATLIB/Scientific ${TARGET_DIR_CYGWIN}/Lib/site-packages/Scientific
# this is a hack due to a bug introduced by Konrad in version 2.9.2 of Scientific: the N.package is not defined anymore
# which triggers erros for modules that used N.package (e.g. MMTK.Random)
mv DATA/Lib/site-packages/Scientific/netcdf3.dll ${TARGET_DIR_CYGWIN}/Lib/site-packages/Scientific
mv SCRIPTS/task_manager ${TARGET_DIR_CYGWIN}/Scripts/task_manager

mv PLATLIB/MMTK ${TARGET_DIR_CYGWIN}/Lib/site-packages/MMTK

rm -rf DATA
rm -rf PLATLIB
rm -rf PURELIB
rm -rf SCRIPTS

cd ${SCRIPT_DIR}

rm pythonlog.txt

cd ${CI_PROJECT_DIR}

# Update the __pkginfo__ file with the current commit 
COMMIT_ID=$(git rev-parse --short HEAD)
sed -i "s/.*__commit__.*/__commit__ = \"${COMMIT_ID}\"/" MDANSE/__pkginfo__.py

# Get revision number from GIT
echo "Commit id ${COMMIT_ID}"

# setup the environment for a visual studio build of MDANSE using microsoft SDK 7.0 and build MDANSE
echo "MDANSE setup and build"

# go back to the installation base directory
cd ${SCRIPT_DIR}

cmd /V:ON /E:ON /C "setup_and_build.bat" "${CI_PROJECT_DIR_WIN}" "${TARGET_DIR}" ${MSVC_BUILD_TARGET}

# Exit now if unable to build
if [ $? -ne 0 ]; then
	status=$?
	echo "Failed to build MDANSE"
	exit $status
fi
