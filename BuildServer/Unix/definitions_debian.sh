export ARCH=amd64
export DISTRO=Xenial
export PYTHONEXE=/usr/bin/python
# The sed -i"" is compulsory other crashes on macos
export SED_I_COMMAND='sed -i'
export MDANSE_SOURCE_DIR=`pwd`
export MDANSE_TEMPORARY_INSTALLATION_DIR=${MDANSE_SOURCE_DIR}/BuildServer/Unix/Build_Debian
export PYTHONPATH=${MDANSE_TEMPORARY_INSTALLATION_DIR}/lib/python2.7/site-packages/:${PYTHONPATH}
export RED="\\033[1;31m"
export BLUE="\\033[1;34m"
export NORMAL="\\033[0m"
