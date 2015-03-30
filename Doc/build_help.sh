#!/bin/sh

rm -rf ../Documentation

setenv PYTHONPATH=/home/pellegrini/workspace/MDANSE

sphinx-apidoc -o  . -F --separate -d 5 -H mdanse -A "G. Goret, B. Aoun  & E. Pellegrini"  -V 4.0 -R 4.0 ../MDANSE
cp conf_help.py conf.py

cp layout.html _templates/
cp mdanse_logo.png _static/
sphinx-build -b htmlhelp ./ ./Help/
