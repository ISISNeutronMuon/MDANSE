#!/bin/bash

export ARCH=$1
export DISTRO=$2

#############################
# CONFIGURATION
#############################

## Add some colors
BLEU="\\033[1;34m"

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