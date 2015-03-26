#!/bin/sh

rm -rf ../Documentation

sphinx-apidoc -o  ../Documentation -F --separate -d 5 -H nMoldyn -A "B. Aoun & G. Goret & E. Pellegrini, G.R. Kneller"  -V 4.0 -R 4.0 ../nMOLDYN/
cp doc_utils/conf_help.py ../Documentation/conf.py
cp doc_utils/layout.html ../Documentation/_templates/
sphinx-build -b htmlhelp ../Documentation ../nMOLDYN/GUI/Help/
