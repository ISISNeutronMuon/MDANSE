#!/bin/sh

rm -rf ./Documentation

mkdir ./Documentation
mkdir ./Documentation/_static
mkdir ./Documentation/_templates

sphinx-apidoc -o  ./Documentation -F --separate -d 5 -H MDANSE -A "G. Goret, B. Aoun  & E. Pellegrini"  -V 1.0 -R 1.0 ../MDANSE

cp conf_help.py ./Documentation/conf.py

cp layout.html ./Documentation/_templates/

cp mdanse_logo.png ./Documentation/_static/

sphinx-build -b htmlhelp ./Documentation ./Documentation/Help/
