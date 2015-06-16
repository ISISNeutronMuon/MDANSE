#!/bin/sh

MDANSE_API="../MDANSE/Doc/API"

#rm -rf ${MDANSE_API}

#mkdir -p ${MDANSE_API}
#mkdir ${MDANSE_API}/_static
#mkdir ${MDANSE_API}/_templates

sphinx-apidoc -o ${MDANSE_API} -F --separate -d 5 -H MDANSE -A "G. Goret & E. Pellegrini"  -V 1.0 -R 1.0 ../MDANSE ../MDANSE/Externals

cp conf_html.py ${MDANSE_API}/conf.py

cp layout.html ${MDANSE_API}/_templates/

cp mdanse_logo.png ${MDANSE_API}/_static/

sphinx-build -b html ${MDANSE_API} ${MDANSE_API}


