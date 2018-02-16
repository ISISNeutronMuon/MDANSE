#!/bin/bash

export ARCH=$1
export DISTRO=$2

#############################
# CONFIGURATION
#############################

## Add some colors
BLEU="\\033[1;34m"

# build ILL version of ScientificPython
cd /tmp
rm -rf scientific-python
git clone https://code.ill.fr/scientific-software/scientific-python.git
git checkout master
cd scientific-python
python setup.py build

declare -x PYTHONPATH=/tmp/scientific-python/build/lib.linux-x86_64-2.7/:${PYTHONPATH}

# build ILL version of ScientificPython
cd /tmp
rm -rf mmtk
git clone https://code.ill.fr/scientific-software/mmtk.git
git checkout master
cd mmtk
python setup.py build


declare -x PYTHONPATH=/tmp/mmtk/build/lib.linux-x86_64-2.7/:${PYTHONPATH}

cd
cd $CI_PROJECT_DIR

# Update the __pkginfo__ file with the current commit 
COMMIT_ID=$(git rev-parse --short HEAD)
sed -i "s/.*__commit__.*/__commit__ = \"${COMMIT_ID}\"/" MDANSE/__pkginfo__.py

# Get revision number from git (without trailing newline)
echo -e "$BLEU""Commit id = ${COMMIT_ID}<--" "$NORMAL"

# Now build last version
echo "$BLEU""Building MDANSE" "$NORMAL"
python setup.py build

status=$?
if [ $status -ne 0 ]; then
	echo "Failed to build MDANSE"
	exit $status
fi

exit 0