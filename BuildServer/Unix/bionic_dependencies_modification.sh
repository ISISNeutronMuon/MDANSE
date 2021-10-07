#!/bin/bash

cd ${CI_PROJECT_DIR}

# Modifying python-vtk to python-vtk6 in CONTROL FILE
cd ${CI_PROJECT_DIR}
sed -i "s/python-vtk/python-vtk6/" $GITHUB_WORKSPACE/BuildServer/Unix/Debian/Resources/DEBIAN/control

status=$?
if [ $status -ne 0 ]; then
	echo -e "${RED}" "Failed to build/install MDANSE""${NORMAL}"
	exit $status
fi
