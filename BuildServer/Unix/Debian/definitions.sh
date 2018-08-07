export ARCH=amd64

export DISTRO=$(lsb_release -c | cut -f2)

export PYTHONEXE=/usr/bin/python

export SED_I_COMMAND=(sed -i)

# Define colors
export RED="\\033[1;31m"
export BLUE="\\033[1;34m"
export NORMAL="\\033[0m"
