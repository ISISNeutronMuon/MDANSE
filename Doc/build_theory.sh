#!/bin/sh

latex theory_help.tex
makeglossaries theory_help
latex theory_help.tex
latex theory_help.tex
dvipdf theory_help.dvi

mv theory_help.pdf ../MDANSE/Doc

rm theory_help.acn
rm theory_help.acr
rm theory_help.alg
rm theory_help.aux
rm theory_help.dvi
rm theory_help.glo
rm theory_help.ist
rm theory_help.out
rm theory_help.log
rm theory_help.toc

