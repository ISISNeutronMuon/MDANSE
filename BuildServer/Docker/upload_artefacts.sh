docker run --rm -iv${PWD}:/artifacts/ deploy_mdanse_xenial << COMMANDS
chown ci:ci /mdanse/BuildServer/*.deb
chmod 755 /mdanse/BuildServer/*.deb
cp -a /mdanse/BuildServer/*.deb /artifacts/.
COMMANDS

