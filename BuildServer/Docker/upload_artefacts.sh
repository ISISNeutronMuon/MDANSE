docker run --rm -iv${PWD}:/artifacts/ deploy_mdanse_$1 << COMMANDS
chmod 755 /mdanse/BuildServer/*.deb
cp -a /mdanse/BuildServer/*.deb /artifacts/.
COMMANDS
