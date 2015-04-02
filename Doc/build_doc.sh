#!/bin/sh

rm -rf Documentation

mkdir Documentation
mkdir Documentation/_static

sphinx-apidoc -o  ./Documentation -F --separate -d 5 -H MDANSE -A "B. Aoun & G. Goret & E. Pellegrini"  -V 1.0 -R 1.0 ../MDANSE/

cp conf_html.py ./Documentation/conf.py

cp mdanse_logo.png ./Documentation/_static/

sphinx-build -b html ./Documentation ./Documentation/_build/html/






