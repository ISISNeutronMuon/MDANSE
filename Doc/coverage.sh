#!/bin/sh

cd ../Tests/
coverage run --source=../nMOLDYN/ ../Tests/AllTests.py
coverage html --omit=../nMOLDYN/Externals/*,../nMOLDYN/GUI/*,../nMOLDYN/Framework/Plugins/*,../nMOLDYN/Framework/ConfiguratorWidgets/*