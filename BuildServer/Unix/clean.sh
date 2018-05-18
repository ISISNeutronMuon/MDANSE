#!/bin/bash

#############################
# PREPARATION
#############################
cd ${MDANSE_SOURCE_DIR}

#############################
# UNITARY TESTS
#############################
echo -e "${BLUE}""Cleaning repository""${NORMAL}"
rm -rf MDANSE_TEMPORARY_INSTALLATION_DIR
rm -rf build
rm -rf BuildServer/Build_Debian
rm -rf BuildServer/Build_macOS
rm -rf BuildServer/Unix/Build_Debian
rm -rf BuildServer/Unix/Build_macOS