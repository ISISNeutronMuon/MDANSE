docker run --rm -iv${PWD}:/artifacts/ deploy_mdanse_$1 << COMMANDS
chmod 755 /mdanse/*.deb
cp -a /mdanse/*.deb /artifacts/.
COMMANDS
