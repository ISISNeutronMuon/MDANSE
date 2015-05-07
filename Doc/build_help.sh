#!/bin/sh

MDANSE_HELP="../MDANSE/Doc/Help"

rm -rf ${MDANSE_HELP}

mkdir -p ${MDANSE_HELP}
mkdir ${MDANSE_HELP}/_static
mkdir ${MDANSE_HELP}/_templates

sphinx-apidoc -o  ${MDANSE_HELP} -F --separate -d 5 -H MDANSE -A "G. Goret & E. Pellegrini"  -V 1.0 -R 1.0 ../MDANSE

cp conf_help.py ${MDANSE_HELP}/conf.py

cp layout.html ${MDANSE_HELP}/_templates/

cp mdanse_logo.png ${MDANSE_HELP}/_static/

sphinx-build -b htmlhelp ${MDANSE_HELP} ${MDANSE_HELP}
