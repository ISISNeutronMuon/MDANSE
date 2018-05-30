docker run --rm -iv${PWD}:/artifacts/ deploy_mdanse_xenial << COMMANDS
chown $(id -u):$(id -g) /mdanse/BuildServer/*.deb
chmod 755 /mdanse/BuildServer/*.deb
cp -a /mdanse/BuildServer/*.deb /artifacts/.
COMMANDS

