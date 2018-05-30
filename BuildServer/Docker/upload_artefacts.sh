docker run --rm -iv${PWD}:/artifacts/ deploy_mdanse_xenial << COMMANDS
chmod 755 /mdanse/BuildServer/*.deb
cp -a /mdanse/BuildServer/*.deb /artifacts/.
COMMANDS

