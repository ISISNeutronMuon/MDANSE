#!/bin/bash

VERSION=$1

# Update version number to python source code (will appear in "About..." dialog)
# see http://stackoverflow.com/questions/7648328/getting-sed-error
sed -i "s/.*__version__.*/__version__ = \"${VERSION}\"/" Src/__pkginfo__.py

# Update the date of the version
sed -i "s/.*__date__.*/__date__ = \"`date +"%d-%m-%Y"`\"/" Src/__pkginfo__.py

