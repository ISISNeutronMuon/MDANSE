#!/bin/sh


sphinx-apidoc -o  ../Documentation -F --separate -d 5 -H nMoldyn -A "B. Aoun & G. Goret & E. Pellegrini, G.R. Kneller"  -V 4.0 -R 4.0 ../nMOLDYN/

cp doc_utils/conf_html.py ../Documentation/conf.py


cp doc_utils/nMoldyn_logo.png ../Documentation/_static/

sphinx-build -b html ../Documentation ../Documentation/_build/html/






